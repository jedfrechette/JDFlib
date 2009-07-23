#!/usr/bin/env python

#------------------------------------------------------------------------------
#
# Copyright (C) 2007 Jed Frechette <jedfrechette@gmail.com>
#
# This software is provided without warranty under the terms of the MIT
# license available online at http://opensource.org/licenses/mit-license.php
# and may be redistributed only under the conditions described in the
# aforementioned license.
#
#------------------------------------------------------------------------------

"""Change font-size units in an SVG file for pixels to points.

WARNING: This script has not been thoroughly tested and will overwrite your
data in place. I highly recommend that you make backups of any files before
processing them. 

This script does not actually convert the font-sizes it simply changes the
unit suffix from px to pt. When the file is then loaded into Inkscape all
font-sizes will be converted back to pixels and scaled assuming a 90 dpi
pixel density. For example 10 pt text will be converted to 12.5 px text.
"""

__author__ = "Jed Frechette <jedfrechette@gmail.com>"
__date__ = "14 March 2007"
__version__ = 0.1
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"


from glob import glob
from optparse import OptionParser
from os import name
from xml.dom import minidom, Node
import codecs

def walk(parent):
    """Walk the xml tree and replace all font-size units of px with pt."""
    for node in parent.childNodes:
        if node.nodeType == Node.ELEMENT_NODE:
            if node.tagName == 'text':
                value_list = node.attributes['style'].value.split(';')
                for idx, value in enumerate(value_list):
                    if value[:9] == 'font-size':
                        value_list[idx] = value.replace('px', 'pt')
                node.attributes['style'].value = ';'.join(value_list)
            walk(node)
       
def get_file_list():
    """Return a list of files specified on the command line."""
    parser = OptionParser(usage='%prog INPUT_FILES', 
                          description=' '.join(__doc__.split()), 
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
    return args

def process_files(file_list):
    """Process each file named in the input list."""
    for file_name in file_list:
        doc = minidom.parse(file_name)
        walk(doc.documentElement)
        
        output_file = codecs.open(file_name, 'w', 'utf-8')
        doc.writexml(output_file)
        output_file.close()

if __name__ == '__main__':
    process_files(get_file_list())
