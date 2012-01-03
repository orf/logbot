from .. import plugin
#import inspect

class Mod(plugin.Plugin):
    __NAME__ = "Help"
    __VERSION__ = 0.1

    def __init__(self, manager, settings):
        plugin.Plugin.__init__(self, manager)

    def event_LOAD(self):
        self.register_command("help", self.help)

    def help(self, sender, arguments):
        ''' List all available modules, and if specified all the commands an addon has registered '''
        if len(arguments) == 0:
            # List available modules
            self.message(sender, "Available mods:")
            for mod in self.manager.handlers:
                self.message(sender, " * %-10s v%s"%(mod.__NAME__, mod.__VERSION__))
        else:
            # List a specific addons commands, complete with docstrings.
            for mod in self.manager.handlers:
                if mod.__NAME__ == arguments[0]:
                    break
            else:
                return self.message(sender, "Module %s not found!"%arguments[0])

            self.message(sender, "Available commands for module %s:"%mod.__NAME__)
            for command in mod.targeted_commands:
                self.message(sender, " * %-15s %s"%(command, mod.targeted_commands[command].__doc__))