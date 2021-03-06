#!/usr/bin/env python
"""Send a wakeonlan packet to epsll from inside the EPS LAN."""

__author__ = 'Jed Frechette <jdfrech@unm.edu>'
__version__ = '0.1'
__date__ = '28 May 2008'

import socket
import struct

if __name__ == '__main__':
    hostname = 'epsll.unm.edu'
    ip = socket.gethostbyname(hostname)
    hw_addr = '0003ba29ae13'

    print "Sending magic packet to %s with %s" % (ip, hw_addr)
    # Pad the synchronization stream.
    data = ''.join(['FFFFFFFFFFFF', hw_addr * 20])
    send_data = '' 

    # Split up the hex values and pack.
    for i in range(0, len(data), 2):
        send_data = ''.join([send_data,
                             struct.pack('B', int(data[i: i + 2], 16))])

    # Broadcast it to the LAN.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, (ip, 9))
