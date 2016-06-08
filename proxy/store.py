from base64 import b64encode

class DataStore(object):
    ''' 
    Backing model for a given proxy. Exposes API for interacting with backing model.
    '''
    def __init__(self, session, topic):
        self.local = bytearray()
        self.remote = bytearray()
        self.localPackets = []
        self.remotePackets = []
        self.localopenlog = []
        self.localcloselog = []
        self.remoteopenlog = []
        self.remotecloselog = []

        self._registers = []
        self.session = session
        self.topic = topic

    def register(self, func):
        endpoint = func.__name__
        d = self.session.register(func, "%s.%s" % (self.topic, endpoint))
        def unregistercb(x):
            self._registers.append(x)
        d.addCallback(unregistercb)

    def registerAll(self):
        self.register(self.getBuffer)
        self.register(self.getPackets)
        self.register(self.getPacket)
        

    # Called by App

    def getBuffer(self, myType, start=None, end=None, encode=True):
        myType = myType.lower()
        if myType == "local":
            buff = self.local[start:end]
        elif myType == "remote":
            buff = self.remote[start:end]
        # This is hacky, consider re-design on the 'encode' aspect.
        if encode:
            return b64encode(buff)
        return buff

    def _serialize(self, packet, index, includeData=True):
        json = packet.serialize(includeData)
        json['index'] = index
        return json

    def getPackets(self, myType, start=None, end=None, includeData=False):
        myType = myType.lower()
        if myType == "local":
            packets = self.localPackets[start:end]
        elif myType == "remote":
            packets = self.remotePackets[start:end]
        res = []
        for i, p in enumerate(packets):
            res.append(self._serialize(p, i, includeData))
        return res

    def getPacket(self, myType, packetId):
        myType = myType.lower()
        if myType == "local":
            i, p = self.getLocalPacket(packetId)
            return self._serialize(p, i)
        if myType == "remote":
            i, p = self.getRemotePacket(packetId)
            return self._serialize(p, i)

    ''' WRITE '''
    def writeLocal(self, data):
        self.session.publish("%s.rawLocal" % self.topic, {
            'offset': len(self.local),
            'data': b64encode(data)
        })
        self.local = self.local + data

    def writeLocalPacket(self, packet):
        self.localPackets.append(packet)
        index = self.localPackets.index(packet)
        self.session.publish("%s.packetLocal" % self.topic, self._serialize(packet, index))
        '''
        index = self.localPackets.index(packet)
        self.session.publish("%s.packetLocal" % self.topic, {
            'position': len(self.localPackets) + 1,
            'packet': self._serialize(packet, index)
        })
        self.localPackets.append(packet)
        '''

    def writeRemote(self, data):
        self.session.publish("%s.rawRemote" % self.topic, {
            'offset': len(self.local),
            'data': b64encode(data)
        })
        self.remote = self.remote + data

    def writeRemotePacket(self, packet):
        self.remotePackets.append(packet)
        index = self.remotePackets.index(packet)
        self.session.publish("%s.packetRemote" % self.topic, self._serialize(packet, index))
        '''
        index = self.remotePackets.index(packet)
        self.session.publish("%s.packetRemote" % self.topic, {
            'position': len(self.localPackets) + 1,
            'packet': self._serialize(packet, index)
        })
        self.remotePackets.append(packet)
        '''

    ''' READ '''
    def getLocal(self, start=None, end=None):
        return self.local[start, end]

    def getLocalPackets(self):
        return self.localPackets
        
    def getRemote(self, start=None, end=None):
        return self.remote

    def getRemotePackets(self):
        return self.remotePackets

    def getLocalPacket(self, packetId):
        for i, p in enumerate(self.localPackets):
            if id(p) == packetId:
                return i, p
        return None

    def getRemotePacket(self, packetId):
        for i, p in enumerate(self.remotePackets):
            if id(p) == packetId:
                return i, p
        return None

    ''' RECORD '''

    def localRecordOpen(self):
        ''' Assists in cases where protocol message ends are dependant 
        on socket open/close (e.g. http/1.0)'''
        self.localopenlog.append(len(self.local))
        
    def localRecordClose(self):
        ''' Assists in cases where protocol message ends are dependant 
        on socket open/close (e.g. http/1.0)'''
        self.localcloselog.append(len(self.local))

    def remoteRecordOpen(self):
        ''' Assists in cases where protocol message ends are dependant 
        on socket open/close (e.g. http/1.0)'''
        self.remoteopenlog.append(len(self.remote))
        
    def remoteRecordClose(self):
        ''' Assists in cases where protocol message ends are dependant 
        on socket open/close (e.g. http/1.0)'''
        self.remotecloselog.append(len(self.remote))


        
