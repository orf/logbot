from twisted.words.protocols import irc
from twisted.protocols import basic
from twisted.internet import reactor, ssl, protocol, defer
from twisted.python import log
from zope.interface import implements
from twisted.application import internet, service
from twisted.python.logfile import DailyLogFile
from twisted.python.log import  FileLogObserver
from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer
import os

import urllib
import sys
import time
import yaml
import platform
import re
import shlex

import mods

class Producer(object):
    implements(IBodyProducer)

    def __init__(self, line, time, fname):
        self.line = line
        self._fname = fname
        self._time = time
        self.length = len(line)

    def startProducing(self, consumer):
        consumer.write(urllib.urlencode({"line":self.line,"time":self._time,
                                         "file":self._fname}))
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

#log.startLogging(sys.stdout)


class TailedFile(object):
    def __init__(self, name, location, channel = None):
        self.name = name
        self.location = location
        self.channel = channel

        self.queue = defer.DeferredQueue()

    def enqueue(self, time, message):
        self.queue.put( (time, message,) )

    def pop(self):
        return self.queue.get()


class FileManager(object):
    def __init__(self, config, services):
        self.files = []

        self.irc = None
        self.services = services
        internet.SSLClient(LOGBOT_LOCATION, LOGBOT_PORT, LogBotFactory(self), ssl.ClientContextFactory()
                            ).setServiceParent(services)
        self.mods = mods.ModManager(self, config)
        self.mods.handleEvent("LOAD")

    def getServiceCollection(self):
        return self.services

    def SendPluginMessage(self, plugin_name, message, channel):
        if self.irc:
            self.irc.sendmsg("[%s] %s"%(plugin_name, message), channel=channel)

    def tail_closed(self, file_name, status):
        if self.irc:
            self.irc.sendmsg("Tail for file name %s closed! Status: %s"%(file_name, status))

    def error_callback(self, name, data):
        if self.irc:
            self.irc.sendmsg("Tail Error (%s)"%name, data)

    def add_file(self, file_o):
        self.files.append(file_o)
        self.spawnTail(file_o)

    def spawnTail(self, file_o):
        tail = TailProtocol(file_o, self.tail_closed, self.error_callback)
        reactor.spawnProcess(tail, TAIL_LOCATION , args=["tail","--retry","--lines","0",
                                                         "-F",file_o.location])
        self.followTailedFile(file_o)

    @defer.inlineCallbacks
    def followTailedFile(self, file_o):
        while True:
            line_time, line = yield file_o.pop()
            #TODO: what if irc fails?
            if self.irc:
                self.irc.emit(file_o.name, line, channel=file_o.channel)
            self.mods.handleEvent("DATA", file_o, line)

class TailProtocol(protocol.ProcessProtocol, basic.LineOnlyReceiver):
    delimiter = "\n"

    disconnecting = False

    def __init__(self, file_o, closed_callback, error_callback):
        self.closed_callback = closed_callback
        self.error_callback = error_callback
        self.file = file_o

    def connectionMade(self):
        self.transport.disconnecting = False

    # Handing
    def lineReceived(self, line):
        self.file.enqueue(time.time(), line)

    # Termination
    def processEnded(self, status):
        self.closed_callback(self.file.name, status)

    # Handle STDOUT and STDIN
    def outReceived(self, data):
        #log.msg("Got data: %s"%repr(data))
        self.dataReceived(data)

    def errReceived(self, data):
        log.msg("Err: %s"%data)
        self.error_callback(self.file.name, data)


class LogBot(irc.IRCClient):

    @property
    def nickname(self):
        return "LogBot|"+LOGBOT_NAME

    def signedOn(self):
        if all(OPER_CREDENTIALS):
            self.sendLine("OPER %s %s"%OPER_CREDENTIALS)
        log.msg("Signed on")
        self.factory.resetDelay()
        self.join(LOGBOT_CHANNEL)
        for channel in OTHER_CHANNELS:
            self.join(channel)
        self.factory.file_manager.irc = self

    def joined(self, channel):
        if (not channel == LOGBOT_CHANNEL) and (not channel in OTHER_CHANNELS):
            self.leave(channel)

    def privmsg(self, user, channel, message):
        if user.startswith("LogBot|"):
            return # Ignore messages from other LogBots
        split = shlex.split(message, posix=False)

        matched = False
        if not channel == self.nickname:

            if not len(split) >= 3: # Target Module Command
                return

            if split[0] == self.nickname:
                print "Nickname matched"
                matched = True
                args = split[1:]
                sender = channel
            else:
                return
            '''else:
                try:
                    if re.match(split[0], self.nickname):
                        matched = True
                        args = split[1:]
                        sender = channel
                except Exception:
                    pass'''
        else:
            if not len(split) >= 2: # Module Command
                return
            matched = True
            args = split
            sender = user.split("!")[0]

        if matched:
            print sender, args
            self.factory.file_manager.mods.GotMessage(sender, args)

    def sendmsg(self, message, channel=None):
        if channel:
            if channel[0] == "#":
                self.say(channel, message, length=200)
            else:
                self.msg(channel, message, length=200)
        else:
            self.say(LOGBOT_CHANNEL, message, length=200)

    def emit(self, name, message, channel=None):
        self.say(channel or LOGBOT_CHANNEL, "%s: %s"%(name, message), length=200)


class LogBotFactory(protocol.ReconnectingClientFactory):
    protocol = LogBot

    def __init__(self, file_manager):
        self.file_manager = file_manager


if __name__ in ("__main__", "__builtin__"):
    with open("config.yaml","r") as fd:
        config = yaml.load(fd)
    LOGBOT_CHANNEL  = config["server"]["channel"]
    LOGBOT_LOCATION = config["server"]["ip"]
    LOGBOT_PORT     = config["server"]["port"]
    LOGBOT_NAME     = config["server"]["name"] or platform.node().split(".")[0][:15]
    if not LOGBOT_NAME:
        print "Cannot detect a name for the client (usually means the system hostname cannot be detected)"
        sys.exit(1)

    OPER_CREDENTIALS = (config["server"]["user"], config["server"]["password"])
    TAIL_LOCATION = config["logbot"]["tail_location"][platform.system().lower()]

    OTHER_CHANNELS = [config["files"][x].get("channel",None) for x in config["files"]
                                                             if config["files"][x].get("channel",None)]

    application = service.Application('LogBot')#, uid=1, gid=1)
    if not os.path.exists("logs"):
        os.mkdir("logs")
    logfile = DailyLogFile("logbot.log","logs")
    log_observer = FileLogObserver(logfile).emit
    #application.setComponent(ILogObserver, log_observer)
    log.addObserver(log_observer)
    serviceCollection = service.IServiceCollection(application)
    manager = FileManager(config, serviceCollection)
    for item in config["files"]:
        manager.add_file(TailedFile(item,
            config["files"][item]["path"],
            config["files"][item].get("channel",None)
        ))