from proxy.receiver import PacketFactory, HITMReceiver, HITMPacket
from pypacker.layer567 import dns

class DNSPacket(dns.DNS, HITMPacket):
    def getHeaders(self):
        return self.hdr

    def getBody(self):
        return self.data

    def getData(self):
        return self.bin()

class MyFactory(PacketFactory):
    packet = DNSPacket
    
class DNSReceiver(HITMReceiver):
    packetFactory = MyFactory

    def isComplete(self, packet, openlog, closelog, start, total):
        print(openlog)
        print(closelog)
        print(start)
        print(total)
        for point in closelog:
            if point > start and total >= point:
                return True, point - start
        return True, len(packet)

    def packetReceived(self, packet):
        print("Packet Recieved!")
        print(repr(packet.bin()))
        self.logPacket(packet)

    def sendPacket(self, packet):
        self.write(packet.bin())
