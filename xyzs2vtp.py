#!/usr/bin/env python
"""Convert a csv file containing particles to a VTK XML PolyData file.

The format of the comma separated file is: x, y, z, scalar. Additional
columns will be ignored as will missing scalars.

The results are saved to an output file with the same base name as the input
file and the extension vtp."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "27 September 2007"
__version__ = "0.1"

from glob import glob
from optparse import OptionParser
from os import name, path
from vtk import vtkParticleReader, vtkXMLPolyDataWriter

if __name__ == '__main__':
    parser = OptionParser(usage='%prog INPUT_FILES',
                          description=' '.join(__doc__.split()),
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])

    for input_file in args:
        output_file = '.'.join([path.splitext(path.split(input_file)[-1])[0],
                                'vtp'])
        reader = vtkParticleReader()
        reader.SetFileName(input_file)
        
        writer = vtkXMLPolyDataWriter()
        writer.SetFileName(output_file)
        writer.SetInputConnection(reader.GetOutputPort())
        writer.Write()
        print "Saved file: %s" % output_file