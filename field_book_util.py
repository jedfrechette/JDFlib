#!/usr/bin/env python
"""Manipulate and simplify SOKKIA text field books."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "6 February 2009"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

# Local imports.
from cogo import AngleDMS, avg_angles, dd2dms

# Standard library imports.
from copy import copy
import datetime
from glob import glob
from optparse import OptionParser
from os import name, path

# Numpy imports.
from numpy import asarray, ma, mean, ptp

# Enthought library imports.
from enthought.traits.api import Date, Dict, Bool, Enum, File, Float, HasTraits, \
                                 Int, List, ListStr, String, Time

class SOKKIARecord(HasTraits):
    """Single or multiline record in a SOKKIA text fieldbook."""
    record_type = Enum('NM', 'Fbk Settings', 'SCALE', 'INSTR', 'RED',
                       'BKB', 'TARGET', 'STN', 'OBS', 'POS')
    point_id = Int
    dc = Enum(None, 'NM', 'KI', 'TP', 'F1', 'F2')
    north_horizontal = AngleDMS
    east_vertical = AngleDMS
    elevation_distance = Float
    code = String
    
class FieldbookSettings(SOKKIARecord):
    """Fieldbook settings"""
    atmospheric_correction = Bool
    sea_level_correction = Bool
    curvature_and_refraction_correction = Bool
    include_elevation = Bool
    refraction_constant = Float
    
class SOKKIABook(HasTraits):
    """SOKKIA text fieldbook."""
    project = String
    sdr_file = File
    print_date = Date
    print_time = Time
    distance_unit = String('Meters')
    angle_unit = String('Degrees [dd-mm-ss.ss]')
    point_count = Int
    record_divider = String('-'*135)
    record_pattern = Dict
    record_list = List
    
    def load(self, input_filename):
        try:
            in_file = open(input_filename)
            try:
                in_file.readline()
                self.project = in_file.readline().split(':')[-1].strip()
                self.sdr_file = in_file.readline().split()[-1].strip()
                date_time = in_file.readline().split()
                date =  [int(d) for d in date_time[3].split('-')]
                self.print_date = datetime.date(date[0],
                                                date[1],
                                                date[2])
                time =  [int(t) for t in date_time[4].split(':')]
                if date_time[-1] == 'PM':
                    time[0] += 12
                self.print_time = datetime.time(time[0],
                                                time[1],
                                                time[2])
                self.distance_unit = in_file.readline().split()[-1].strip()
                if self.distance_unit != 'Meters':
                    raise IOError, 'Unknown distance unit'
                self.angle_unit = in_file.readline().split(':')[-1].strip()
                if self.angle_unit != 'Degrees [dd-mm-ss.ss]':
                    raise IOError, 'Unknown angle unit'
                self.point_count = int(in_file.readline().split(':')[-1])
                in_file.readline()
                in_file.readline()
                heading = in_file.readline()
                self.record_pattern = dict(zip([heading[:8].strip(),
                                                heading[8:20].strip(),
                                                heading[20:25].strip(),
                                                heading[25:70].strip(),
                                                heading[70:115].strip(),
                                                heading[115:150].strip(),
                                                heading[150:].strip()],
                                               range(7))) 
                in_file.readline()
                records = ''.join(in_file.readlines())\
                            .split(self.record_divider + '\r\n')
                for record in records:
                    lines = record.splitlines()
                    for line in lines:
                        line = [line[:8].strip(),
                                line[8:20].strip(),
                                line[20:25].strip(),
                                line[25:70].strip(),
                                line[70:115].strip(),
                                line[115:150].strip(),
                                line[150:].strip()]
                        if line[1] == 'OBS':
                            obs = SOKKIARecord()
                            obs.point_id = int(line[self.record_pattern['Pt.']])
                            obs.record_type = line[self.record_pattern['Record Type']]
                            obs.dc = line[self.record_pattern['DC']]
                            h = line[self.record_pattern['North/Hor']]
                            h = h.split(':')[-1].split('-')
                            obs.north_horizontal = AngleDMS(degrees=int(h[0]),
                                                            minutes=int(h[1]),
                                                            seconds=int(h[2]),)
                            v = line[self.record_pattern['East/Vert']]
                            v = v.split(':')[-1].split('-')
                            obs.east_vertical = AngleDMS(degrees=int(v[0]),
                                                         minutes=int(v[1]),
                                                         seconds=int(v[2]),)
                            d = line[self.record_pattern['Elev./Dist']]
                            try:
                                d = float(d.split(':')[-1])
                            except ValueError:
                                d = 0
                            obs.elevation_distance = d
                            obs.code = line[self.record_pattern['Code']]
                            self.record_list.append(obs)
            finally:
                in_file.close()
            
        except:
            print "Unable to parse %s" % input_filename
            raise
        
    def save(self, output_filename):
        out_file = open(output_filename, 'wb')
        out_file.write('< Condition >\n')
        out_file.write('Project : %s\n' % self.project)
        out_file.write('File Name : %s\n' % self.sdr_file)
        out_file.write('Print Date : %s %s\n' % (self.print_date,
                                                 self.print_time.strftime('%I:%M:%S %p')))
        out_file.write('Distance Unit : %s\n' % self.distance_unit)
        out_file.write('Angle Unit : %s\n' % self.angle_unit)
        out_file.write('Pt. Count : %s\n\n' % self.point_count)
        out_file.write('%s\n' % self.record_divider)

        col_idx = dict(zip(self.record_pattern.values(),
                           self.record_pattern.keys()))
        col_width = {0: 8,
                     1: 12,
                     2: 5,
                     3: 45,
                     4: 45,
                     5: 35,
                     6: 10}
        for col in xrange(max(col_idx.keys())+1):
            out_file.write(col_idx[col].ljust(col_width[col]))
        out_file.write('\n%s\n' % self.record_divider)
        out_file.close()
        
def get_filenames():
    """Return a list of filenames to process."""
    parser = OptionParser(usage='%prog INPUT_FILES',
                          description=' '.join(__doc__.split()),
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
    return args

def average_codes(in_book,
                  horizontal_tol='0:0:30.0', vertical_tol='0:0:30.0',
                  distance_tol=0.01):
    """Average observations with the same code."""
    out_book = copy(in_book)
    out_book.record_list = [r for r in in_book.record_list \
                            if r.record_type != 'OBS']
    out_book.point_count = 0
    tmp = {}
    for record in in_book.record_list:
        tmp[record.code] = 1
        code_list = tmp.keys()
    record_codes = [rl.code for rl in in_book.record_list]
    for code in code_list:
        masked_codes =  ma.masked_not_equal(ma.asarray(record_codes), code)
        masked_index = ma.arange(masked_codes.size)
        masked_index.mask = masked_codes.mask
        record_list = asarray(in_book.record_list)[masked_index.compressed()]
        
        h_angles = []
        v_angles = []
        for record in record_list:
            if record.dc == 'F1':
                h_angles.append(record.north_horizontal)
                v_angles.append(record.east_vertical)
            elif record.dc == 'F2':
                reverse = record.north_horizontal.decimal_degrees + 180
                if reverse >= 360:
                    reverse -= 360
                h_angles.append(dd2dms(reverse))
                v_angles.append(dd2dms(360 \
                                       - record.east_vertical.decimal_degrees))
            else:
                continue
        distances = [r.elevation_distance for r in record_list]
        avg_record = SOKKIARecord(record_type = 'OBS',
                                  point_id = record_list[0].point_id,
                                  dc = 'F1',
                                  code = code)
        avg_record.north_horizontal, range_horizontal = avg_angles(h_angles)
        avg_record.east_vertical, range_vertical = avg_angles(v_angles)
        avg_record.elevation_distance = mean(distances)
        range_distance = ptp([distances])
        
        
        d, m, s = horizontal_tol.split(':')
        angle_tol = AngleDMS(degrees=int(d), minutes=int(m), seconds=float(s))
        if range_horizontal.decimal_degrees > angle_tol.decimal_degrees:
            print u'WARNING: Horizontal angle tolerance (%s) exceeded.' \
                    % angle_tol
            print u'%s HAR difference: %s\n' % (avg_record.code,
                                                range_horizontal)
        d, m, s = vertical_tol.split(':')
        angle_tol = AngleDMS(degrees=int(d), minutes=int(m), seconds=float(s))
        if range_vertical.decimal_degrees > angle_tol.decimal_degrees:
            print u'WARNING: Zenith angle tolerance (%s) exceeded.' % angle_tol
            print u'%s ZA difference: %s\n' % (avg_record.code, range_vertical)
        if range_distance > distance_tol:
            print 'WARNING: Slope distance tolerance (%.4f) exceeded.' \
                   % distance_tol
            print '%s S difference: %.4f\n' % (avg_record.code, range_distance)
        out_book.record_list.append(avg_record)
        out_book.point_count += 1
    return out_book

if __name__ == '__main__':
    for in_filename in get_filenames():
        BOOK = SOKKIABook()
        BOOK.load(in_filename)
        AVG_BOOK = average_codes(BOOK)
        AVG_BOOK.save('new_%s' % in_filename)