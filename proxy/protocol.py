from twisted.internet.protocol import Protocol
from proxy.store import DataStore
from proxy.receiver import ProxyReceiverFactory
from base64 import b64encode, b64decode

(ESTABLISHED, DISCONNECTED) = range(2) 
(REQUEST_INTERCEPT, RESPONSE_INTERCEPT, INTERCEPT, WATCH) = range(4) 

DEFAULT_CHUNK=1024

class BaseProtocol(object):
    ''' Does NOT inherient from twisted.internet.protocol.Protocol '''
    state = {'state': DISCONNECTED, 'mode': WATCH}

class HITMChannel(BaseProtocol):
    """ The HITM Pipe instanced once a proxy is started"""

    _localBuffer = b''
    _remoteBuffer = b''
    disconnecting = 0
    _registers = []

    def __init__(self, config, session, topic):
        print('init HITMChannel')
        self.state['mode'] = WATCH
        #self.state['mode'] = REQUEST_INTERCEPT
        #self.state['mode'] = RESPONSE_INTERCEPT
        #self.state['mode'] = INTERCEPT
        self._receiverFactory = ProxyReceiverFactory()

        self.dataStore = DataStore(session, topic)
        self.dataStore.registerAll()

        self.session = session
        self._config = config
        self.topic = topic
        #self._registerSession()
        self.loadProtocols()

    def loadProtocols(self, local=True, remote=True):
        if self._config:
            if local:
                self._receiverFactory.receiverClass = self._config['local']['receiver']
                self.localProtocol = self._receiverFactory.buildReceiver()
                #self.localProtocol.write = self.remoteWrite # TODO: validate this...
                self.localProtocol.logPacket = self.localPacketReceived
            if remote:
                self._receiverFactory.receiverClass = self._config['remote']['receiver']
                self.remoteProtocol = self._receiverFactory.buildReceiver()
                self.remoteProtocol.logPacket = self.remotePacketReceived

    def registerSession(self):
        self.dataStore.registers = []
        #self._register(self.getBuffer)
        self.dataStore.register(self.setMode)
        self.dataStore.register(self.applyConfig)
        self.dataStore.register(self.validatePacket)
        self.dataStore.register(self.getConfig)
        self.dataStore.register(self.loadProtocols)
        #self._register(self.getPackets)
        #self._register(self.getPacket)
        self.dataStore.register(self.reprocess)

    def unregisterSession(self):
        for r in self._registers:
            r.unregister()

    def _getProtocol(self, myType):
        if myType.lower() == "local":
            return self.localProtocol
        elif myType.lower() == "remote":
            return self.remoteProtocol

    def applyConfig(self, myType, config):
        self._config = config
        return self._getProtocol(myType.lower()).loadConfig(config[myType])

    def getConfig(self, myType):
        return self._config[myType.lower()]

    def validatePacket(self, myType, start, end):
        buff = self.dataStore.getBuffer(myType, start, end, False)
        data, size = self._getProtocol(myType).validatePacket(buff)
        return b64encode(data), size

    def setLocalTransport(self, localTransport):
        self.localTransport = localTransport
        self.localProtocol.transport = self.localTransport
        self.localFlush()

    def setRemoteTransport(self, remoteTransport):
        self.remoteTransport = remoteTransport
        self.remoteProtocol.transport = self.remoteTransport
        self.remoteFlush()

    def setMode(self, mode):
        if mode == 'REQUEST_INTERCEPT':
            self.mode = REQUEST_INTERCEPT
        if mode == 'RESPONSE_INTERCEPT':
            self.mode = RESPONSE_INTERCEPT
        if mode == 'INTERCEPT':
            self.mode = INTERCEPT
        if mode == 'WATCH':
            self.mode = WATCH

    def reprocess(self, myType, chunk=DEFAULT_CHUNK):
        """ Reprocess a stream, chunk bytes at a time to simulate fragmentation """
        # TODO: may need a lock to avoid issues of a current connection 
        # being processed at the same time
        myType = myType.lower()
        if myType == "local":
            self.reprocessLocal(chunk)
        if myType == "remote":
            self.reprocessRemote(chunk)

    def reprocessLocal(self, chunk=DEFAULT_CHUNK):
        self.dataStore.localPackets = []
        self.localProtocol.clearBuffer()
        start = 0
        while(len(self.dataStore.local) > start):
            self.localProtocol.dataReceived(self.dataStore.local[start:start+chunk], self.dataStore.localopenlog, self.dataStore.localcloselog)
            start = start + chunk if chunk else len(self.dataStore.local)

    def reprocessRemote(self, chunk=DEFAULT_CHUNK):
        print(self.dataStore.remote)
        self.dataStore.remotePackets = []
        self.remoteProtocol.clearBuffer()
        start = 0
        while(len(self.dataStore.remote) > start):
            self.remoteProtocol.dataReceived(self.dataStore.remote[start:start+chunk], self.dataStore.remoteopenlog, self.dataStore.remotecloselog)
            start = start + chunk if chunk else len(self.dataStore.remote)

    # Local <- Remote
    def remoteRead(self, data):
        ''' TcpRemote recv '''
        self._remoteBuffer = self._remoteBuffer + data
        self.dataStore.writeRemote(data)
        self.localFlush()
        return data


    def localFlush(self):
        if self.state['state'] == ESTABLISHED:
            self.remoteProtocol.dataReceived(self._remoteBuffer, self.dataStore.remoteopenlog, self.dataStore.remotecloselog)
            if self.state['mode'] == RESPONSE_INTERCEPT or self.state['mode'] == INTERCEPT:
                self.localWrite(self._remoteBuffer)
            self._remoteBuffer = b''

    def localWrite(self, data):
        ''' TcpLocal write '''
        #print('localWrite')
        self.localTransport.write(data)

    def remotePacketReceived(self, packet):
        self.dataStore.writeRemotePacket(packet)

    # Local -> Remote
    def localRead(self, data):
        ''' TcpLocal read '''
        self._localBuffer = self._localBuffer + data
        self.dataStore.writeLocal(data)
        self.remoteFlush()

    def remoteFlush(self): 
        if self.state['state'] == ESTABLISHED:
            self.localProtocol.dataReceived(self._localBuffer, self.dataStore.localopenlog, self.dataStore.localcloselog)
            if self.state['mode'] == REQUEST_INTERCEPT or self.state['mode'] == INTERCEPT:
                self.remoteWrite(self._localBuffer)
            self._localBuffer = b''
        
    def remoteWrite(self, data):
        ''' TcpRemote write '''
        self.remoteTransport.write(data)

    def localPacketReceived(self, packet):
        self.dataStore.writeLocalPacket(packet)

    # Connect/Lost
    def localConnectionMade(self):  
        self.dataStore.localRecordOpen()

    def localConnectionLost(self, reason):
        self.dataStore.localRecordClose()
        self.localProtocol.dataReceived(b'', self.dataStore.localopenlog, self.dataStore.localcloselog)

    def remoteConnectionMade(self):  
        self.dataStore.remoteRecordOpen()

    def remoteConnectionLost(self, reason):
        self.dataStore.remoteRecordClose()
        # Then bubble up our close event for us to process
        self.remoteProtocol.dataReceived(b'', self.dataStore.remoteopenlog, self.dataStore.remotecloselog)

class TcpRemote(BaseProtocol, Protocol):
    """ Connect to remote port, instanced once a TcpLocal connection is made """

    def __init__(self, father, protocol):
        self._buffer = b''
        self._father = father
        self.protocol = protocol
        self.state['state'] = DISCONNECTED

    def connectionMade(self):
        print('Connection made to remote host %s' % str(self.transport.getPeer()))
        self.protocol.remoteConnectionMade()
        self._father.setOutgoing(self)
        self.state['state'] = ESTABLISHED
        self.protocol.setRemoteTransport(self.transport)
        # Make sure we get anything that could be waiting to push to remote
        self._father.flush()

    def connectionLost(self, reason):
        print('Connection lost to remote host %s reason %s' % (str(self.transport.getPeer()), reason or 'unknown'))
        self.protocol.remoteConnectionLost(reason)
        if self._father:
            # Disconnect Local
            self._father.setOutgoing(None)
            self._father.transport.loseConnection()
            self.state['state'] = DISCONNECTED

    def dataReceived(self, data):
        self.protocol.remoteRead(data)
        self._buffer = self._buffer + data
        self.flush()

    def flush(self):
        if self.state['state'] == ESTABLISHED:
            if self.state['mode'] != RESPONSE_INTERCEPT and self.state['mode']!= INTERCEPT:
                self._father.write(self._buffer)
                self._buffer = b''

    def write(self, data):
        self.transport.write(data)

class TcpLocal(BaseProtocol, Protocol):
    """ Handle local connections, instnaced once a connection is made to a local port """

    def __init__(self, protocol, server, port):
        self._buffer = b''
        self._server = server
        self._port = port
        self.protocol = protocol

    def setOutgoing(self, outgoing):
        self._outgoing = outgoing

    def connectionMade(self):
        print('Connection made to proxy from %s' % str(self.transport.getPeer()))
        self.protocol.localConnectionMade()
        if self.state['state'] == DISCONNECTED:
            self.protocol.setLocalTransport(self.transport)
            self.remote = self.factory.connectTcp(self._server, self._port, self, self.protocol)
            self.remote.addErrback(lambda result, self=self: self.transport.loseConnection())

    def connectionLost(self, reason):
        print('Connection lost to proxy from  %s reason %s' % (str(self.transport.getPeer()), reason or 'unknown'))
        self.protocol.localConnectionLost(reason)
        if self._outgoing:
            # Disconnect Remote
            self._outgoing.transport.loseConnection()
            self._outgoing = None
            self.protocol = None
        self.state['state'] = DISCONNECTED

    def dataReceived(self, data):
        self.protocol.localRead(data)
        self._buffer = self._buffer + data
        self.flush()

    def flush(self):
        if self.state['state'] == ESTABLISHED:
            if self.state['mode'] != REQUEST_INTERCEPT and self.state['mode'] != INTERCEPT:
                self._outgoing.write(self._buffer)
                self._buffer = b''

    def write(self, data):
        self.transport.write(data)


