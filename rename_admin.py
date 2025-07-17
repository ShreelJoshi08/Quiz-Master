import sqlite3

conn = sqlite3.connect('parking.db')
cursor = conn.cursor()
cursor.execute("ALTER TABLE admin RENAME TO admin_old;")
conn.commit()
conn.close()