import sqlite3
import sys

con = sqlite3.connect('superstore.db')
c = con.cursor()

def find(name):
    c.execute('SELECT Name, (SELECT Name FROM User WHERE User_ID = Owes_User), Amount FROM Owes JOIN User ON User.User_ID = Owes.User_ID WHERE Name = ?', (name, ))
    print c.fetchall()   
        
    
find(sys.argv[1])
