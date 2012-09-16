# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# MySQL 
import MySQLdb as mdb

# Regular Experssion
import re

# system imports
import time, sys

class Todo:

	def add(self, msg):
		self.con = None
		try:
			self.con = mdb.connect('localhost', 'root', 'superawesomepass', 'testdb');
			cur = self.con.cursor()
			cur.execute("SELECT VERSION()")
			log.msg("%s" % mdb.escape_string(msg))
			data = cur.fetchone()
			log.msg("Database version : %s " % data)
		except mdb.Error, e:
			log.msg("Error %d: %s" % (e.args[0],e.args[1]))
		finally:      
			if self.con:    
				self.con.close()

class MessageLogger:
	"""
	An independent logger class (because separation of application
	and protocol logic is a good thing).
	"""
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

	nickname = "Motoko"

	def connectionMade(self):
		irc.IRCClient.connectionMade(self)
		self.logger = MessageLogger(open(self.factory.filename, "a"))
		self.logger.log("[connected at %s]" % time.asctime(time.localtime(time.time())))

	def connectionLost(self, reason):
		irc.IRCClient.connectionLost(self, reason)
		self.logger.log("[disconnected at %s]" % time.asctime(time.localtime(time.time())))
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

		# Only allow specific users access
		if user == "Osaka": # Replace this with an array from a config file.
			t = Todo()
			p = re.compile('^!todo ')
			if p.match(msg):
				t.add(msg[6:])

		# Check to see if they're sending me a private message
		if channel == self.nickname:
			msg = "I am a living, thinking entity that was created in the sea of information."
			self.msg(user, msg)
			return

		# Otherwise check to see if it is a message directed at me
		if msg.startswith(self.nickname + ":"):
			msg = "%s: As a sentient lifeform, I hereby demand political asylum." % user
			self.msg(channel, msg)
 
class LogBotFactory(protocol.ClientFactory):
	"""A factory for LogBots.

	A new protocol instance will be created each time we connect to the server.
	"""

	def __init__(self, channel, filename):
		self.channel = channel
		self.filename = filename

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
	# initialize twisted logging 
	log.startLogging(sys.stdout)

	# create factory protocol and application
	f = LogBotFactory(sys.argv[1], sys.argv[2])

	# connect factory to this host and port
	reactor.connectTCP("localhost", 6667, f)

	# run bot
	reactor.run()