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

"""Calculate statistics for lines in GIS coverages. 

One or more shapefiles[1]_ containining polyline features to be analyze should
be provided as arguments. An additional shapefile containing Region of Interest
(ROI) polygons can also be provided. If ROIs are provided separate statistics
will be calculated for each group of lines that intersect the ROI, if not
statistics will be calculated for all lines in the input file. An additional
shapefile with transect lines for sampling line spacing can also be provided.

.. [1] It should be possible to use any format recognized by the OGR library
   as the tile index but only shapefiles have been tested."""

__author__ = "Jed Frechette <jed@lidarguys.com>"
__date__ = "May 19, 2011"
__version__ = "0.1"

# Standard library imports
from datetime import datetime
from glob import glob
from optparse import OptionParser
from os import mkdir, name, path
from sys import exit
import csv

# Numpy imports
from numpy import allclose, append, arctan, around, asarray, mean, median, \
                  ones, rad2deg, savetxt

# Scipy imports
from scipy.stats import mode

# OSGEO imports
try:
    from osgeo import ogr
except ImportError:
    raise ImportError, "The OGR Simple Feature Library "\
                       "(http://www.gdal.org/ogr/) "\
                       "is required but could not be found"
                       
# Shapely imports
try:
    from shapely.geometry import asMultiPoint, LineString
    import shapely
    import shapely.wkb
except ImportError:
    raise ImportError, "The Shapely package "\
                       "(http://pypi.python.org/pypi/Shapely) "\
                       "is required but could not be found"

def parse_cmd():
    """Parse command line options and arguments."""
    parser = OptionParser(usage='\n\n'.join(('%prog [options] '\
                                             'ROI_FILE LINE_FILE',
                                              __doc__)),
                          version=__version__)
    parser.add_option('-r', '--roi_file', dest='roi_file',
                      default=None,
                      help='File containing polygon regions of interest. '\
                           'The default is: "%default"',
                      metavar='ROI_FILE')
    parser.add_option('--roi_field', dest='roi_field',
                      default='id',
                      help="Field containing each ROI polygon's name. "\
                           'The default is: "%default"',
                      metavar='ROI_FIELD')
    parser.add_option('-t', '--transect_file', dest='transect_file',
                      default=None,
                      help='File containing transect sampling lines. '\
                           'The default is: "%default"',
                      metavar='TRANSECT_FILE')
    parser.add_option('--transect_field', dest='transect_field',
                      default='id',
                      help="Field containing each transect line's name. "\
                           'The default is: "%default"',
                      metavar='TRANSECT_FIELD')
    parser.add_option('-l', '--set_tolerance', dest='set_tolerance',
                      default='5,10,15,20',
                      help="List of azimuth tolerances (in degrees) within "\
                           "which lines will be considered part of the same set. "\
                           'The default is: "%default"',
                      metavar='SET_TOLERANCE')
    parser.add_option('-f', '--fill_value', dest='fill_value',
                      default=-9999, type='int',
                      help='Fill value for table cells with no data. '\
                           'The default is: "%default"',
                      metavar='FILL_VALUE')
    parser.add_option('-m', '--minimum_lines', dest='min_lines',
                      default=5, type='int',
                      help='Skip ROIs intersecting less than this minimum number of lines. '\
                           'The default is: "%default"',
                      metavar='MININIMUM_LINES')
    parser.add_option('-s', '--split', dest='split',
                      default=False, action='store_true',
                      help='Split polylines into segments at nodes before processing. '\
                           'The default is: "%default"',
                      metavar='SPLIT')
    (opts, args) = parser.parse_args()
    opts.set_tolerance = [float(v) for v in opts.set_tolerance.split(',')]
    
    if name == 'nt':
        args = glob(args[0])
    
    if len(args) < 1:
        parser.print_help()
        exit()
    
    return (opts, args)
    
def get_rois(data_source, opts):
    """Extract a list of ROI polygon features from an OGR data source."""
    if not opts.roi_file:
        # Extract envelope from data_source
        corner_pts = []
        for line_layer in data_source:
            extents = line_layer.GetExtent()
            corner_pts.append((extents[0], extents[2]))
            corner_pts.append((extents[1], extents[3]))
        pts = asMultiPoint(corner_pts)
        roi_geom = ogr.CreateGeometryFromWkb(pts.envelope.wkb,
                                             line_layer.GetSpatialRef())
        
        data_name = '-'.join([path.split(path.splitext(data_source.name)[0])[1],
                             'roi'])
        roi_file = '.'.join([data_name, 'shp'])
        
        if path.isfile(roi_file):
            print "%s already exists, attempting to load ROIs" % roi_file
            data_source = ogr.Open(roi_file)
        else:
            drv = ogr.GetDriverByName('ESRI Shapefile')
            roi_src = drv.CreateDataSource(roi_file)
            roi_layer = roi_src.CreateLayer('ROI',
                                            line_layer.GetSpatialRef(),
                                            ogr.wkbPolygon)
            field_defn = ogr.FieldDefn(opts.roi_field, ogr.OFTString)
            field_defn.SetWidth(32)
            roi_layer.CreateField(field_defn)
            feature = ogr.Feature(roi_layer.GetLayerDefn())
            feature.SetField(opts.roi_field, data_name)
            feature.SetGeometry(roi_geom)
            roi_layer.CreateFeature(feature)
            return [feature]
    
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

def get_intersecting_lines(test_lines, target):
    """Extract a list of line features that intersect a target feature."""
    line_list = []
    for line in test_lines:
        if line.geometry().GetGeometryName() in ('MULTILINESTRING',
                                                 'LINESTRING'):    
            if line.geometry().Intersect(target.geometry()):
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

def get_row(line_lengths, line_orientations, region_id):
    return {'id': region_id,
            'n': len(line_lengths),
            'length_min': min(line_lengths),
            'length_mode_int': int(mode(around(line_lengths))[0][0]),
            'length_median': median(line_lengths),
            'length_mean': mean(line_lengths),
            'length_max': max(line_lengths)}

def get_feature_id(feature, field=None):
    if field:
        try:
            feature_id = feature.GetField(field)
        except ValueError:
            feature_id = 'FID%i' % feature.GetFID()
    else:
        feature_id = 'FID%i' % feature.GetFID()
    return feature_id

def write_GMT_roses(line_orientations, roi, base_dir, script, region_id):
    """Write a GMT script and supporting files for generating rose plots.
    
    Note that this script is not complete and is intended for inclusion into
    another handwritten GMT script via 'source'. This script will place rose
    diagrams at specific coordinates on a basemap."""
    
    centroid = roi.geometry().Centroid()
    
    s_srs = roi.geometry().GetSpatialReference()
    t_srs = ogr.osr.SpatialReference()
    t_srs.ImportFromEPSG(4326)
    s2ll = ogr.osr.CoordinateTransformation(s_srs, t_srs)

    centroid_ll = s2ll.TransformPoint(centroid.GetX(), centroid.GetY())[:2]
    centroid_ll = asarray(centroid_ll).reshape([1,2])
    
    nn = line_orientations.size
    
    az_file = '.'.join([region_id, 'az'])
    ll_file = '.'.join([region_id, 'll'])
    xy_file = '.'.join([region_id, 'xy'])
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
    
def two_iter(src_list):
    start = 0
    end = 2
    while end <= len(src_list):
        yield src_list[start:end]
        start += 1
        end += 1

def split_lines(line_list):
    """Split polylines into individual segments."""
    segments = []
    for line in line_list:
        sline = shapely.wkb.loads(line.GetGeometryRef().ExportToWkb())
        for coords in two_iter(asarray(sline)):
            seg = line.Clone()
            ls = LineString(coords)
            seg.SetGeometry(ogr.CreateGeometryFromWkb(ls.wkb))
            segments.append(seg)
    return segments

def get_normal_lines(lines, azimuth, tol):
    """Return list of lines that are normal to azimuth, within tolerance.
    
    All angles are in degrees."""
    normal = 2*(azimuth+90)
    if normal >= 360:
        normal -= 360
    normal = normal/2
        
    n_lines = []
    for line in lines:
        sline = shapely.wkb.loads(line.GetGeometryRef().ExportToWkb())
        lo = 2* asarray(end2end_orientation(asarray(sline)))
        if lo >= 360:
            lo -= 360
        lo = lo/2
        if allclose(normal, lo, atol=tol):
            n_lines.append(line)
    return n_lines

def transect_intercept_spacing(lines, transect):
    """Return an array listing the spacing between lines intercepting a transect."""
    spacing = []
    st = shapely.wkb.loads(transect.GetGeometryRef().ExportToWkb())
    origin = shapely.geometry.Point(st.coords[0])
    for ln in lines:
        sln = shapely.wkb.loads(ln.GetGeometryRef().ExportToWkb())
        spacing.append(origin.distance(st.intersection(sln)))
    spacing.sort()
    spacing = [v - spacing[n-1] for n, v in enumerate(spacing)][1:]
    return asarray(spacing)

def main():
    opts, args = parse_cmd()
    
    gmt_base = 'gmt'
    rose_base = 'rose.sh'
    line_stats_base = 'rois.csv'
    trans_stats_base = 'transects.csv'
    
    roi_header = ['#ROIs intersecting less than %i lines were ignored.\n' % opts.min_lines]
    if opts.roi_file:
        roi_filebase = path.splitext(path.split(opts.roi_file)[1])[0]
        roi_src = ogr.Open(opts.roi_file)
        if not roi_src:
            raise IOError, 'Unable to open %s, not a valid OGR Data Source' % opts.roi_file
        roi_list = get_rois(roi_src, opts)
        roi_header = ['#The input ROI file was:\n',
                      '#%s\n' % path.abspath(opts.roi_file)] + roi_header
        gmt_base = ('-').join([roi_filebase, gmt_base])
        rose_base = '-'.join([roi_filebase, rose_base])
        line_stats_base = '-'.join([roi_filebase, line_stats_base])
    
    for line_filename in args:
        # Load line features.
        line_src = ogr.Open(line_filename)
        line_filebase = path.splitext(path.split(line_filename)[1])[0]
        if not line_src:
            raise IOError, 'Unable to open %s, not a valid OGR Data Source' % line_filename
        all_lines = get_lines(line_src)
        if opts.split:
            all_lines = split_lines(all_lines)
        # Define basic output file headers.
        header = ['#This file was generated at:\n',
                  '#%s\n' % datetime.today().isoformat(),
                  '#The input line file was:\n',
                  '#%s\n' % path.abspath(line_filename)]
        if opts.split:
            poly_header = ['#Polylines were split into segments at nodes before processing.\n']
        else:
            poly_header = ['#Polyline orientations were approximated as:\n',
                           '#The vector between the start & end points.\n']
        
        # Process transect files.  
        if opts.transect_file:
            trans_stats_name = '-'.join([line_filebase, trans_stats_base])
            trans_header = ['#The input transects file was:\n',
                            '#%s\n' % path.abspath(opts.transect_file),
                            '#Lines normal to the transect within plus/minus\n',
                            '#the following degrees are part of a set:\n',
                            '#%s\n' % opts.set_tolerance,
                            '#Fill value for output table cells with no data:\n',
                            '#%s\n' % opts.fill_value]
            trans_stats = open(trans_stats_name, 'wb')
            trans_stats.writelines([r[:-1]+'\r\n' for r in header + trans_header + poly_header])
            trans_stats_writer = csv.writer(trans_stats)
            trans_stats_cols = ['transect_id',
                                'transect_length',
                                'transect_azimuth',
                                'intercept_count',
                                'intercept_rate']
            for tol in opts.set_tolerance:
                trans_stats_cols.append('normal_+/-%s_count' % tol)
                trans_stats_cols.append('normal_+/-%s_spacing_min' % tol)
                trans_stats_cols.append('normal_+/-%s_spacing_mean' % tol)
                trans_stats_cols.append('normal_+/-%s_spacing_max' % tol)
            trans_stats_writer.writerow(trans_stats_cols)
            
            trans_src = ogr.Open(opts.transect_file)
            if not trans_src:
                raise IOError, 'Unable to open %s, not a valid OGR Data Source' % opts.transect_file
            all_trans = get_lines(trans_src)
            for trans in all_trans:
                trans_row = [get_feature_id(trans, opts.transect_field)]
                strans = shapely.wkb.loads(trans.GetGeometryRef().ExportToWkb())
                
                if len(strans.coords) != 2:
                    print "WARNING: %s has more than 1 segment and was skipped." % trans_row[0]
                    continue
                
                trans_row.append(strans.length)
                trans_orientation = end2end_orientation(asarray(strans.coords))
                trans_row.append(trans_orientation)
                
                lines = get_intersecting_lines(all_lines, trans)
                trans_row.append(len(lines))
                trans_row.append(len(lines)/strans.length)
                for tol in opts.set_tolerance:
                    n_lines = get_normal_lines(lines, trans_orientation, tol)
                    trans_row.append(len(n_lines))
                    if len(n_lines) > 1:
                        spacing = transect_intercept_spacing(n_lines, trans)
                        trans_row.append(spacing.min())
                        trans_row.append(spacing.mean())
                        trans_row.append(spacing.max())
                    else:
                        for nn in xrange(3):
                            trans_row.append(opts.fill_value)
                
                trans_stats_writer.writerow(trans_row)
        
        # Process ROIs
        gmt_dir = ('-').join([line_filebase, gmt_base])
        rose_name = '-'.join([line_filebase, rose_base])
        line_stats_name = '-'.join([line_filebase, line_stats_base])
        if not path.isdir(gmt_dir):
            mkdir(gmt_dir)
        rose_sh = open(path.join(gmt_dir, rose_name), 'wb')
        line_stats = open(line_stats_name, 'wb')    
        if not opts.roi_file:
            roi_list = get_rois(line_src, opts)
        rose_sh.writelines(header + roi_header +poly_header)
        line_stats.writelines([r[:-1]+'\r\n' for r in header + roi_header + poly_header])
            
        line_stats_writer = csv.writer(line_stats)
        line_stats_cols = ['id',
                           'n',
                           'length_min',
                           'length_mode_int',
                           'length_median',
                           'length_mean',
                           'length_max']
        line_stats_writer.writerow(line_stats_cols)
        
        try:
            for roi in roi_list:
                # Calculate statistics for lines intersecting ROI
                slines = [shapely.wkb.loads(l.GetGeometryRef().ExportToWkb()) for l in get_intersecting_lines(all_lines, roi)]
                n_lines = len(slines)
                line_lengths = asarray([s.length for s in slines])
                line_orientations = asarray([end2end_orientation(asarray(s)) for s in slines])
                
                # Write output data.
                if n_lines >= opts.min_lines:
                    row = get_row(line_lengths,
                                  line_orientations,
                                  get_feature_id(roi, opts.roi_field))
                    values = [row[c] for c in line_stats_cols]
                    line_stats_writer.writerow(values)
                    write_GMT_roses(line_orientations,
                                    roi,
                                    gmt_dir,
                                    rose_sh,
                                    get_feature_id(roi, opts.roi_field))
        except:
            raise
        finally:
            rose_sh.close()
            line_stats.close()
            try:
                trans_stats.close()
            except:
                pass
        print "Finished processing: %s" % line_filename
    
if __name__ == '__main__':
    main()
