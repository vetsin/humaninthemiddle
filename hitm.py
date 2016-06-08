from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import ClientCreator, ServerFactory
from twisted.logger import Logger
from twisted.internet import reactor

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.exception import ApplicationError

#from proxy import ReceiverFactory, ProxyReceiverFactory
from proxy.receiver import HITMReceiver, ProxyReceiverFactory
from proxy.protocol import HITMChannel, TcpLocal, TcpRemote

import json, tempfile, shutil, os

# TODO: make dynamic
CONFIG_PATH = "configs"

class ProxySession(ServerFactory):
    factory = None
    def __init__(self, localPort, remoteHost, remotePort, session, configFile):
        self._localPort = localPort
        self._remoteHost = remoteHost
        self._remotePort = remotePort
        self._session = session
        self._defaultConfig = configFile
        self._openReceivers = [] 
        self._topic = "com.hitm.%s" % localPort # TODO: change to com.hitm.uniquieid.%s

        #self._receiverFactory = ProxyReceiverFactory(self._receiver)
        #self._channel = HITMChannel(self._loadConfig(configFile), self._session, self._topic)

    def _loadChannel(self, configFile, cb):
        def setChannel(config):
            self._channel = HITMChannel(config, self._session, self._topic)
            cb()
        val = self._session.call(u'com.hitm.config.read', configFile)
        val.addCallback(setChannel)
        return val

    def startFactory(self):
        print('Proxy Started to %s:%s' % (self._remoteHost, self._remotePort))
        self._channel.registerSession()

    def stopFactory(self):
        print('Proxy Stopped to %s:%s' % (self._remoteHost, self._remotePort))
        self._channel.unregisterSession()

    def connectTcp(self, host, port, *args):
        p = ClientCreator(reactor, TcpRemote, *args).connectTCP(host, port)
        return p

    def buildProtocol(self, addr):
        print("Connection Building")
        p = TcpLocal(self._channel, self._remoteHost, self._remotePort)
        p.factory = self
        return p

    def start(self):
        def scb():
            self._twistedPort = reactor.listenTCP(self._localPort, self)
        self._loadChannel(self._defaultConfig, scb)

    def startUDP(self):
        self._twistedPort = reactor.listenUDP(self._localPort, self)

    def stop(self):
        if self._twistedPort:
            self._twistedPort.stopListening()

    def serialize(self):
        return {
            #"id": self._id,
            "localPort": self._localPort,
            "remoteHost": self._remoteHost,
            "remotePort": self._remotePort
        }

class HITMSession(ApplicationSession):

    log = Logger()
    running = {}
    _receiver = HITMReceiver # temp?

    def startTCPListener(self, localPort, remoteHost, remotePort, config):
        self.log.info("Starting TCP proxy %s:%s:%s" % (localPort, remoteHost, remotePort))
        session = ProxySession(localPort, remoteHost, remotePort, self, config)
        session.start()
        self.running[localPort] = session

    def startUDPListener(self, localPort, remoteHost, remotePort):
        self.log.info("Starting UDP proxy %s:%s:%s" % (localPort, remoteHost, remotePort))
        session = ProxySession(localPort, remoteHost, remotePort, self, self._receiver)
        session.startUDP()
        self.running[localPort] = session

    def stopTCPListener(self, localPort):
        self.running[localPort].stop()
        del self.running[localPort]

    @inlineCallbacks
    def onJoin(self, details):
        # Register start()
        def start(localPort, remoteHost, remotePort, config='default.config'):
            self.startTCPListener(localPort, remoteHost, remotePort, config)
            return "Running TCP proxy %s:%s:%s" % (localPort, remoteHost, remotePort)

        yield self.register(start, 'com.hitm.start')

        def startUDP(localPort, remoteHost, remotePort):
            self.startUDPListener(localPort, remoteHost, remotePort)
            return "Running UDP proxy %s:%s:%s" % (localPort, remoteHost, remotePort)

        ## TESTING auto-start testing proxies
        start(8000, '127.0.0.1', 8001, "http.config")

        start(1053, '192.168.2.1', 53, "dns.config")

        # Register stop()
        def stop(localPort):
            self.stopTCPListener(localPort)
            return "Stopping"

        yield self.register(stop, 'com.hitm.stop')

        # Register list()
        def list():
            return json.dumps([self.running[x].serialize() for x in self.running])

        yield self.register(list, 'com.hitm.list')

        # Load Config
        #yield self.register(self.loadConfig, 'com.hitm.config.load')



# TODO: make dynamic
CONFIG_PATH = "../configs"

class ConfigService(ApplicationSession):

    log = Logger()
    
    def listConfigs(self):
        files = [f for f in os.listdir(CONFIG_PATH) if os.path.isfile(os.path.join(CONFIG_PATH, f))]
        return files

    def getConfig(self, name):
        return json.loads(open(os.path.join(CONFIG_PATH, name),'r').read())

    def writeConfig(self, name, content):
        fd, filename = tempfile.mkstemp()
        try:
            os.write(fd, json.dumps(content))
            os.close(fd)
            shutil.copy(filename, os.path.join(CONFIG_PATH, name))
        finally:
            os.remove(filename)

    @inlineCallbacks
    def onJoin(self, details):
        yield self.register(self.listConfigs, 'com.hitm.config.list')
        yield self.register(self.getConfig, 'com.hitm.config.read')
        yield self.register(self.writeConfig, 'com.hitm.config.write')
