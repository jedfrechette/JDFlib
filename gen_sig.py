#!/usr/bin/env python
"""Generate a .signature file."""

__author__ = 'Jed Frechette <jedfrechette@gmail.com>'
__version__ = '0.1'
__date__ = '24 October 2006'

from HTMLParser import HTMLParser
from os import path
from urllib import urlopen

class iCasualtyParser(HTMLParser):
    """Parse the main HTML file from icasualties.org."""
    line_num = -1
    def __init__(self):
        HTMLParser.__init__(self)
        self.dead = ''
        self.wounded = ''
        sock = urlopen('http://icasualties.org')
        self.feed(sock.read())
        sock.close()
        self.close()
        
    def handle_data(self, data):
        """Extract the number of dead and wounded."""
        if 'US Casualties By Calendar' in data:
            self.line_num = self.getpos()[0] + 17
        elif self.getpos()[0] == self.line_num:
            if self.getpos()[1] == 34:
                self.dead = data
            if self.getpos()[1] == 61:
                self.wounded = data
#            print data
#            print self.getpos()[1]
                
    def tag(self):
        """Return a tagline listing the number of dead and wounded."""
        return '\n%s Dead, %s Wounded' % (self.dead, self.wounded)
                 

if __name__ == '__main__':
    dest = '/home/jdfrechette/briefcase'
    base_sig = ['Jed Frechette\n',
                'http://jdfrechette.alturl.com\n']
    parser = iCasualtyParser()
    
    sig = open(path.join(dest, '.signature'), 'w')
    sig.writelines(base_sig)
    sig.write(parser.tag())
    sig.close()
