#!/usr/bin/env python
"""Convert a csv file containing particles to a VTK XML PolyData file.

The format of the comma separated file is: x, y, z, scalar. Additional
columns will be ignored as will missing scalars.

The results are saved to an output file with the same base name as the input
file and the extension vtp."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "23 January 2008"
__version__ = "0.1"
__license__ = "BSD <http://opensource.org/licenses/bsd-license.php>"

from glob import glob
from optparse import OptionParser
from os import name, path
from vtk import vtkParticleReader, vtkXMLPolyDataWriter

def get_filenames():
    """Return a list of filenames to process."""
    parser = OptionParser(usage='%prog INPUT_FILES',
                          description=' '.join(__doc__.split()),
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
    return args


if __name__ == '__main__':
    for in_filename in get_filenames():
        out_filename = '.'.join([path.splitext(path.split(in_filename)[-1])[0],
                                'vtp'])
        reader = vtkParticleReader()
        reader.SetFileName(in_filename)
        
        writer = vtkXMLPolyDataWriter()
        writer.SetFileName(out_filename)
        writer.SetInputConnection(reader.GetOutputPort())
        writer.Write()
        print "Saved file: %s" % out_filename
