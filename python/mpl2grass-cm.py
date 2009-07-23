#!/usr/bin/env python
#------------------------------------------------------------------------------
#
# Copyright (C) 2009 University of New Mexico Board of Regents
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#------------------------------------------------------------------------------

"""Convert a Matplotlib colormap to a GRASS color map"""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "Jun 25, 2009"

def convert(m_map):
    red = m_map['red']
    green = m_map['green']
    blue = m_map['blue']
    g_map = []
    for nn, r in enumerate(red):
        g_map.append("%.1f%% %.0f %.0f %.0f\n" % (r[0]*100,
                                   r[1]*255,
                                   green[nn][1]*255,
                                   blue[nn][1]*255))
    return g_map

if __name__ == "__main__":
    from matplotlib._cm import _gist_earth_data
    g_handle = open('/tmp/gist_earth.colors', 'wb')
    g_handle.writelines(convert(_gist_earth_data))
    g_handle.close