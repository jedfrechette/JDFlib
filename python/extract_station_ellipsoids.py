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

"""Extract 3D connected station ellipsoids from a Columbus report."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "Sep 28, 2009"
__version__ = "0.1"

# Standard library imports.
from os import name, path
import csv

# Numpy imports
from numpy import empty

def main():
    """Return a list of command line arguments."""
    from optparse import OptionParser
    from glob import glob
    
    parser = OptionParser(usage='%prog REPORT',
                          description=' '.join(__doc__.split()),
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
        
    if len(args) < 1:
        parser.print_help()
        return
            
    for file_name in args:
        f_handle = open(file_name)
        output_rows = []
        try:
            ignore = True
            while ignore:
                line = f_handle.readline()
                if line.strip() == 'Connected Station 3D Error Ellipsoids':
                    ignore = False
            for nn in xrange(8):
                f_handle.readline()
            while not ignore:
                in_rows = []
                for nn in xrange(5):
                    in_rows.append(f_handle.readline())
                if in_rows == ['', '', '', '', '']:
                    ignore = True
                else:
                    output_rows.append(in_rows[0].split() + in_rows[1].split()[:3])
        except:
            raise
        finally:
            f_handle.close()
        
        w_handle = open('_'.join([path.splitext(file_name)[0], 'connected.csv']),
                        'wb')
        try:
            writer = csv.writer(w_handle)
            writer.writerows(output_rows)
        except:
            pass
        finally:
            w_handle.close()
        
        data = empty([len(output_rows), 3])
        for n_row, row in enumerate(output_rows):
            data[n_row, 0] = float(row[2])
            data[n_row, 1] = float(row[3])
            data[n_row, 2] = float(row[4])
        print "%0.4f %0.4f %0.4f" % tuple(data.mean(axis=0))
        
if __name__ == "__main__":
    main()
