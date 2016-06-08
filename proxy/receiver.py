from twisted.protocols import basic
from twisted.logger import Logger
from twisted.internet import reactor, protocol
from twisted.internet.protocol import Factory
from pypacker.layer567 import dns
from importlib import reload
from base64 import b64encode, b64decode

"""
class HITMPacket(object):
    ''' Attempts to decode packets based on configuration '''
    _isComplete = False
    _packet = b''
    _config = {}
    # Default binary type
    _type = 'binary'
    _end = 0

    def __init__(self, config, data): #, channel, queued):
        self._load_config(config)
        self.data = data
        self._parse()
        #self.channel = channel
        #self.queued = queued

    def _load_config(self, config):
        if config != None:
            self._config = config
        if 'packet' in self._config:
            if 'type' in self._config['packet']:
                self._type = self._config['packet']['type']

    def _get_config(self):
        return self._config

    def _parse(self):
        if self._type == "line":
            self._lineParse()
        else:
            self._binaryParse()

    def _lineParse(self):
        lineDelimiter = self._config['packet']['lineDelimiter']
        packetDelimiter = self._config['packet']['packetDelimiter']
        if self.data.count(packetDelimiter) == 0:
            self._isComplete = False
            return
        splitIndex = self.data.index(packetDelimiter)
        self._packet = self.data[:splitIndex]
        # Packet end including delimiter
        self._end = splitIndex + len(packetDelimiter)
        lines = self._packet.split(lineDelimiter)
        print(lines)

    def _binaryParse(self):
        packet = dns.DNS(self.data)
        
    def isComplete(self):
        return self._isComplete

    def __len__(self):
        return 0

    def getSize(self):
        return self._end

    def bin(self):
        return self._packet

    def process(self):
        ''' Override in subclass '''
        pass

#class TestPacket(dns.DNS):
    #def __getattribute__        
     
"""

class HITMPacket(object):
    ''' To support serialization to UI for activities '''
    start = 0
    end = 0

    def getHeaders(self):
        raise Exception('Implement')

    def getBody(self):
        raise Exception('Implement')

    def getData(self):
        raise Exception('Implement')

    def setPosition(self, start, end):
        self.start = start
        self.end = end

    def serialize(self, includeData=True):
        r = {
            "id": id(self),
            "len": len(self),
            "start": self.start,
            "end": self.end
        }
        if(includeData):
            r["data"] = b64encode(self.getData())
            r["headers"] = self.getHeaders()
            r["body"] = b64encode(self.getBody())
        return r

    def __str__(self):
        return str(self.serialize())

class PacketFactory(object):
    """ Default Packet Generator """
    packet = HITMPacket

    def buildPacket(self, data):
        return self.packet(data)

class HITMReceiver(protocol.Protocol):
    """ The Configuration based Receiver instanced per tcp connection """
    log = Logger()
    _bytelog = 0
    _seek = 0
    _buffer = b''
    _busyReceiving = False
    packetFactory = PacketFactory
    MAX_LENGTH = 16394

    def __init__(self):
        self._config = { 'stream': None, 'packet': {}, 'constants': {} }

    def _bufferWrite(self, data):
        self._buffer += data
        self._bytelog = self._bytelog + len(data)

    def dataReceived(self, data, openlog=None, closelog=None):
        #print(b'dR' + data)
        if self._busyReceiving:
            self._bufferWrite(data)
            return
        try:
            self._busyReceiving = True
            self._bufferWrite(data)
            print(b'processing: ' + self._buffer)

            # Could have multiple 'packets' within the data stream
            continueProcessing = True
            while(continueProcessing and (len(self._buffer) > 0)):
                packet = self.packetFactory().buildPacket(self._buffer)
                isComplete, size = self.isComplete(packet, openlog, closelog, self._seek, self._bytelog)
                if isComplete:
                    print('isComplete! %s' % size)
                    # only sub packet size from buffer
                    validPacket = self.packetFactory().buildPacket(self._buffer[:size])
                    validPacket.setPosition(self._seek, self._seek+size)
                    self._seek = self._seek + size
                    self._buffer = self._buffer[size:]
                    #self._bytelog = self._bytelog + size
                    self.packetReceived(validPacket)
                else:
                    continueProcessing = False
        except Exception as e:
            print('Error in dataReceived')
            print(e)
        finally:
            self._busyReceiving = False
            
    def isComplete(self, packet, openlog, closelog, start, total):
        '''
        :param packet: The packet constructed within dataReceieve from the packetFactory
        :param openlog: A list containing integers which are points in the byte stream connections where opened
        :param closelog: A list contianing integers which are points in the byt estream connections were closed
        :param seek: The current point in the byte stream
        '''
        if len(packet.bin()) == 0:
            return False, -1
        if packet.bin() == self._buffer[:len(packet)]:
            return True, len(packet)
        return False, -1

    def packetReceived(self, packet):
        ''' Override to do something with valid packets received '''
        self.logPacket(packet)

    def logPacket(self, packet):
        raise Exception('This should be over-ridden by HITMChannel')

    def clearBuffer(self):
        self._buffer = b''
        self._bytelog = 0
        self._seek = 0
        
    def sendPacket(self, packet):
        print('sendPacket')
        pass
        #self.write(packet.bin())
        #self.transport.write(packet.bin())

    def loadConfig(self, config):
        self._config = config
        self.log.info('Loaded configuration file')
        return config

    def getConfig(self):
        return self._config

    def validatePacket(self, buff):
        """ Validates packet by parsing buff into a packet and returning the resultant binary and the length of the packet """
        packet = self.packetFactory().buildPacket(buff)
        return packet.bin(), len(packet)


class ReceiverFactory(Factory):

    def __init__(self, receiverClass='proxy.receiver.HITMReceiver'):
        self.receiverClass = receiverClass

    def _load(self, name):
        components = name.split('.')
        mod = __import__('.'.join(components[:-1]), fromlist=[components[-1]])
        reload(mod)
        return getattr(mod, components[-1]) 

    def buildReceiver(self, receiverClass=None):
        if receiverClass == None:
            return self._load(self.receiverClass)()
        return self._load(receiverClass)()

class ProxyReceiverFactory(ReceiverFactory):

    def startFactory(self):
        ''' When you start listening '''
        print('PROTOCOL STARTED')

    def stopFactory(self):
        ''' Called when you stop listening '''
        print('PROTOCOL STOPPED')
