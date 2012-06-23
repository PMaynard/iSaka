import sqlite3

con = sqlite3.connect('superstore.db')
c = con.cursor()

c.execute('''CREATE TABLE User (User_ID INTEGER PRIMARY KEY AUTOINCREMENT, Name text)''')
c.execute('''CREATE TABLE Owes (Owes_ID INTEGER PRIMARY KEY AUTOINCREMENT, User_ID INTEGER, Owes_User INTEGER, Amount real)''')
c.execute('''INSERT INTO USER (Name) VALUES('Osaka')''')

con.commit()
c.close()
