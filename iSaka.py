# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# SQLlite
import sqlite3

# system imports
import time, sys

class Monies:
    """
    Handles all the money stuff.
    """
    def __init__(self, database, logfile):
		self.conn = sqlite3.connect(database)
		self.c = self.conn.cursor()
		self.logger = MessageLogger(logfile)

    """
    Makes sure that there is a user in the database,
    if not it will add a new user.
    """
    def ParseUser(self, users):
        for user in users:
            self.c.execute('SELECT Name FROM User WHERE Name = ?', (user,))
            if not self.c.fetchone():
                self.c.execute('INSERT INTO User (Name) VALUES(?)', (user,))
                self.logger.log("Added new user '%s'." % user)
                self.conn.commit()
                        
    def calculate(self, source, target, amount): 
        self.ParseUser([source, target])
        """ Now that we know there is a user lets give them all my money. """
        res = self.isRecord(source, target)
        if res:             
            self.c.execute("SELECT Amount FROM Owes WHERE User_ID = ? AND Owes_User = ?", (res[0], res[1]))
            amount = self.c.fetchone()[0] + res[2]
            self.c.execute("UPDATE Owes SET Amount = ? WHERE User_ID = ? AND Owes_User = ?", (amount, res[0], res[1]))
            self.conn.commit()
            print ("Amount: %s\nRes: %s" % (amount, res[2]))
            amount = 0
    
    # Please don't judge me on this...
    def isRecord(self, source, target):
        self.c.execute('SELECT User_ID, Owes_User, Amount FROM Owes WHERE User_ID IN ((SELECT User_ID FROM User WHERE Name = ?),(SELECT User_ID FROM User WHERE name = ?)) AND Owes_User IN ((SELECT User_ID FROM User WHERE Name = ?),(SELECT User_ID FROM User WHERE name = ?))',(source, target, source, target))
        
        return self.c.fetchone()
    
class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MessageLogger, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self, file):
        self.file = file

    def log(self, message):
       	"""Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class LogBot(irc.IRCClient):
    """A logging IRC bot."""

    nickname = "iSaka"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))
        self.money = Monies(self.factory.database, open(self.factory.filename, "a"))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
        self.logger.close()


    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
    

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "I see you..."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname):
            msg = "%s: I'm a bot ding ding." % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))
	
        if msg.startswith("!monies"):
			target = msg.split(' ')[1]
			amount = msg.split(' ')[2]
			self.money.calculate(user, target, amount)
			self.msg(channel, "%s: Thank you" % user)

class LogBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, channel, filename, database):
        self.channel = channel
        self.filename = filename
        self.database = database

    def buildProtocol(self, addr):
        p = LogBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)
	

    # create factory protocol and application
    f = LogBotFactory(sys.argv[1], sys.argv[2], sys.argv[3])

    # connect factory to this host and port
    reactor.connectTCP("127.0.0.1", 6667, f)

    # run bot
    reactor.run()
