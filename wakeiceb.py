#!/usr/bin/env python
"""Send a wakeonlan packet to SiSkadi from outside the LAN."""

__author__ = 'Jed Frechette <jedfrechette@gmail.com>'
__version__ = '0.1'
__date__ = '22 July 2007'

import socket
import struct

if __name__ == '__main__':
    hostname = 'iceb.ath.cx'
    ip = socket.gethostbyname(hostname)
    hw_addr = '00022AD6B5FC'

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