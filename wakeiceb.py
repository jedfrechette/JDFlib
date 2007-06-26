#!/usr/bin/env python
"""Send a wakeonlan packet to SiSkadi from outside the LAN."""

__author__ = 'Jed Frechette <jedfrechette@gmail.com>'
__version__ = '0.1'
__date__ = '26 June 2007'

from socket import gethostbyname
from subprocess import call

if __name__ == '__main__':
    hostname = 'iceb.ath.cx'
    ip = gethostbyname(hostname)
    hw_addr = '00:02:28:D6:B5:FC'

    cmd = 'wakeonlan'
    cmd_opts = '-i %s' %ip

    call([cmd, cmd_opts, hw_addr])
