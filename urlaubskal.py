from flask import Flask, render_template, request, json, jsonify
from functools import wraps
from src.models import sess, User, Category, Day, Userday, Calender, \
    CalenderUser, datetime, Base, SyncCatUser, \
    metadata, engine
from sqlalchemy import and_, or_
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta
from src.specialDayCatalogue import feiertage

app = Flask(__name__)
cors = CORS(app, resources={r"/urlaub/api/*": {"origins": "*"}})


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get('Authorization', '').split()
        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }
        if len(auth_headers) != 2:
            return jsonify(invalid_msg), 401

        try:
            token = auth_headers[1]
            data = jwt.decode(token, 'secretKeyShouldBeinConfigups')
            user = sess.query(User).filter_by(email=data['sub']).first()
            if not user:
                raise RuntimeError('User not found')
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(expired_msg), 401  # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401

    return _verify


@app.route('/urlaub/api/v1.0/register/', methods=['POST'])
def register():
    data = request.get_json()
    user = User(**data)
    print("da1")
    print(data["email"])
    if checkIfMailExists(data["email"]):
        print("hier")
        return "999"
    else:
        print("da")
        sess.add(user)
        sess.commit()
        return jsonify(user.to_dict()), 201


@app.route('/urlaub/api/v1.0/addUnreg/', methods=['POST'])
@token_required
def addUnreg(user):
    try:
        data = request.json
        if data["years"] is not None and data["cats"] is not None:
            addCalendarUnreg(data["years"], data["cats"], user)
        return "ok"
    except:
        return "ups"


def addCalendarUnreg(years, cats, user):
    newCal = Calender(name="Kalender", shared=False)
    sess.add(newCal)
    sess.commit()
    calUser = CalenderUser(cID=newCal.id, uID= user.id, admin=True, accepted=True)
    sess.add(calUser)
    sess.commit()
    catOldIDDict = {}
    for cat in cats:
        if cat["id"] != 0:
            newCat = Category(name=cat["name"], color=cat["style"]["background-color"], cal_id=newCal.id)
            sess.add(newCat)
            sess.commit()
            catOldIDDict[cat["id"]] = newCat.id
    for year in years:
        for month in year:
            for day in month:
                if day["note"] is not None or day["cat_id"] != 0:
                    dbDay = sess.query(Day).filter(Day.day==day["day"], Day.month==day["month"], Day.year==day["year"]).first()
                    newUserday = Userday(dayID=dbDay.id, value=1, catID = catOldIDDict[day["cat_id"]], calID=newCal.id, name=day["note"], userID=user.id)
                    sess.add(newUserday)
    sess.commit()


@app.route('/urlaub/api/v1.0/login/', methods=['POST'])
def login():
    data = request.get_json()
    user = User.authenticate(**data)

    if not user:
        return jsonify({'message': 'Invalid credentials', 'authenticated': False}), 401
    token = jwt.encode({
        'sub': user.email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=1440)},
        'secretKeyShouldBeinConfigups')
    return jsonify({'token': token.decode('UTF-8')})


@app.route('/urlaub/api/v1.0/cal', methods=['GET'])
@token_required
def getCals(user):
    try:
        rows = sess.query(CalenderUser).filter(CalenderUser.uID == user.id).outerjoin(Calender,
                                                                                 Calender.id == CalenderUser.cID).all()
        cals = []
        for cal in rows:
            cals.append({"id": cal.calender.id,
                      "name": cal.calender.name,
                         "shared": cal.calender.shared
                      })
        return jsonify(cals)
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/addCal', methods=['POST', 'GET'])
@token_required
def addCal(user):
    try:
        calName = request.json["calName"]
        newCal = Calender(name=calName, shared=False)
        sess.add(newCal)
        sess.commit()
        newUserCal = CalenderUser(uID=user.id, cID=newCal.id, admin=True, accepted=True)
        sess.add(newUserCal)
        sess.commit()
        return "ok"
    except:
        return "ups"


#check if user is allowed to get cal
@app.route('/urlaub/api/v1.0/days/<calID>/<year>', methods=['GET'])
@token_required
def get_days(user, calID, year):
    try:
        allowed = sess.query(CalenderUser).filter(CalenderUser.uID==user.id, CalenderUser.cID==calID).first()
        if allowed is not None:
            rows = sess.query(Day, Userday).filter(Day.year == int(year))\
                    .outerjoin(Userday, and_(Day.id== Userday.dayID,Userday.calID == calID, Userday.userID==user.id)).all()
            list = orderDays(rows, year, user.id)
            cats = sess.query(Category).filter(Category.cal_id == int(calID))
            categ = {}
            for cat in cats:
                categ[cat.id] = {"id": cat.id,
                                 "name": cat.name,
                                 "style": {"background-color": cat.color}
                                 }
            return jsonify({'days': list, "cats": categ, "user": user.id})
        else:
            return "No rights"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/daysUnreg/<year>', methods=['GET'])
def getDaysUnreg(year):
    try:
        rows = sess.query(Day).filter(Day.year == int(year)).all()
        list = orderDaysUnreg(rows, year)
        categ = {}
        return jsonify({'days': list, "cats": categ, "user": 0})
    except:
        return "ups"

#Nur für eigene Kalender???? berechtigung checken
@app.route('/urlaub/api/v1.0/change_cat', methods=['POST', 'GET'])
@token_required
def change_cat(user):
    try:
        days = request.json['days']
        catID = request.json["cat_id"]
        if catID==0:
            catID = None
        calID = request.json["calID"]
        allowed = sess.query(CalenderUser).filter(CalenderUser.uID == user.id, CalenderUser.cID == calID).first()
        if allowed is not None and allowed.admin:
            newUserdays = changeCat(user, days, catID, calID)
            return newUserdays
        else:
            return "No rights"
    except:
        return "ups"

def changeCat(user, days, catID, calID):
    newUserdays = {}
    changedUserdays = {}
    for day in days:
        exists = sess.query(Userday).filter(Userday.dayID == day['id'], Userday.calID == calID,
                                            Userday.userID == day['userID']).first()
        if day['userdayID'] == -1 and exists is None:
            userday = Userday(dayID=day['id'], calID=calID, catID=catID,
                              userID=day['userID'])
            sess.add(userday)
            sess.commit()
            newUserdays[day['id']] = {"userdayID": userday.id, "userID": userday.userID}
        else:
            userday = sess.query(Userday).filter(Userday.id == day['userdayID']).first()
            if userday.catID in changedUserdays:
                changedUserdays[userday.catID].append(userday)
            else:
                changedUserdays[userday.catID] = [userday]
            userday.catID = catID
            sess.commit()
    cal = sess.query(Calender).filter(Calender.id == calID).first()
    if not cal.shared:
        syncCats(catID, days, user.id, changedUserdays)
    return jsonify(newUserdays)

#sharedUser Admin darf Notes bei anderen User hinzufügen
@app.route('/urlaub/api/v1.0/addNote', methods=['POST', 'GET'])
@token_required
def addNote(currentUser):
    try:
        days = request.json['days']
        note = request.json["note"]
        if note == "":
            note = None
        calID = request.json["calID"]
        newUserdays = {}
        for day in days:
            if currentUser.id == day['userID']: #SharedAdmin?
                exists = sess.query(Userday).filter(Userday.dayID == day['id'], Userday.calID == calID,
                                                    Userday.userID == day['userID']).first()
                if day['userdayID'] == -1 and exists is None:
                    userday = Userday(dayID=day['id'], calID=calID, name=note, userID=day['userID'])
                    sess.add(userday)
                    sess.commit()
                    newUserdays[day['id']] = {"userdayID" : userday.id,  "userID": userday.userID}
                else:
                    userday = sess.query(Userday).filter(Userday.id == day['userdayID']).first()
                    userday.name = note
                    sess.commit()
        return jsonify(newUserdays)
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/add_cat', methods=['POST'])
@token_required
def add_cat(currentUser):
    try:
        cat_name = request.json["cat_name"]
        cat_color = request.json["cat_color"]
        calID = request.json["calID"]
        new_cat = Category(cal_id=calID, name=cat_name, color=cat_color)
        sess.add(new_cat)
        sess.commit()
        days = request.json['clicked']
        newUserdays = {}
        for day in days:
            if day['userdayID'] == -1:
                userday = Userday(dayID=day['id'], calID=calID, catID=new_cat.id,
                                  userID=currentUser.id)
                sess.add(userday)
                sess.commit()
                newUserdays[day['id']] = userday.id
            else:
                userday = sess.query(Userday).filter(Userday.id == day['userdayID']).first()
                userday.catID = new_cat.id
                sess.commit()
        cat = {"id": new_cat.id, "name": new_cat.name, "style": {"background-color": new_cat.color}}
        return jsonify(cat, newUserdays)
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/editCat', methods=['POST'])
@token_required
def editCat(user):
    try:
        cat_name = request.json["catName"]
        cat_color = request.json["catColor"]
        cat_id = request.json["catId"]
        cat = sess.query(Category).filter(Category.id == cat_id).first()
        allowed = sess.query(CalenderUser).filter(CalenderUser.uID == user.id, CalenderUser.cID == cat.cal_id).first()
        if allowed is not None and allowed.admin:
            if cat_name != '':
                cat.name = cat_name
            if cat_color != '':
                cat.color = cat_color
            sess.commit()
        return "ok"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/editCatName', methods=['POST'])
@token_required
def editCatName(user):
    try:
        cat_name = request.json["catName"]
        cat_id = request.json["catId"]
        cat = sess.query(Category).filter(Category.id == cat_id).first()
        allowed = sess.query(CalenderUser).filter(CalenderUser.uID == user.id, CalenderUser.cID == cat.cal_id).first()
        if allowed is not None and allowed.admin:
            if cat_name != '':
                cat.name = cat_name
            sess.commit()
        return "ok"
    except:
        return "ups"

@app.route('/urlaub/api/v1.0/getCalName/<calID>', methods=['GET'])
@token_required
def getCalName(user, calID):
    try:
        cal = sess.query(Calender).filter(Calender.id == calID).first()
        allowed = sess.query(CalenderUser).filter(CalenderUser.uID==user.id, CalenderUser.cID==calID).first()
        if allowed is not None:
            return cal.name
        else:
            return "No rights"
    except:
        return "ups"

@app.route('/urlaub/api/v1.0/editCatColor', methods=['POST'])
@token_required
def editCatColor(user):
    try:
        cat_color = request.json["catColor"]
        cat_id = request.json["catId"]
        cat = sess.query(Category).filter(Category.id == cat_id).first()
        allowed = sess.query(CalenderUser).filter(CalenderUser.uID == user.id, CalenderUser.cID == cat.cal_id).first()
        if cat_color != '' and allowed is not None and allowed.admin:
            cat.color = cat_color
            sess.commit()
        return "ok"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/deleteUser', methods=['POST'])
@token_required
def deleteUser(user):
    try:
        cals = sess.query(CalenderUser).filter(CalenderUser.uID == user.id).all()
        for cal in cals:
            deleteCalendar(user, cal.cID)
        thatUser = sess.query(User).filter(User.id == user.id).first()
        sess.delete(thatUser)
        sess.commit()
        return "rip"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/removeUserFromShared', methods=['POST'])
@token_required
def removeUserFromShared(user):
    try:
        calID = int(request.json["calID"])
        cal = sess.query(CalenderUser).filter(CalenderUser.uID == user.id, CalenderUser.cID == calID).first()
        sess.query(Userday).filter(Userday.userID == user.id, Userday.calID == calID).delete()
        sess.delete(cal)
        sess.commit()
        return "rip"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/deleteCal', methods=['POST'])
@token_required
def deleteCal(user):
    try:
        calID = request.json["calID"]
        deleteCalendar(user, calID)
        return "RIP"
    except:
        return "ups"


def deleteCalendar(user, calID):
    calTodelete = sess.query(Calender).filter(Calender.id == calID).first()
    users = sess.query(CalenderUser).filter(CalenderUser.cID == calID).all()
    berechtigt = False
    for us in users:
        if us.uID == user.id and us.admin:
            berechtigt = True
    if berechtigt:
        sess.query(CalenderUser).filter(CalenderUser.cID == calID).delete()
        sess.query(Userday).filter(Userday.calID == calID).delete()
        catsToDelete = sess.query(Category).filter(Category.cal_id == calID).all()
        for cat in catsToDelete:
            if calTodelete.shared:
                sess.query(SyncCatUser).filter(SyncCatUser.scID == cat.id).delete()
            else:
                sess.query(SyncCatUser).filter(SyncCatUser.ucID == cat.id).delete()
            sess.delete(cat)
            sess.commit()

        sess.delete(calTodelete)
        sess.commit()
    else:
        sess.query(CalenderUser).filter(CalenderUser.cID == calID, CalenderUser.uID == user.id).delete()
        sess.query(Userday).filter(Userday.calID == calID, Userday.userID == user.id).delete()
    return "RIP"


@app.route('/urlaub/api/v1.0/deleteCat', methods=['POST'])
@token_required
def deleteCat(user):
    try:
        catID = request.json["catID"]
        cat = sess.query(Category).filter(Category.id == catID).first()
        allowed = sess.query(CalenderUser).filter(CalenderUser.uID == user.id, CalenderUser.cID == cat.cal_id).first()
        daysChanged = []
        if allowed is not None and allowed.admin:
            days = sess.query(Userday).filter(Userday.catID == catID).all()
            for day in days:
                day.catID = None
                daysChanged.append(day.dayID)
            sess.delete(cat)
            sess.commit()
        return jsonify(daysChanged)
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/createShared', methods=['POST', 'GET'])
@token_required
def createShared(currentUser):
    try:
        data = request.get_json()
        addedUsers = data['addedUsers']
        #add new Shared Calendar
        name = data['named']
        newShared = Calender(name=name, shared=True)
        sess.add(newShared)
        sess.commit()
        # add new Shared Calendar User
        sess.commit()
        for user, admin in addedUsers.items():
            userToAdd = sess.query(User).filter(User.email == user).first()
            newSharedUser = CalenderUser(cID=newShared.id, uID=userToAdd.id, accepted=False, admin=admin)
            sess.add(newSharedUser)
            sess.commit()
        return "done"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/shared/<id>/<year>', methods=['GET'])
@token_required
def getShared(userLoggedIn, id, year):
    try:
        shared = sess.query(Calender).filter(Calender.id == id).first()
        sharedDict = {}
        sharedDict['id'] = shared.id
        sharedDict['name'] = shared.name
        users = sess.query(CalenderUser).filter(CalenderUser.cID == id).all()
        userCals = [[],[],[],[],[],[],[],[],[],[],[],[]]
        userlist = []
        cats = sess.query(Category).filter(Category.cal_id == int(id))
        categ = {}
        for cat in cats:
            categ[cat.id] = {"id": cat.id,
                             "name": cat.name,
                             "style": {"background-color": cat.color}
                             }
        allowed = False
        for i, user in enumerate(users):
            userFound = sess.query(User).filter(User.id == user.uID).first()
            if userFound.id == userLoggedIn.id:
                allowed = True
            userlist.append([userFound.id, userFound.email, i])
            rows = sess.query(Day, Userday).filter(Day.year == int(year)).outerjoin(Userday, and_(Day.id == Userday.dayID,
                                                                                                  Userday.calID == id,
                                                                                             Userday.userID == userFound.id)).all()
            for j, monat in enumerate(orderDays(rows, int(year), userFound.id)):
                userCals[j].append(monat)
        if allowed:
            return jsonify(sharedDict, userlist, userCals, categ, userLoggedIn.id)
        else:
            return "No rights"
    except:
        return "ups"


#check if User in SharedUsers
@app.route('/urlaub/api/v1.0/getCats/<id>/<id2>', methods=['GET'])
@token_required
def getCats(user, id, id2):
    try:
        sharedCats = sess.query(Category).filter(Category.cal_id == int(id2))
        sharedDict = {}
        for cat in sharedCats:
            syncList = []
            syncs = sess.query(SyncCatUser, Category, CalenderUser).filter(SyncCatUser.scID==cat.id)\
                .join(Category, and_(Category.id==SyncCatUser.ucID, Category.cal_id==int(id)))\
                .join(CalenderUser, and_(CalenderUser.cID == SyncCatUser.ucID, CalenderUser.uID == user.id)).all()
            if syncs is not None:
                for sync in syncs:
                    syncList.append(sync[0].ucID)
            sharedDict[cat.id] = {"id": cat.id,
                                  "name": cat.name,
                                  "style": {"background-color": cat.color},
                                  "calID": cat.cal_id,
                                  "syncList": syncList
                             }
        personalCats = sess.query(Category).filter(Category.cal_id == int(id))
        personalDict = {}
        for cat in personalCats:
            personalDict[cat.id] = {"id": cat.id,
                             "name": cat.name,
                             "style": {"background-color": cat.color},
                             "calID": cat.cal_id
                             }
        allowed = sess.query(CalenderUser).filter(CalenderUser.cID==int(id), CalenderUser.uID==user.id).first()
        if allowed is not None:
            return jsonify(personalDict, sharedDict)
        else:
            return "No rights"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/saveCalName', methods=['POST'])
@token_required
def saveCalName(user):
    try:
        name = request.json['name']
        calID = request.json['calID']
        allowed = sess.query(CalenderUser).filter(CalenderUser.cID == int(calID), CalenderUser.uID == user.id).first()
        if allowed is not None and allowed.admin:
            cal = sess.query(Calender).filter(Calender.id == int(calID)).first()
            cal.name = name
            sess.commit()
            return "DONE"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/checkMail/<mail>', methods=['GET'])
def checkMail(mail):
    try:
        return jsonify(checkIfMailExists(mail))
    except:
        return "ups"


def checkIfMailExists(mail):
    result = sess.query(User).filter(User.email == mail).first()
    if result is not None:
        return True
    else:
        return False


@app.route('/urlaub/api/v1.0/getCurrentUser', methods=['GET'])
@token_required
def getCurrentUser(currentUser):
    try:
        return jsonify(currentUser.email)
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/getUserRole/<sCalID>', methods=['GET'])
@token_required
def getUserRole(currentUser, sCalID):
    try:
        role = sess.query(CalenderUser).filter(CalenderUser.uID==currentUser.id, CalenderUser.cID==sCalID).first()
        user = {'id': currentUser.id, 'email': currentUser.email, 'admin': role.admin}
        return jsonify(user)
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/getFeiertage', methods=['GET'])
def getFeiertage():
    try:
        return jsonify(feiertage)
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/addFeiertage', methods=['Post'])
@token_required
def addFeiertage(currentUser):
    try:
        key = request.json['region']
        cat = int(request.json['catID'])
        cal = request.json['calID']
        if cat == 0:
            cat = None
        if cat == -1:
            newCat = Category(name="Feiertage", color="#ffb2b2", cal_id=cal)
            sess.add(newCat)
            sess.commit()
            cat = newCat.id
        for year, holidays in feiertage[key].items():
            for holiday in holidays:
                day = sess.query(Day, Userday).filter(Day.day == holiday['day'], Day.month==holiday['month'], Day.year == year)\
                    .outerjoin(Userday, and_(Day.id==Userday.dayID, Userday.userID==currentUser.id, Userday.calID == cal)).first()
                if day[1] is not None:
                    day[1].name = holiday['name']
                    if cat is not None:
                        day[1].catID = cat
                    sess.commit()
                else:
                    newUserday = Userday(dayID=day[0].id, catID=cat, calID=cal, name=holiday['name'], userID=currentUser.id)
                    sess.add(newUserday)
                    sess.commit()
        return "done"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/getSharedInfo/<calID>', methods=['GET'])
@token_required
def getSharedInfo(user, calID):
    try:
        cal = sess.query(Calender).filter(Calender.id == calID).first()
        name = cal.name
        users = sess.query(CalenderUser, User).filter(CalenderUser.cID == calID).join(User, User.id == CalenderUser.uID).all()
        userlist = {}
        allowed = False
        for sharedUser in users:
            if sharedUser[1].id == user.id:
                allowed = True
            userlist[sharedUser[1].id] = {'email': sharedUser[1].email, 'id': sharedUser[1].id, 'admin': sharedUser[0].admin}
        print(allowed)
        if allowed:
            return jsonify(userlist, name)
        else:
            return "No rights"
    except:
        return "ups"


@app.route('/urlaub/api/v1.0/editShared', methods=['POST'])
@token_required
def editShared(user):
    try:
        calID = request.json['calID']
        newUsers = request.json['users']
        name = request.json['name']
        cal = sess.query(Calender).filter(Calender.id == calID).first()
        allowed = sess.query(CalenderUser).filter(CalenderUser.uID == user.id).first()
        if allowed is not None and allowed.admin:
            if cal.name != name:
                cal.name = name
                sess.commit()
            existingUsers = sess.query(CalenderUser, User).filter(CalenderUser.cID == calID).join(User,
                                                                                          User.id == CalenderUser.uID).all()
            for eUser in existingUsers:
                if str(eUser[1].id) in newUsers:
                    if eUser[0].admin != newUsers[str(eUser[1].id)]['admin']:
                        eUser[0].admin = newUsers[str(eUser[1].id)]['admin']
                    del newUsers[str(eUser[1].id)]
                else:
                    rows = sess.query(Userday).filter(Userday.calID == calID, Userday.userID == eUser[1].id)
                    for row in rows:
                        sess.delete(row)
                    sess.delete(eUser[0])
                sess.commit()
            for email, nUser in newUsers.items():
                addingUser = sess.query(User).filter(User.email==email).first()
                new = CalenderUser(cID=calID, uID=addingUser.id, accepted=True, admin=nUser['admin'])
                sess.add(new)
                sess.commit()
            return 'Done'
        else:
            return "No rights"
    except:
        return "ups"


#sync
@app.route('/urlaub/api/v1.0/setSyncPair', methods=['POST'])
@token_required
def setSyncPair(user):
    #to be added: check if sync for personalCatID in same shared Calendar already exists
    try:
        syncDict = request.json["syncDict"]
        noSync = request.json["nosync"]
        sharedCal = None
        for sharedID, listPersonalIDs in syncDict.items():
            shared = sess.query(Category).filter(sharedID==Category.id).first()
            sharedCal = shared.cal_id
            for personal in listPersonalIDs:
                existing = sess.query(SyncCatUser, Category).filter(SyncCatUser.ucID==personal['id']).join(Category,
                                                                                Category.id == SyncCatUser.scID).all()
                exists = False
                for result in existing:
                    if(result[1] is not None and result[1].cal_id == sharedCal and not exists):
                        result[0].scID = sharedID
                        exists = True
                if not exists:
                    newSyncPair = SyncCatUser(scID= sharedID, ucID=personal['id'])
                    sess.add(newSyncPair)
                sess.commit()
                initSyncDays(personal['id'], sharedID, sharedCal, user.id)
        for cat in noSync:
            existing = sess.query(SyncCatUser, Category).filter(SyncCatUser.ucID == int(cat)).join(Category,
                                                                                                         Category.id == SyncCatUser.scID).all()
            exists = False
            for result in existing:
                removeSyncDays(result[0].ucID, result[0].scID)
                if (result[1] is not None and result[1].cal_id == sharedCal and not exists):
                    sess.delete(result[0])
                    exists = True
                    sess.commit()
        return "It's done."
    except:
        return "ups"

@app.route('/urlaub/api/v1.0/createDB', methods=['POST', "GET"])
def createDB():
    Base.metadata.create_all(engine)
    # new_cat = Category(user_id=0, name="default", value=0, color="fff", id=1)
    # sess.add(new_cat)
    createYear(2020)
    createYear(2021)
    createYear(2022)
    sess.commit()
    return "DONE"



def createYear(year):
    monate = ["Januar", "Februar", "Maerz", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
              "November", "Dezember"]
    januar = {}
    februar = {}
    maerz = {}
    april = {}
    mai = {}
    juni = {}
    juli = {}
    august = {}
    september = {}
    oktober = {}
    november = {}
    dezember = {}
    einunddreisig = [januar, maerz, mai, juli, august, oktober, dezember]
    dreisig = [april, juni, september, november]
    achtundzwanzig = [februar]
    jahr = [januar, februar, maerz, april, mai, juni, juli, august, september, oktober, november, dezember]
    wochentag = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    for ele in einunddreisig:
        i = 0
        while i < 31:
            i = i + 1
            ele[i] = []

    for ele in dreisig:
        i = 0
        while i < 30:
            i = i + 1
            ele[i] = []

    if year == 2020 or year == 2024:
        lenFeb = 29
    else:
        lenFeb = 28
    for ele in achtundzwanzig:
        i = 0
        while i < lenFeb:
            i = i + 1
            ele[i] = []
    startTag = {"2019": 1, "2020": 2, "2021": 4, "2022": 5, "2023": 6, "2024": 0, "2025":2}
    j = startTag[str(year)]
    for monat in jahr:
        for tag in monat:
            try:
                monat[tag].append(wochentag[j])
                if j == 6:
                    j = 0
                else:
                    j += 1
            except:
                pass
    m = 0
    d = 0
    for monat in jahr:
        for tag in monat:
            d += 1
            new_day = Day(day=d, month=m + 1, year=int(year), weekday=jahr[m][d][0])
            sess.add(new_day)
        m += 1
        d = 0
    sess.commit()


def orderDays(userDays, year, userID):
    list = [[], [], [], [], [], [], [], [], [], [], [], []]
    for entry in userDays:
        if entry[1] is not None:
            if entry[1].catID is None:
                catID = 0
            else:
                catID = entry[1].catID
            list[(entry[0].month - 1)].append(
                {"id": entry[0].id,
                 "userdayID": entry[1].id,
                 "day": entry[0].day,
                 "month": entry[0].month,
                 "weekday": entry[0].weekday,
                 "year": year,
                 "cat_id": catID,
                 "userID": entry[1].userID,
                 "note": entry[1].name
                 }
            )
        else:
            list[(entry[0].month - 1)].append(
                {"id": entry[0].id,
                 "userdayID": -1,
                 "day": entry[0].day,
                 "month": entry[0].month,
                 "weekday": entry[0].weekday,
                 "year": year,
                 "cat_id": 0,
                 "userID": userID,
                 "note": None
                 }
            )
    return list

def orderDaysUnreg(days, year):
    list = [[], [], [], [], [], [], [], [], [], [], [], []]
    for entry in days:
        list[(entry.month - 1)].append(
            {"id": entry.id,
             "userdayID": -1,
             "day": entry.day,
             "month": entry.month,
             "weekday": entry.weekday,
             "year": year,
             "cat_id": 0,
             "userID": -1,
             "note": None
             }
        )
    return list


def removeSyncDays(ucID, scID):
    toBeRemovedDays = sess.query(Userday).filter(Userday.catID == ucID).all()
    for removeDay in toBeRemovedDays:
        dayToDelete = sess.query(Userday).filter(and_(Userday.catID == scID, Userday.dayID == removeDay.dayID)).first()
        if dayToDelete is not None:
            dayToDelete.catID = None
            sess.commit()

def initSyncDays(ucID, scID, calID, userID):
    toBeAddedDays = sess.query(Userday).filter(Userday.catID == ucID).all()
    for addDay in toBeAddedDays:
        dayToBeAdded = sess.query(Userday).filter(Userday.dayID == addDay.dayID, Userday.calID== calID, Userday.userID==userID).first()
        if dayToBeAdded is not None:
            dayToBeAdded.catID = scID
            sess.commit()
        else:
            newUserday = Userday(dayID=addDay.dayID, calID=calID, catID=scID,userID=userID)
            sess.add(newUserday)
            sess.commit()


def syncCats(catID, days, userID, removed):
    for keyCatID, userdays in removed.items():
        removeSyncCat(keyCatID, userdays, userID)
    sync = sess.query(SyncCatUser).filter(SyncCatUser.ucID == catID).first()
    if sync is not None:
        cat = sess.query(Category).filter(Category.id == sync.scID).first()
        for day in days:
            tag = sess.query(Day, Userday).filter(Day.year == 2020, Day.id == day['id']).outerjoin(Userday, and_(Day.id == Userday.dayID,
                                                                                            Userday.calID == cat.cal_id,
                                                                                            Userday.userID == userID)).first()
            if tag[1] is None:
                userday = Userday(dayID=day['id'], calID=cat.cal_id, catID=sync.scID,
                                  userID=day['userID'])
                sess.add(userday)
                sess.commit()
            else:
                tag[1].catID = sync.scID
                sess.commit()

def removeSyncCat(catID, userdays, userID):
    sync = sess.query(SyncCatUser).filter(SyncCatUser.ucID == catID).first()
    if sync is not None:
        cat = sess.query(Category).filter(Category.id == sync.scID).first()
        for day in userdays:
            tag = sess.query(Day, Userday).filter(Day.year == 2020, Day.id == day.dayID).outerjoin(Userday, and_(Day.id == Userday.dayID,
                                                                                            Userday.calID == cat.cal_id,
                                                                                            Userday.userID == userID)).first()
            tag[1].catID = None
            sess.commit()

if __name__ == '__main__':
    app.run()
