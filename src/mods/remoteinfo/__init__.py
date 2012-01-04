from twisted.web import server, resource
from twisted.application import internet
from .. import plugin
import platform
from twisted.python import log

if not platform.system() == "Linux":
    import win32pdh

class StatBase(resource.Resource):
    def __init__(self, settings):
        self.settings = settings
        resource.Resource.__init__(self)

    def render(self, request):
        qs = request.args.get("pass",[])
        if not len(qs):
            return ""
        if not qs[0] == self.settings["auth_key"]:
            return ""

        return self.GetStat(request)

    def GetStat(self, request):
        raise NotImplementedError

class GetUptime(StatBase):
    def GetStat(self, request):
        if platform.system() == "Windows":
            path = win32pdh.MakeCounterPath( ( None, 'System', None, None, 0, 'System Up Time') )
            query = win32pdh.OpenQuery()
            handle = win32pdh.AddCounter( query, path )
            win32pdh.CollectQueryData( query )
            return str(win32pdh.GetFormattedCounterValue( handle, win32pdh.PDH_FMT_LONG | win32pdh.PDH_FMT_NOSCALE )[1])
        else:
            with open("/proc/uptime") as fd:
                return fd.read().split(" ")[0]


class Mod(plugin.Plugin):
    __NAME__ = "RemoteInfo"
    __VERSION__ = 0.1

    def __init__(self, manager, settings):
        self.settings = settings
        log.msg(self.settings)
        plugin.Plugin.__init__(self, manager)

    def event_LOAD(self):
        application = self.getTwistedServiceCollection()
        root = resource.Resource()
        if self.settings.get("uptime",False):
            self.log("Uptime enabled")
            root.putChild("uptime", GetUptime(self.settings))
        internet.TCPServer(self.settings.get("listen_port",2000), server.Site(root)).setServiceParent(application)

