from flask import Flask, render_template, request, json
import sqlite3

app = Flask(__name__)
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
feiertage_hessen = [["Neujahr",1,1,0],["Karfreitag",3,30,0],["Ostersonntag",4,1,0],["Ostermontag",4,2,0],
                    ["Tag der Arbeit",5,1,0],["Christi Himmelfahrt",5,10,0],["Pfingstsonntag",5,20,0],["Pfingstmontag",5,21,0],
                    ["Fronleichnam",5,31,0],["Tag der Deutschen Einheit",10,3,0], ["Heiligabend", 12,24,0.5],
                    ["Weihnachten", 12, 25,0],["Weihnachten", 12, 26,0],["Silvester",12,31,0,.5]]
berufschule = [[26,2,16,3],[7,5,25,5],[10,9,28,9],[26,11,21,12]]


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


j=0
for monat in jahr:
    for tag in monat:
        #print(j)
        try:
            monat[tag].append(wochentag[j])
            monat[tag].append(0)
            if j==6:
                monat[tag].append("Sonntag")
                j = 0
            elif j==5:
                monat[tag].append("Samstag")
                j += 1
            else:
                monat[tag].append("Betrieb")
                j += 1
            monat[tag].append("")
        except:
            pass

for feiertag in feiertage_hessen:
    if jahr[feiertag[1]-1][feiertag[2]][0] == "Samstag" or jahr[feiertag[1]-1][feiertag[2]][0] == "Sonntag":
        pass
    else:
        jahr[feiertag[1] - 1][feiertag[2]][1] = feiertag[3]
    jahr[feiertag[1] - 1][feiertag[2]][2] = "Feiertag"
    jahr[feiertag[1] - 1][feiertag[2]][3] = feiertag [0]

for block in berufschule:
    if block[1] == block [3]:
        start = block[0]
        while start < (block[2] + 1):
            if not jahr[block[1]-1][start][2] == "Sonntag" and not jahr[block[1]-1][start][2] == "Samstag" \
                and not jahr[block[1]-1][start][2] ==  "Feiertag":
                jahr[block[1]-1][start][2] = "Berufsschule"
            start += 1
    else:
        start = block[0]
        while start < len(jahr[(block[1]-1)])+1:
            if not jahr[block[1] - 1][start][2] == "Sonntag" and not jahr[block[1] - 1][start][2] == "Samstag" \
                    and not jahr[block[1] - 1][start][2] == "Feiertag":
                jahr[block[1] - 1][start][2] = "Berufsschule"
            start += 1
        start = 1
        while start < (block[2] + 1):
            if not jahr[block[3]-1][start][2] == "Sonntag" and not jahr[block[3]-1][start][2] == "Samstag" \
                and not jahr[block[3]-1][start][2] ==  "Feiertag":
                jahr[block[3]-1][start][2] = "Berufsschule"
            start += 1

@app.route('/')
def kalender():
    list = entries_to_list()
    return render_template('kalender.html', jahr=jahr, monate=monate, data=json.dumps(list))

@app.route('/postEntry', methods=['Post', 'GET'])
def postentry():
    id = request.json['date']
    category = request.json['category']
    update_entries(id, category)
    return 'hey'


def update_entries(date, cat, close=db.close()):
    db = sqlite3.connect('/home/ilija/projects/urlaubskalender/mydb')
    cursor = db.cursor()
    cursor.execute('''INSERT or REPLACE INTO users(id, category) VALUES(?,?)''', (date,cat))
    db.commit()
    close

def entries_to_list():
    db = sqlite3.connect('/home/ilija/projects/urlaubskalender/mydb')
    cursor = db.cursor()
    cursor.execute('''SELECT * FROM  users''')
    rows = cursor.fetchall()
    db.close()
    list = []
    for entry in rows:
        list.append({"id":entry[0],"category": entry[1]})
    return list


if __name__ == '__main__':
    app.run()
