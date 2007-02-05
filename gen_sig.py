#!/usr/bin/env python
"""Generate a .signature file."""

__author__ = 'Jed Frechette <jedfrechette@gmail.com>'
__version__ = '0.1'
__date__ = '4 February 2007'

from BeautifulSoup import BeautifulSoup
from os import path
from urllib import urlopen              

if __name__ == '__main__':
    dest = '/home/jdfrechette/briefcase'
    base_sig = ['Jed Frechette\n',
                'http://jdfrechette.alturl.com\n\n']

    soup = BeautifulSoup(urlopen('http://icasualties.org'))    
    dead = soup.body('span', id='lblCount')[0].find('font').string
    wounded = soup.body('table', id='dgWnd')[0]
    wounded = wounded.findAll('tr')[5].findAll('td')[-1].find('b').string
    tag = '%s Dead, %s Wounded' % (dead, wounded)
    
    sig = open(path.join(dest, '.signature'), 'w')
    sig.writelines(base_sig)
    sig.write(tag)
    sig.close()
