
def dumpPacket(data, rows = 16):
	''' Return string hexidecimal representation of data for printing '''
        out = []
        out.append(data.encode("hex"))
        lines = len(data) / rows
        if lines * rows != len(data):
                lines += 1
        for i in xrange(lines):
                d = tuple(data[rows * i:rows * i + rows])
                hex = map(lambda x: '%02X' % ord(x), d)
                text = map(lambda x: (len(repr(x)) > 3 and '.') or x, d)
                out.append(' '.join(hex) + ' ' * 3 * (rows - len(d)) + ' ' + ''.join(text))
        #return data
        return '\n'.join(out)

