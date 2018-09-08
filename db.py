import sqlite3

db = sqlite3.connect('C:/Users/uidn4936/PycharmProjects/urlaubskalender/mydb')
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, category TEXT)
''')
db.commit()
