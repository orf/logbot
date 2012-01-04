from twisted.python import log
import importlib

class ModManager(object):
    def __init__(self, parent, config):
        self.handlers = []
        self.parent = parent

        for mod in config["mods"]:
            if config["mods"][mod]["enabled"]:
                try:
                    module = importlib.import_module("mods.%s"%mod)
                    self.handlers.append(module.Mod(self, config["mods"][mod].get("settings",None)))
                    log.msg("Loaded plugin %s v%s"%(mod, module.Mod.__VERSION__))
                except Exception:
                    log.err(_why="Could not import mod.%s"%mod)

    def getServiceCollection(self):
        return self.parent.getServiceCollection()

    def SendPluginMessage(self, *args):
        self.parent.SendPluginMessage(*args)

    def GotMessage(self, sender, args):
        module, command = args[:2]
        for handler in self.handlers:
            if handler.__NAME__.lower() == module.lower() and handler.hasCommand(command):
                #log.msg("Dispatching command %s - Sender: %s | Args: %s"%(command, sender, args[2:]))
                handler.handleCommand(command, sender, args[2:])

    def handleEvent(self, event_name, *args, **kwargs):
        for handler in self.handlers:
            if hasattr(handler, "event_%s"%event_name):
                getattr(handler, "event_%s"%event_name)(*args, **kwargs)