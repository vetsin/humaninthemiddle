from proxy.receiver import PacketFactory, HITMReceiver, HITMPacket
from pypacker.layer567 import http

class HTTPPacket(http.HTTP, HITMPacket):
    def getHeaders(self):
        return self.hdr

    def getBody(self):
        return self.data

    def getData(self):
        return self.bin()

class MyFactory(PacketFactory):
    packet = HTTPPacket

class HTTPReceiver(HITMReceiver):
    packetFactory = MyFactory

    def isComplete(self, packet, openlog=None, closelog=None, start=-1, total=-1):
        # Ensure the packet is unpacked
        str(packet) # How do i do this any other way?
        data = packet.bin()
        headers = packet.hdr
        #print(packet)
        #print(closelog)
        # Check for Content-Length
        for header, content in headers:
            if header.lower() == b'content-length':
                l = int(content)
                #print('ret?')
                if len(packet.data) >= l:
                    #print('ret!!!')
                    return True, packet.header_len+l
        # Annoying, non-compliant responses or HTTP/1.0
        #print('cl: %s' % closelog)
        if closelog:
            for point in closelog:
                # If there was a socket closure within this body
                #print('p: %s' % point)
                #print('s: %s' % start)
                #print('t: %s' % total)
                calcend = (start+packet.header_len+len(packet.data))
                if point > start and calcend >= point and total >= point:
                    return True, point - start
                        
        return False, -1

    def packetReceived(self, packet):
        #print("Packet Recieved: ")
        # To log the packet
        #print(packet)
        #print("\n")
        self.logPacket(packet)

    def sendPacket(self, packet):
        self.write(packet.bin())
