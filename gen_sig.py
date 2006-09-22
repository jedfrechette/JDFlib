#/usr/bin/env python
"""Generate a .signature file."""

__author__ = 'Jed Frechette <jedfrechette@gmail.com>'
__version__ = '0.1'
__date__ = 'Sep 22, 2006'

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
        
    def handle_data(self, data):
        """Extract the number of dead and wounded"""
        if 'US Casualties By Calendar' in data:
            self.line_num = self.getpos()[0] + 16
        elif self.getpos()[0] == self.line_num:
            if self.getpos()[1] == 145:
                self.dead = data
            if self.getpos()[1] == 233:
                self.wounded = data
 
    
def iraq_casualties():
    """Get the current number of coalition casualties in Iraq and return the
    number of dead and wounded in a string."""
    sock = urlopen('http://icasualties.org')
    html_src = sock.read()
    sock.close()
    parser = iCasualtyParser()
    parser.feed(html_src)
    parser.close()
    return '\n%s Dead, %s Wounded' % (parser.dead, parser.wounded)

if __name__ == '__main__':
    dest = '/home/jdfrechette/briefcase'
    base_sig = ['--\n',
                'Jed Frechette\n',
                'http://jdfrechette.alturl.com\n']
    tag = iraq_casualties()
    
    sig = open(path.join(dest, '.signature'), 'w')
    sig.writelines(base_sig)
    sig.write(tag)
    sig.close()