#!/usr/bin/env python
"""Change font-size units in an SVG file for pixels to points.

WARNING: This script has not been thoroughly tested and will overwrite your
data in place. I highly recommend that you make backups of any files before
processing them. 

This script does not actually convert the font-sizes it simply changes the
unit suffix from px to pt. When the file is then loaded into Inkscape all
font-sizes will be converted back to pixels and scaled assuming a 90 dpi
pixel density. For example 10 pt text will be converted to 12.5 px text.

Copyright (C) 2007 Jed Frechette <jedfrechette@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

__author__ = "Jed Frechette <jedfrechette@gmail.com>"
__date__ = "14 March 2007"
__version__ = 0.1


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
       
if __name__ == '__main__':
    parser = OptionParser(usage='%prog INPUT_FILES', 
                          description=' '.join(__doc__.split()), 
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
        
    for input_name in args:
        doc = minidom.parse(input_name)
        walk(doc.documentElement)
        
        output_file = codecs.open(input_name, 'w', 'utf-8')
        doc.writexml(output_file)
        output_file.close()