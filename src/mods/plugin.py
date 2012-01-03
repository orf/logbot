from twisted.python import log

class Plugin(object):
    __NAME__ = None
    __VERSION__ = None

    def __init__(self, manager):
        self.manager = manager
        self.targetted_commands = {}

    def register_command(self, command, callback):
        self.targetted_commands[command] = callback
        log.msg("[%s] registered command %s"%(self.__NAME__, command))

    def message(self, channel, message):
        self.manager.SendPluginMessage(self.__NAME__, message, channel)

    def hasCommand(self, command):
        return command in self.targetted_commands

    def handleCommand(self, command, channel, user, args):
        self.targetted_commands[command](channel, user, args)