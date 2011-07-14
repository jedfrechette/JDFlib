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
    ogr.UseExceptions()
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
                                             'LINE_FILE',
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
    parser.add_option('--label', dest='label',
                      default=False, action='store_true',
                      help="Label ROIs in GMT output. "\
                           'The default is: "%default"',
                      metavar='LABEL')
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

def get_roi_datasource(data_source, opts):
    """Return an OGR data source with transect LINESTRING features."""
    drv = ogr.GetDriverByName("ESRI Shapefile")
    if opts.roi_file:
        data_name = '-'.join([path.split(path.splitext(data_source.name)[0])[1],
                             TIMESTAMP])
        out_ds = drv.CreateDataSource('.'.join([data_name, 'shp']))
        out_ds.CopyLayer(data_source[0], data_source.GetName())
    else:
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
                             'roi',
                             TIMESTAMP])
        roi_file = '.'.join([data_name, 'shp'])
        
        if path.isfile(roi_file):
            print "%s already exists, attempting to load ROIs" % roi_file
            out_ds = ogr.Open(roi_file)
        else:
            out_ds = drv.CreateDataSource('.'.join([data_name, 'shp']))
            roi_layer = out_ds.CreateLayer('ROI',
                                           line_layer.GetSpatialRef(),
                                           ogr.wkbPolygon)
            field_defn = ogr.FieldDefn(opts.roi_field, ogr.OFTString)
            field_defn.SetWidth(32)
            roi_layer.CreateField(field_defn)
            feature = ogr.Feature(roi_layer.GetLayerDefn())
            feature.SetField(opts.roi_field, data_name)
            feature.SetGeometry(roi_geom)
            roi_layer.CreateFeature(feature)
    return out_ds

def get_transect_datasource(data_source):
    """Return an OGR data source with polygon ROI features."""
    drv = ogr.GetDriverByName("ESRI Shapefile")
    data_name = '-'.join([path.split(path.splitext(data_source.name)[0])[1],
                         TIMESTAMP])
    
    out_ds = drv.CreateDataSource('.'.join([data_name, 'shp']))
    out_ds.CopyLayer(data_source[0], data_source.GetName())
    
    return out_ds

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

def get_feature_id(feature, field=None):
    if field:
        try:
            feature_id = feature.GetField(field)
        except ValueError:
            feature_id = 'FID%i' % feature.GetFID()
    else:
        feature_id = 'FID%i' % feature.GetFID()
    return str(feature_id)

def write_GMT_roses(line_orientations, roi, base_dir, script, region_id, label=True):
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
    script.write("    -Xa$xx'i' -Ya$yy'i' -F -O -K >> $PS\n")
    if label == True:
        script.write("lat=`awk '{print $1}' %s`\n" % ll_file)
        script.write("long=`awk '{print $2}' %s`\n" % ll_file)
        script.write("cat << EOF | GMT pstext -R$ROI -J$PROJ -D.15i/0 -O -K >> $PS\n")
        script.write("$lat $long 10 0 0 TL %s\n" % region_id)
        script.write("EOF\n")
    script.write("\n")
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
    """Return list of lines that are normal to azimuth, within plus or minus tol.
    
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
    
    roi_header = ['#ROIs intersecting less than %i lines were ignored.\n' % opts.min_lines]
    if opts.roi_file:
        roi_filebase = path.splitext(path.split(opts.roi_file)[1])[0]
        roi_src = ogr.Open(opts.roi_file)
        if not roi_src:
            raise IOError, 'Unable to open %s, not a valid OGR Data Source' % opts.roi_file
        roi_ds = get_roi_datasource(roi_src, opts)
        roi_header = roi_header + ['#The input ROI file was:\n',
                                   '#%s\n' % path.abspath(opts.roi_file)]
        
        roi_header = roi_header + ['#The ROI id field was:\n',
                                   '#%s\n' % opts.roi_field]
        gmt_base = ('-').join([roi_filebase, gmt_base])
        rose_base = '-'.join([roi_filebase, rose_base])
    
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
                  '#%s\n' % NOW.isoformat(),
                  '#The input line file was:\n',
                  '#%s\n' % path.abspath(line_filename)]
        if opts.split:
            poly_header = ['#Polylines were split into segments at nodes before processing.\n']
        else:
            poly_header = ['#Polyline orientations were approximated as \n',
                           '#the vector between the start & end points and \n'
                           '#lengths are for the entire multi-segment line.\n']
        
        # Process transect files.  
            trans_ds = ogr.Open(opts.transect_file)
            if not trans_ds:
                raise IOError, 'Unable to open %s, not a valid OGR Data Source' % opts.transect_file
            trans_ds= get_transect_datasource(trans_ds)
                        
            trans_map = {"trans_len": ["trans_len",
                                       ogr.FieldDefn("trans_len", ogr.OFTReal),
                                       lambda st, ln: st.length],
                         "trans_az": ["trans_az",
                                       ogr.FieldDefn("trans_az", ogr.OFTReal),
                                       lambda st, ln: end2end_orientation(asarray(st.coords))],
                         "icpt_count": ["icpt_count",
                                        ogr.FieldDefn("icpt_count", ogr.OFTInteger),
                                        lambda st, ln: len(ln)],
                         "icpt_rate": ["icpt_rate",
                                       ogr.FieldDefn("icpt_rate", ogr.OFTReal),
                                       lambda st, ln: len(ln)/st.length]}
            tol_keys = []
            for tol in opts.set_tolerance:
                tol_keys.append('%gt_cnt' % tol)
                trans_map[tol_keys[-1]] = [tol_keys[-1],
                                           ogr.FieldDefn(tol_keys[-1],
                                                         ogr.OFTInteger)]
                tol_keys.append('%gt_smin' % tol)
                trans_map[tol_keys[-1]] = [tol_keys[-1],
                                           ogr.FieldDefn(tol_keys[-1],
                                                         ogr.OFTReal)]
                tol_keys.append('%gt_smean' % tol)
                trans_map[tol_keys[-1]] = [tol_keys[-1],
                                           ogr.FieldDefn(tol_keys[-1],
                                                         ogr.OFTReal)]
                tol_keys.append('%gt_smax' % tol)
                trans_map[tol_keys[-1]] = [tol_keys[-1],
                                           ogr.FieldDefn(tol_keys[-1],
                                                         ogr.OFTReal)]
            for layer in trans_ds:
                for trans_field in trans_map.values():
                    layer.CreateField(trans_field[1])
                    f_idx = layer.GetLayerDefn().GetFieldCount() - 1
                    trans_field[0] = layer.GetLayerDefn().GetFieldDefn(f_idx).GetName()
                for trans in layer:
                    if trans.geometry() and trans.geometry().GetGeometryName() == 'LINESTRING':                        
                        strans = shapely.wkb.loads(trans.GetGeometryRef().ExportToWkb())
                        if len(strans.coords) != 2:
                            print "WARNING: FID %s has more than 1 segment " \
                            "and was skipped." % trans.GetFID()
                            continue
                        lines = get_intersecting_lines(all_lines, trans)
                        
                        # Update output data source.
                        for key, trans_field in trans_map.iteritems():
                            if key not in tol_keys:
                                trans.SetField(trans_field[0],
                                               trans_field[2](strans,
                                                              lines))
                        for tol in opts.set_tolerance:
                            n_lines = get_normal_lines(lines,
                                                       trans.GetField(trans_map['trans_az'][0]),
                                                       tol)
                            trans.SetField(trans_map['%gt_cnt' % tol][0],
                                           len(n_lines))
                            if len(n_lines) > 1:
                                spacing = transect_intercept_spacing(n_lines, trans)
                                trans.SetField(trans_map['%gt_smin' % tol][0], spacing.min())
                                trans.SetField(trans_map['%gt_smean' % tol][0], spacing.mean())
                                trans.SetField(trans_map['%gt_smax' % tol][0], spacing.max())
                                
                    elif trans.geometry() and trans.geometry().GetGeometryName() == 'MULTILINESTRING':
                        print "WARNING: MULTILINESTRINGs aren't supported yet, " \
                          "FID number %s was skipped." % trans.GetFID()
                    layer.SetFeature(trans)
                layer.ResetReading()

        # Process ROIs
        gmt_dir = ('-').join([line_filebase, gmt_base])
        rose_name = '-'.join([line_filebase, rose_base])
        if not path.isdir(gmt_dir):
            mkdir(gmt_dir)
        rose_sh = open(path.join(gmt_dir, rose_name), 'wb') 
        if not opts.roi_file:
            roi_ds = get_roi_datasource(line_src, opts)
        rose_sh.writelines(header + roi_header +poly_header)

        try:
            roi_map = {"line_count": ["line_count",
                                      ogr.FieldDefn("line_count", ogr.OFTInteger),
                                      len],
                       "len_min": ["len_min",
                                   ogr.FieldDefn("len_min", ogr.OFTReal),
                                   min],
                       "len_md_int": ["len_md_int",
                                      ogr.FieldDefn("len_md_int", ogr.OFTInteger),
                                      lambda x: int(mode(around(x))[0][0])],
                       "len_median": ["len_median",
                                      ogr.FieldDefn("len_median", ogr.OFTReal),
                                      median],
                       "len_mean": ["len_mean",
                                    ogr.FieldDefn("len_mean", ogr.OFTReal),
                                    mean],
                       "len_max": ["len_max",
                                   ogr.FieldDefn("len_max", ogr.OFTReal),
                                   max]}
            for layer in roi_ds:
                for roi_field in roi_map.values():
                    layer.CreateField(roi_field[1])
                    f_idx = layer.GetLayerDefn().GetFieldCount() - 1
                    roi_field[0] = layer.GetLayerDefn().GetFieldDefn(f_idx).GetName()
                for roi in layer:
                    if roi.geometry() and roi.geometry().GetGeometryName() == 'POLYGON':     
                        # Calculate statistics for lines intersecting ROI
                        slines = [shapely.wkb.loads(l.GetGeometryRef().ExportToWkb()) for l in get_intersecting_lines(all_lines, roi)]
                        n_lines = len(slines)
                        line_lengths = asarray([s.length for s in slines])
                        line_orientations = asarray([end2end_orientation(asarray(s)) for s in slines])
                        
                        # Update output data source.
                        for roi_field in roi_map.values():
                            roi.SetField(roi_field[0], roi_field[2](line_lengths))
                        
                        # Write output data.
                        if n_lines >= opts.min_lines:
                            write_GMT_roses(line_orientations,
                                            roi,
                                            gmt_dir,
                                            rose_sh,
                                            get_feature_id(roi, opts.roi_field),
                                            opts.label)
                    layer.SetFeature(roi)
                layer.ResetReading()
        except:
            raise
        finally:
            rose_sh.close()
        print "Finished processing: %s" % line_filename
    
if __name__ == '__main__':
    NOW = datetime.now()
    TIMESTAMP = NOW.strftime('%Y%m%d%H%m%S')
    main()
