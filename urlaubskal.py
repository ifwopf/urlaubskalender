from flask import Flask, render_template, request, json
from src.models import sess, User, Categeory, Day, datetime
from sqlalchemy import and_, or_

app = Flask(__name__)

def create_year(j, berufsschule, feiertage):
    monate = ["Januar", "Februar","Maerz","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
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
    einunddreisig = [januar,maerz,mai,juli,august,oktober,dezember]
    dreisig = [april,juni,september,november]
    achtundzwanzig = [februar]
    jahr = [januar, februar, maerz, april, mai, juni, juli, august, september, oktober, november, dezember]
    wochentag = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
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

    for ele in achtundzwanzig:
        i = 0
        while i < 28:
            i = i + 1
            ele[i] = []

    for monat in jahr:
        for tag in monat:
            try:
                monat[tag].append(wochentag[j])
                monat[tag].append(0)
                if j == 6:
                    monat[tag].append("Sonntag")
                    j = 0
                elif j == 5:
                    monat[tag].append("Samstag")
                    j += 1
                else:
                    monat[tag].append("Betrieb")
                    j += 1
                monat[tag].append("")
            except:
                pass
    print(jahr)
    for feiertag in feiertage:
        if jahr[feiertag[1] - 1][feiertag[2]][0] == "Samstag" or jahr[feiertag[1] - 1][feiertag[2]][0] == "Sonntag":
            pass
        else:
            jahr[feiertag[1] - 1][feiertag[2]][1] = feiertag[3]
        jahr[feiertag[1] - 1][feiertag[2]][2] = "Feiertag"
        jahr[feiertag[1] - 1][feiertag[2]][3] = feiertag[0]

    for block in berufsschule:
        if block[1] == block[3]:
            start = block[0]
            while start < (block[2] + 1):
                if not jahr[block[1] - 1][start][2] == "Sonntag" and not jahr[block[1] - 1][start][2] == "Samstag" \
                        and not jahr[block[1] - 1][start][2] == "Feiertag":
                    jahr[block[1] - 1][start][2] = "Berufsschule"
                start += 1
        else:
            start = block[0]
            while start < len(jahr[(block[1] - 1)]) + 1:
                if not jahr[block[1] - 1][start][2] == "Sonntag" and not jahr[block[1] - 1][start][2] == "Samstag" \
                        and not jahr[block[1] - 1][start][2] == "Feiertag":
                    jahr[block[1] - 1][start][2] = "Berufsschule"
                start += 1
            start = 1
            while start < (block[2] + 1):
                if not jahr[block[3] - 1][start][2] == "Sonntag" and not jahr[block[3] - 1][start][2] == "Samstag" \
                        and not jahr[block[3] - 1][start][2] == "Feiertag":
                    jahr[block[3] - 1][start][2] = "Berufsschule"
                start += 1
    return jahr, monate

#Jahresspezifische_Angaben
feiertage_hessen_2018 = [["Neujahr",1,1,0],["Karfreitag",3,30,0],["Ostersonntag",4,1,0],["Ostermontag",4,2,0],
                    ["Tag der Arbeit",5,1,0],["Christi Himmelfahrt",5,10,0],["Pfingstsonntag",5,20,0],["Pfingstmontag",5,21,0],
                    ["Fronleichnam",5,31,0],["Tag der Deutschen Einheit",10,3,0], ["Heiligabend", 12,24,0.5],
                    ["Weihnachten", 12, 25,0],["Weihnachten", 12, 26,0],["Silvester",12,31,0,.5]]
berufsschule_2018 = [[26,2,16,3],[7,5,25,5],[10,9,28,9],[26,11,21,12]]
j_2018 = 0

feiertage_hessen_2019 = [["Neujahr",1,1,0],["Karfreitag",4,19,0],["Ostersonntag",4,21,0],["Ostermontag",4,22,0],
                    ["Tag der Arbeit",5,1,0],["Christi Himmelfahrt",5,30,0],["Pfingstsonntag",6,9,0],["Pfingstmontag",6,10,0],
                    ["Fronleichnam",6,20,0],["Tag der Deutschen Einheit",10,3,0], ["Heiligabend", 12,24,0.5],
                    ["Weihnachten", 12, 25,0],["Weihnachten", 12, 26,0],["Silvester",12,31,0.5]]
berufsschule_2019 = [[4,3,22,3],[20,5,7,6]]
j_2019 = 1





@app.route('/')
def kalender():
    list = entries_to_list(2018)
    jahr, monate = create_year(j_2018, berufsschule_2018, feiertage_hessen_2018)
    return render_template('kalender.html', jahr=jahr, monate=monate, jahreszahl=2018, data=json.dumps(list))


@app.route('/2019')
def kalender_2019():
    list = entries_to_list(2019)
    jahr, monate = create_year(j_2019, berufsschule_2019, feiertage_hessen_2019)
    return render_template('kalender.html', jahr=jahr, monate=monate,jahreszahl=2019, data=json.dumps(list))


@app.route('/postEntry', methods=['Post', 'GET'])
def postentry():
    id = request.json['date']
    tmp = id.split("d")[1].split("m")
    year = request.json['year']
    categ = request.json['category']
    cat = sess.query(Categeory).filter_by(name=categ).first()
    if cat is None:
        cat = Categeory(name=categ, user_id=0, timestamp=datetime.utcnow())
        sess.add(cat)
        sess.commit()
    entry = sess.query(Day).filter(and_(Day.day==int(tmp[0]),Day.month==int(tmp[1]), Day.year==int(year))).first()
    if entry is None:
        entry = Day(user=0, day=int(tmp[0]), month=int(tmp[1]), year=year, category=cat.id)
        sess.add(entry)
    else:
        entry.category = cat.id
    sess.commit()
    return 'hey'



def entries_to_list(year):
    rows = sess.query(Day).filter(and_(Day.user==0, Day.year==year)).all()
    list = []
    for entry in rows:
        cat = sess.query(Categeory).filter_by(id=entry.category).first()
        list.append({"id": "d" + str(entry.day) + "m" + str(entry.month), "category": cat.name})
    return list



if __name__ == '__main__':
    app.run()
