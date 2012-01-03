from twisted.python import log
import importlib

class ModManager(object):
    def __init__(self, parent, config):
        self.handlers = []

        for mod in config["mods"]:
            try:
                module = importlib.import_module("mods.%s"%mod)
                self.handlers.append(module.Mod(self, config["mods"][mod].get("settings",None)))
                log.msg("Loaded plugin %s v%s"%(mod, module.Mod.__VERSION__))
            except Exception:
                log.err(_why="Could not import mod.%s"%mod)

    def GotMessage(self, user, channel, args):
        command = args[0]
        for handler in self.handlers:
            if handler.hasCommand(command):
                handler.handleCommand(command, user, channel, args)

    def handleEvent(self, event_name, *args, **kwargs):
        for handler in self.handlers:
            if hasattr(handler, "event_%s"%event_name):
                getattr(handler, "event_%s"%event_name)(*args, **kwargs)