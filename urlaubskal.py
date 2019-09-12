from flask import Flask, render_template, request, json, jsonify
from src.models import sess, User, Categeory, Day, datetime
from sqlalchemy import and_, or_
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/urlaub/api/*": {"origins": "*"}})


@app.route('/urlaub/api/v1.0/days/<year>', methods=['GET'])
def get_days(year):
    rows = sess.query(Day, Categeory).filter(and_(Day.user == 0, Day.year == year)) \
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


if __name__ == '__main__':
    app.run()
