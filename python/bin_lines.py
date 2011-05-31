#!/usr/bin/env python
#------------------------------------------------------------------------------
#
# Copyright (C) 2011 Jed Frechette
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
#------------------------------------------------------------------------------

"""Calculate statistics for lines within geographic areas defined by polygons
in another geospatial data file. 

The first nonoption argument to the script must be a shapefile[1]_ containing
polygons corresponding to the Regions of Interest (ROI) for analysis.
Next one or more shapefiles containing polyline features to be analyzed should
be provided

.. [1] It should be possible to use any format recognized by the OGR library
   as the tile index but only shapefiles have been tested to date."""

__author__ = "Jed Frechette <jed@lidarguys.com>"
__date__ = "May 19, 2011"
__version__ = "0.1"

# Standard library imports
from datetime import datetime
from glob import glob
from optparse import OptionParser
from os import mkdir, name, path

# Numpy imports
from numpy import arctan, append, asarray, ones, rad2deg, savetxt

# OSGEO imports
try:
    from osgeo import ogr
except ImportError:
    raise ImportError, "The OGR Simple Feature Library "\
                       "(http://www.gdal.org/ogr/) "\
                       "is required but could not be found"
                       
# Shapely imports
try:
    import shapely
    import shapely.wkb
except ImportError:
    raise ImportError, "The Shapely package "\
                       "(http://pypi.python.org/pypi/Shapely) "\
                       "is required but could not be found"


def get_rois(data_source):
    """Extract a list of ROI polygon features from an OGR data source."""
    roi_list = []
    for layer in data_source:
        for feature in layer:
            if feature.geometry():
                if feature.geometry().GetGeometryName() == 'POLYGON':
                    roi_list.append(feature)
        layer.ResetReading()
    if len(roi_list) == 0:
        raise IOError('No ROI polygons found in ROI data source.')
    return roi_list

def get_lines(data_source):
    """Extract a list of line features from an OGR data source."""
    line_list = []
    for layer in data_source:
        for feature in layer:
            if feature.geometry():
                if feature.geometry().GetGeometryName() == 'LINESTRING':    
                    line_list.append(feature)
                elif feature.geometry().GetGeometryName() == 'MULTILINESTRING':
                    print "WARNING: MULTILINESTRINGs aren't supported yet, " \
                          "FID number %s was skipped." % feature.GetFID()
                    #TODO: Split MULTILINESTRING into LINESTRINGs.
        layer.ResetReading()
    if len(line_list) == 0:
        raise IOError('No lines found in line data source.')
    return line_list

def get_intersecting_lines(all_lines, roi):
    """Extract a list of line features that intersect an ROI."""
    line_list = []
    for line in all_lines:
        if line.geometry().GetGeometryName() in ('MULTILINESTRING',
                                                 'LINESTRING'):    
            if line.geometry().Intersect(roi.geometry()):
                line_list.append(line)
    return line_list

def end2end_orientation(vert_array):
    """Return the orientation (0-180 degrees) of an input polyline.
    
    The orientation is measured between the first and last vertices."""
    origin = vert_array[0, :]
    end = vert_array[-1, :]
    e2e = end - origin
    o = rad2deg(arctan(e2e[0]/e2e[1]))
    if o >= 0:
        return o
    else:
        return 180 + o

def write_GMT_roses(line_orientations, roi, base_dir, script, opts):
    try:
        file_base = roi.GetField(opts.field)
    except ValueError:
        file_base = 'FID%i' % roi.GetFID()
    
    centroid = roi.geometry().Centroid()
    
    s_srs = roi.geometry().GetSpatialReference()
    t_srs = ogr.osr.SpatialReference()
    t_srs.ImportFromEPSG(4326)
    s2ll = ogr.osr.CoordinateTransformation(s_srs, t_srs)

    centroid_ll = s2ll.TransformPoint(centroid.GetX(), centroid.GetY())[:2]
    centroid_ll = asarray(centroid_ll).reshape([1,2])
    
    nn = line_orientations.size
    
    az_file = '.'.join([file_base, 'az'])
    ll_file = '.'.join([file_base, 'll'])
    xy_file = '.'.join([file_base, 'xy'])
    savetxt(path.join(base_dir, az_file),
            zip(append(line_orientations,
                       180 + line_orientations),
                append(ones(nn)/nn,
                       ones(nn)/nn)),
            fmt='%f')
    savetxt(path.join(base_dir, ll_file), centroid_ll, fmt='%f')
    
    script.write('GMT mapproject %s -R$ROI -J$PROJ -Di >%s\n' % (ll_file,
                                                                    xy_file))
    script.write("xx=`awk '{print $1-.15}' %s`\n" % xy_file)
    script.write("yy=`awk '{print $2-.15}' %s`\n" % xy_file)
    script.write('GMT psrose %s -R0/.25/0/360 -B0.1g0.1/30g30 -: \\\n' % az_file)
    script.write('    -A10 -S.15i -Gblack -L -T -F \\\n')
    script.write("    -Xa$xx'i' -Ya$yy'i' -F -O -K >> $PS\n\n")

def main():
    parser = OptionParser(usage='\n\n'.join(('%prog [options] '\
                                             'ROI_FILE LINE_FILE',
                                              __doc__)),
                          version=__version__)
    parser.add_option('-f', '--name_field', dest='field',
                      default='roi_index',
                      help='Field containing each polygons name. '\
                           'The default is: "%default"',
                      metavar='NAME_FIELD')
    parser.add_option('-m', '--minimum_lines', dest='min_lines',
                      default=5, type='int',
                      help='Skip ROIs intersecting less than the minimum number of lines. '\
                           'The default is: "%default"',
                      metavar='MININIMUM_LINES')
    (opts, args) = parser.parse_args()
    
    if name == 'nt':
        args = glob(args[0])
    
    if len(args) < 2:
        parser.print_help()
        return
    
    roi_filename = args[0]
    roi_filebase = path.splitext(path.split(roi_filename)[1])[0]
    
    roi_src = ogr.Open(roi_filename)
    if not roi_src:
        raise IOError, 'Unable to open %s. The first argument must be a valid'\
                       'OGR Data Source' % roi_filename
    roi_list = get_rois(roi_src)
    
    line_filenames = args[1:]
    for line_filename in line_filenames:
        header = ['#This file was generated at:\n',
                  '#%s\n' % datetime.today().isoformat(),
                  '#The input line file was:\n',
                  '#%s\n' % path.abspath(line_filename),
                  '#The input ROI file was:\n',
                  '#%s\n' % path.abspath(roi_filename),
                  '#ROIs intersecting less than %i lines were ignored.\n' % opts.min_lines]
        
        line_src = ogr.Open(line_filename)
        line_filebase = path.splitext(path.split(line_filename)[1])[0]
        if not line_src:
            raise IOError, 'Unable to open %s. The 2nd and later arguments' \
                           'must be valid OGR Data Sources' % line_filename
        all_lines = get_lines(line_src)

        gmt_dir = ('-').join([roi_filebase, line_filebase, 'gmt'])
        if not path.isdir(gmt_dir):
            mkdir(gmt_dir)
        rose_sh = open(path.join(gmt_dir,
                                 '-'.join([roi_filebase,
                                           line_filebase,
                                           'rose.sh'])), 'wb')
        rose_sh.writelines(header)
        try:
            for roi in roi_list:
                line_list = get_intersecting_lines(all_lines, roi)
                slines = [shapely.wkb.loads(l.GetGeometryRef().ExportToWkb()) for l in line_list]
                n_lines = len(slines)
                line_lengths = asarray([s.length for s in slines])
                line_orientations = asarray([end2end_orientation(asarray(s)) for s in slines])
                
                if n_lines >= opts.min_lines:
                    write_GMT_roses(line_orientations,
                                    roi,
                                    gmt_dir,
                                    rose_sh,
                                    opts)
        except:
            raise
        finally:
            rose_sh.close()
        print "Finished processing: %s" % line_filename
    
if __name__ == '__main__':
    main()
