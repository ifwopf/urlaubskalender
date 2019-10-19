from flask import Flask, render_template, request, json, jsonify
from functools import wraps
from src.models import sess, User, Categeory, Day, datetime, Base, metadata, engine
from sqlalchemy import and_, or_
from flask_cors import CORS
#import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
cors = CORS(app, resources={r"/urlaub/api/*": {"origins": "*"}})

"""
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
        print(auth_headers)
        if len(auth_headers) != 2:
            print('hereee')
            return jsonify(invalid_msg), 401

        try:
            token = auth_headers[1]
            data = jwt.decode(token, 'secretKeyShouldBeinConfigups')
            user = sess.query(User).filter_by(email=data['sub']).first()
            if not user:
                raise RuntimeError('User not found')
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            print('here')
            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print('here2')
            print(e)
            return jsonify(invalid_msg), 401

    return _verify

@app.route('/urlaub/api/v1.0/register/', methods=('POST',))
def register():
    data = request.get_json()
    user = User(**data)
    sess.add(user)
    sess.commit()
    return jsonify(user.to_dict()), 201

@app.route('/urlaub/api/v1.0/login/', methods=('POST',))
def login():
    data = request.get_json()
    user = User.authenticate(**data)

    if not user:
        return jsonify({ 'message': 'Invalid credentials', 'authenticated': False }), 401
    token = jwt.encode({
        'sub': user.email,
        'iat':datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=1440)},
        'secretKeyShouldBeinConfigups')
    return jsonify({ 'token': token.decode('UTF-8') })
"""

@app.route('/urlaub/api/v1.0/days/<year>', methods=['GET'])
#@token_required verify,
def get_days(year):
    print('year' + year)
    rows = sess.query(Day, Categeory).filter(and_(Day.user == 0, Day.year == int(year))) \
        .filter(Day.category == Categeory.id).all()
    if len(rows) == 0:
        createYear(year)
        rows = sess.query(Day, Categeory).filter(and_(Day.user == 0, Day.year == int(year))) \
            .filter(Day.category == Categeory.id).all()
    list = [[], [], [], [], [], [], [], [], [], [], [], []]
    for entry in rows:
        list[(entry[0].month - 1)].append(
            {"day": entry[0].day,
             "month": entry[0].month,
             "weekday": entry[0].weekday,
             "year": year,
             "id": entry[0].id,
             "name": entry[0].name,
             "cat_id": entry[1].id
             }
        )
    cats = sess.query(Categeory).filter(Categeory.user_id == 0)
    categ = {}
    count = 0
    for cat in cats:
        categ[cat.id] = {"id": cat.id,
                         "name": cat.name,
                         "value": cat.value,
                         "style": {"background-color": cat.color}
                         }
        count += 1
    return jsonify({'days': list, "cats": categ})


@app.route('/urlaub/api/v1.0/change_cat', methods=['POST'])
#@token_required verify
def change_cat():
    days = request.json['days']
    cat_id = request.json["cat_id"]
    for day in days:
        id = day['id']
        day = sess.query(Day).filter(Day.id == id).first()
        day.category = cat_id
        sess.commit()
    return str(cat_id)


@app.route('/urlaub/api/v1.0/add_cat', methods=['POST'])
def add_cat():
    cat_name = request.json["cat_name"]
    cat_color = request.json["cat_color"]
    new_cat = Categeory(user_id=0, name=cat_name, value=0, color=cat_color)
    sess.add(new_cat)
    sess.commit()
    clicked = request.json['clicked']
    for click in clicked:
        day = sess.query(Day).filter(Day.id == click["id"]).first()
        day.category = new_cat.id
        sess.commit()
    cat = {"id": new_cat.id, "name": new_cat.name, "value": new_cat.value, "style": {"background-color": new_cat.color}}
    return jsonify(cat)


@app.route('/urlaub/api/v1.0/editCat', methods=['POST'])
def editCat():
    cat_name = request.json["catName"]
    cat_color = request.json["catColor"]
    cat_id = request.json["catId"]
    cat = sess.query(Categeory).filter(Categeory.id == cat_id).first()
    if cat_name != '':
        cat.name = cat_name
    if cat_color != '':
        cat.color = cat_color
    sess.commit()
    return "ok"

@app.route('/urlaub/api/v1.0/editCatName', methods=['POST'])
def editCatName():
    cat_name = request.json["catName"]
    cat_id = request.json["catId"]
    cat = sess.query(Categeory).filter(Categeory.id == cat_id).first()
    if cat_name != '':
        cat.name = cat_name
    sess.commit()
    return "ok"

@app.route('/urlaub/api/v1.0/editCatColor', methods=['POST'])
def editCatColor():
    cat_color = request.json["catColor"]
    cat_id = request.json["catId"]
    cat = sess.query(Categeory).filter(Categeory.id == cat_id).first()
    if cat_color != '':
        cat.color = cat_color
    sess.commit()
    return "ok"

@app.route('/urlaub/api/v1.0/deleteCat', methods=['POST'])
def deleteCat():
    catID = request.json["catID"]
    if catID != 1:
        days = sess.query(Day).filter(Day.category == catID).all()
        for day in days:
            day.category = 1
        sess.commit()
        sess.query(Categeory).filter(Categeory.id == catID).delete()
        sess.commit()
        return "It's done. RIP"
    else:
        return "Default Cat! Cannot Delete"

@app.route('/urlaub/api/v1.0/createDB', methods=['POST', "GET"])
def createDB():
    Base.metadata.create_all(engine)
    new_cat = Categeory(user_id=0, name="default", value=0, color="fff", id=1)
    sess.add(new_cat)
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

    if year == "2020":
        lenFeb = 29
    else:
        lenFeb = 28
    for ele in achtundzwanzig:
        i = 0
        while i < lenFeb:
            i = i + 1
            ele[i] = []
    startTag = {"2019": 1, "2020":2, "2021":4}
    j = startTag[str(year)]
    for monat in jahr:
        for tag in monat:
            try:
                monat[tag].append(wochentag[j])
                if j==6:
                    j = 0
                else:
                    j += 1
            except:
                pass
    print(jahr)

    m = 0
    d = 0
    for monat in jahr:
        for tag in monat:
            d += 1
            new_day = Day(day=d, month=m + 1, year=int(year), category=1, weekday=jahr[m][d][0], user=0)
            sess.add(new_day)
        m += 1
        d = 0
    sess.commit()



if __name__ == '__main__':
    app.run()
