import sqlite3

db = sqlite3.connect('/home/ilija/projects/urlaubskalender/mydb')
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, category TEXT)
''')
db.commit()
