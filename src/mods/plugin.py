from twisted.python import log
from collections import namedtuple

User = namedtuple("User", "name host")

class Plugin(object):
    __NAME__ = None
    __VERSION__ = None

    def __init__(self, manager):
        self.manager = manager
        self.targeted_commands = {}

    def log(self, msg):
        log.msg("[%s] %s"%(self.__NAME__, msg))

    def getTwistedServiceCollection(self):
        return self.manager.getServiceCollection()

    def register_command(self, command, callback):
        self.targeted_commands[command] = callback
        log.msg("[%s] registered command %s"%(self.__NAME__, command))

    def message(self, channel, message):
        self.manager.SendPluginMessage(self.__NAME__, message, channel)

    def hasCommand(self, command):
        return command in self.targeted_commands

    def handleCommand(self, command, sender, args):
        self.targeted_commands[command](sender, args)

    def getUser(self, user):
        name = user.split("!")[0]
        host = user.split("@")[1]
        return User(name, host)