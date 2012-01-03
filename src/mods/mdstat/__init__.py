from .. import plugin
import os

class Mod(plugin.Plugin):
    __NAME__ = "MDStat"
    __VERSION__ = 0.1

    def __init__(self, manager, settings):
        plugin.Plugin.__init__(self, manager)

    def event_LOAD(self):
        self.register_command("display", self.display_mdstat)

    def display_mdstat(self, sender, arguments):
        ''' Display the output of /proc/mdstat '''
        if not os.path.exists("/proc/mdstat"):
            return self.message(sender, "Cannot find /proc/mdstat")
        with open("/proc/mdstat","r") as fd:
            for line in fd.readlines():
                self.message(sender, line)