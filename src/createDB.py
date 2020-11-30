from src.models import sess, User, Category, Day, Userday, Calender, \
    CalenderUser, datetime, Base, SyncCatUser, \
    metadata, engine


def deleteAllTableRows():
    sess.query(SyncCatUser).delete()
    sess.query(CalenderUser).delete()
    sess.query(Userday).delete()
    sess.query(Category).delete()
    sess.query(Calender).delete()
    sess.query(Day).delete()
    sess.query(User).delete()
    sess.commit()

def createDB():
    Base.metadata.create_all(engine)
    # new_cat = Category(user_id=0, name="default", value=0, color="fff", id=1)
    # sess.add(new_cat)
    createYear(2020)
    createYear(2021)
    createYear(2022)
    sess.commit()
    print("DOne")
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

createDB()
#deleteAllTableRows()