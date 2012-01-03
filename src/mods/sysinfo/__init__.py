from .. import plugin
from twisted.internet import reactor
import psutil
import os

def byte_format(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0

class Mod(plugin.Plugin):
    __NAME__ = "SysInfo"
    __VERSION__ = 0.1

    def __init__(self, manager, settings):
        plugin.Plugin.__init__(self, manager)

    def event_LOAD(self):
        self.register_command("memory", self.display_memory)
        self.register_command("disk", self.display_disk)
        self.register_command("io_counter", self.disk_io_counters)
        self.register_command("loadavg", self.load_average)
        self.register_command("cpu", self.cpu_load)

    def display_memory(self, sender, arguments):
        ''' Display the total, used and free memory values for the current system '''
        usage = psutil.phymem_usage()
        return self.message(sender, "Total: %s | Used: %s | Free: %s | Percent Free: %s"%(byte_format(usage.total),
                                                                                           byte_format(usage.used),
                                                                                           byte_format(usage.free),
                                                                                           usage.percent))

    def display_disk(self, sender, arguments):
        ''' Display the total, used and free disk values for the current system. Does not handle multiple disks.
        '''
        disk = psutil.disk_usage("/")
        return self.message(sender, "Total: %s | Used: %s | Free: %s | Percent Free: %s"%(byte_format(disk.total),
                                                                                           byte_format(disk.used),
                                                                                           byte_format(disk.free),
                                                                                           disk.percent))

    def disk_io_counters(self, sender, arguments):
        ''' Display the systems disk IO counters
        '''
        counters = psutil.disk_io_counters()
        return self.message(sender, "Read: %s (%s) | Write: %s (%s)"%(counters.read_count, byte_format(counters.read_bytes),
                                                                       counters.write_count, byte_format(counters.write_bytes)))

    def load_average(self, sender, arguments):
        ''' Display the systems load average. Only works on Linux.
        '''
        if not hasattr(os, "getloadavg"):
            return self.message(sender, "Cannot get the system load average, try using cpu average instead")

        return "%.2f %.2f %.2f"%os.getloadavg()

    def cpu_load(self, sender, arguments):
        ''' Return the average CPU utilization for all cores measured over 1 second
        '''
        reactor.callInThread(self._cpu_load,sender)

    def _cpu_load(self, sender):
        reactor.callFromThread(self.message, sender, "Measured CPU load over 1 second: %s"%psutil.cpu_percent(interval=1))