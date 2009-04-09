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
import csv
import datetime
from glob import glob
from optparse import OptionParser
from os import name, path

# Numpy imports.
from numpy import empty, mean, ptp

# Enthought library imports.
from enthought.traits.api import Date, Dict, Bool, Enum, File, Float, \
                                 HasTraits, Instance, Int, List, String, Time

class TPSModel(HasTraits):
    """Define total station model and specifications.""" 
    horizontal_sd = Float(5, desc='horizontal angle standard deviation in seconds')
    zenith_sd = Float(5, desc='zenith angle standard deviation in seconds')
    chord_sd = Float(.003, desc='chord distance standard deviation in m')
    chord_ppm = Float(2, desc='chord distance ppm variation')
    model = String
    
    known_models = {'SET530R V33-17': {'horizontal_sd': 5,
                                       'zenith_sd': 5,
                                       'chord_sd': 0.002,
                                       'chord_ppm': 2},
                    'SET5F': {'horizontal_sd': 5,
                              'zenith_sd': 5,
                              'chord_sd': 0.003,
                              'chord_ppm': 2}}
    
    def _model_changed(self, old, new):
        if new in self.known_models.keys():
            self.horizontal_sd = self.known_models[new]['horizontal_sd']
            self.zenith_sd = self.known_models[new]['zenith_sd']
            self.chord_sd = self.known_models[new]['chord_sd']
            self.chord_ppm = self.known_models[new]['chord_ppm']
    

class SOKKIARecord(HasTraits):
    """Single or multiline record in a SOKKIA text fieldbook."""
    record_type = Enum('Fbk Settings', 'JOB', 'SCALE', 'INSTR', 'RED',
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
    
class Job(SOKKIARecord):
    """Job name and source file."""
    source_file = String
    job_id = String
    
class Station(SOKKIARecord):
    """Base station description."""
    north_horizontal = Float
    east_vertical = Float
    theodolite_height = Float
    
class Target(SOKKIARecord):
    """Target description."""
    target_height = Float
    
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
    tps_model = Instance(TPSModel)
    
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
                file_text = ''.join(in_file.readlines())
                # Normalize new lines and split records.
                file_text = file_text.replace('\r\n', '\n').replace('\r', '\n')
                records = file_text.split('\n%s\n' % self.record_divider)
                for record in records:
                    lines = record.splitlines()
                    record = empty([len(lines), 7], dtype='S45')
                    for line_num, line in enumerate(lines):
                        line = [line[:8].strip(),
                                line[8:20].strip(),
                                line[20:25].strip(),
                                line[25:70].strip(),
                                line[70:115].strip(),
                                line[115:150].strip(),
                                line[150:].strip()]
                        record[line_num, :] = line
                    if len(record.shape) == 1:
                        record = record.reshape([1, record.size])
                    if record.shape[0] == 0:
                        continue
                    if record[0, 1] == 'OBS':
                        obs = SOKKIARecord()
                        obs.point_id = int(record[0, self.record_pattern['Pt.']])
                        obs.record_type = record[0, self.record_pattern['Record Type']]
                        obs.dc = record[0, self.record_pattern['DC']]
                        obs.code = str(record[0, self.record_pattern['Code']]).strip()
                        h = record[0, self.record_pattern['North/Hor']]
                        h = h.split(':')[-1].split('-')
                        obs.north_horizontal = AngleDMS(degrees=int(h[0]),
                                                        minutes=int(h[1]),
                                                        seconds=int(h[2]),)
                        v = record[0, self.record_pattern['East/Vert']]
                        v = v.split(':')[-1].split('-')
                        obs.east_vertical = AngleDMS(degrees=int(v[0]),
                                                     minutes=int(v[1]),
                                                     seconds=int(v[2]),)
                        d = record[0, self.record_pattern['Elev./Dist']]
                        try:
                            d = float(d.split(':')[-1])
                        except ValueError:
                            d = 0
                        obs.elevation_distance = d
                        self.record_list.append(obs)
                    elif record[0, 1] == 'JOB':
                        job = Job()
                        job.record_type = record[0, self.record_pattern['Record Type']]
                        job.dc = record[0, self.record_pattern['DC']]
                        job.source_file = record[0, self.record_pattern['Elev./Dist']].strip()
                        j = record[0, self.record_pattern['North/Hor']]
                        job.job_id = j.split(':')[-1].strip()
                        self.record_list.append(job)
                    elif record[0, 1] == 'INSTR':
                        m = record[1, 3].split(':')[1].strip()
                        self.tps_model = TPSModel(model = m)
#                        self.tps_model.model = record[1,
#                                                      3].split(':')[1].strip()
                    elif record[0, 1] == 'STN':
                        stn = Station()
                        stn.point_id = int(record[0, self.record_pattern['Pt.']])
                        stn.record_type = record[0, self.record_pattern['Record Type']]
                        stn.dc = record[0, self.record_pattern['DC']]
                        stn.code = str(record[0, self.record_pattern['Code']]).strip()
                        n = record[0, self.record_pattern['North/Hor']]
                        stn.north_horizontal = float(n.split(':')[-1])
                        e = record[0, self.record_pattern['East/Vert']]
                        stn.east_vertical = float(n.split(':')[-1])
                        d = record[0, self.record_pattern['Elev./Dist']]
                        stn.elevation_distance = float(d.split(':')[-1])
                        t = record[1, self.record_pattern['North/Hor']]
                        stn.theodolite_height = float(t.split(':')[-1])
                        self.record_list.append(stn)
                    elif record[0, 1] == 'TARGET':
                        trg = Target()
                        trg.record_type = record[0, self.record_pattern['Record Type']]
                        trg.dc = record[0, self.record_pattern['DC']]
                        trg.code = str(record[0, self.record_pattern['Code']]).strip()
                        h = record[0, self.record_pattern['North/Hor']]
                        trg.target_height = float(h.split(':')[-1])
                        self.record_list.append(trg)
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

    def export_hor_obs(self,
                       output_filename,
                       bs_station='BS_STATION',
                       hor_offset = 0):
        """Export fieldbook as Horizontal Angle Right observations in a text
        format that is compatible with the COLUMBUS network adjustment
        software."""
        out_file = open(output_filename, 'w')
        out_file.write('! Chord (Slope) Distance PPM correction\n')
        out_file.write('$PPM_CHORDDIST; %g\n\n' % self.tps_model.chord_ppm)
        out_file.write('! ')
        cols = ['AT Station Name',
                'TO Station Name',
                'BS Station Name',
                'Hor Angle',
                'Hor Angle SD',
                'Zenith',
                'Zenith SD',
                'Chord',
                'Chord SD',
                'Instr Hgt',
                'Targ Hgt']
        rows = [cols]
        for record in self.record_list:
            if record.record_type == "STN":
                at = record.code
                instrument_height = record.theodolite_height
            elif record.record_type == "TARGET":
                target_height = record.target_height
            elif record.record_type == "OBS":
                row = ['$HOR_COMPACT']
                row.append(at)
                row.append(record.code)
                row.append(bs_station)
                if hor_offset == 0:
                    hor = record.north_horizontal
                else:
                    hor = record.north_horizontal.decimal_degrees + hor_offset
                    if hor >= 360:
                        hor -= 360
                    hor = dd2dms(hor)
                row.append('%.3i%.2i%07.4f' % (hor.degrees,
                                               hor.minutes,
                                               hor.seconds))
                row.append('%g' % self.tps_model.horizontal_sd)
                row.append('%.3i%.2i%07.4f' % (record.east_vertical.degrees,
                                               record.east_vertical.minutes,
                                               record.east_vertical.seconds))
                row.append('%g' % self.tps_model.zenith_sd)
                row.append(record.elevation_distance)
                row.append('%g' % self.tps_model.chord_sd)
                row.append(instrument_height)
                row.append(target_height)
                rows.append(row)
        writer = csv.writer(out_file, delimiter=';', lineterminator='\n')
        writer.writerows(rows)
        
    def export_direction_obs(self, output_filename):
        """Export fieldbook as direction observations in a text format that
        is compatible with the COLUMBUS network adjustment software."""
        out_file = open(output_filename, 'w')
        out_file.write('! Chord (Slope) Distance PPM correction\n')
        out_file.write('$PPM_CHORDDIST; %g\n\n' % self.tps_model.chord_ppm)
        out_file.write('! ')
        cols = ['AT Station Name',
                'TO Station Name',
                'Direction',
                'Direction SD',
                'Zenith',
                'Zenith SD',
                'Chord',
                'Chord SD',
                'Instr Hgt',
                'Targ Hgt',
                'DirSetNum']
        rows = [cols]
        for record in self.record_list:
            if record.record_type == "JOB":
                job = record.job_id
            elif record.record_type == "STN":
                at = record.code
                instrument_height = record.theodolite_height
            elif record.record_type == "TARGET":
                target_height = record.target_height
            elif record.record_type == "OBS":
                row = ['$DIR_COMPACT']
                row.append(at)
                row.append(record.code)
                row.append('%.3i%.2i%07.4f' % (record.north_horizontal.degrees,
                                               record.north_horizontal.minutes,
                                               record.north_horizontal.seconds))
                row.append('%g' % self.tps_model.horizontal_sd)
                row.append('%.3i%.2i%07.4f' % (record.east_vertical.degrees,
                                               record.east_vertical.minutes,
                                               record.east_vertical.seconds))
                row.append('%g' % self.tps_model.zenith_sd)
                row.append(record.elevation_distance)
                row.append('%g' % self.tps_model.chord_sd)
                row.append(instrument_height)
                row.append(target_height)
                row.append(job)
                rows.append(row)
        writer = csv.writer(out_file, delimiter=';', lineterminator='\n')
        writer.writerows(rows)

    def export_azimuth_obs(self, output_filename):
        """Export fieldbook as azimuth observations in a text format that
        is compatible with the COLUMBUS network adjustment software."""
        out_file = open(output_filename, 'w')
        out_file.write('! Chord (Slope) Distance PPM correction\n')
        out_file.write('$PPM_CHORDDIST; %g\n\n' % self.tps_model.chord_ppm)
        out_file.write('! ')
        cols = ['AT Station Name',
                'TO Station Name',
                'Azimuth',
                'Azimuth SD',
                'Zenith',
                'Zenith SD',
                'Chord',
                'Chord SD',
                'Instr Hgt',
                'Targ Hgt']
        rows = [cols]
        for record in self.record_list:
            if record.record_type == "STN":
                at = record.code
                instrument_height = record.theodolite_height
            elif record.record_type == "TARGET":
                target_height = record.target_height
            elif record.record_type == "OBS":
                row = ['$AZ_COMPACT']
                row.append(at)
                row.append(record.code)
                row.append('%.3i%.2i%07.4f' % (record.north_horizontal.degrees,
                                               record.north_horizontal.minutes,
                                               record.north_horizontal.seconds))
                row.append('%g' % self.tps_model.horizontal_sd)
                row.append('%.3i%.2i%07.4f' % (record.east_vertical.degrees,
                                               record.east_vertical.minutes,
                                               record.east_vertical.seconds))
                row.append('%g' % self.tps_model.zenith_sd)
                row.append(record.elevation_distance)
                row.append('%g' % self.tps_model.chord_sd)
                row.append(instrument_height)
                row.append(target_height)
                rows.append(row)
        writer = csv.writer(out_file, delimiter=';', lineterminator='\n')
        writer.writerows(rows)
                
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
        if record.record_type == 'OBS':
            tmp[record.code] = 1
    code_list = tmp.keys()
    for code in code_list:
        h_angles = []
        v_angles = []
        distances = []
        for record in in_book.record_list:
            if code != record.code:
                continue 
            if record.dc == 'F1':
                h_angles.append(record.north_horizontal)
                v_angles.append(record.east_vertical)
                distances.append(record.elevation_distance)
                point_id = record.point_id
            elif record.dc == 'F2':
                reverse = record.north_horizontal.decimal_degrees + 180
                if reverse >= 360:
                    reverse -= 360
                h_angles.append(dd2dms(reverse))
                v_angles.append(dd2dms(360 \
                                       - record.east_vertical.decimal_degrees))
                distances.append(record.elevation_distance)
                if not point_id:
                    point_id = record.point_id
            else:
                continue
        avg_record = SOKKIARecord(record_type = 'OBS',
                                  point_id = point_id,
                                  dc = 'F1',
                                  code = code)
        avg_record.north_horizontal, range_horizontal = avg_angles(h_angles)
        avg_record.east_vertical, range_vertical = avg_angles(v_angles)
        avg_record.elevation_distance = mean(distances)
        range_distance = ptp([distances])
        
        d, m, s = horizontal_tol.split(':')
        angle_tol = AngleDMS(degrees=int(d), minutes=int(m), seconds=float(s))
        if min([360 - range_horizontal.decimal_degrees,
               range_horizontal.decimal_degrees]) > angle_tol.decimal_degrees:
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
#        AVG_BOOK.export_hor_obs('%s.obs' % \
#                                path.splitext(path.basename(in_filename))[0],
#                                bs_station='m3a',
#                                hor_offset= -0.0319444)
        AVG_BOOK.export_azimuth_obs('%s.obs' % \
                                    path.splitext(path.basename(in_filename))[0])
#        AVG_BOOK.export_direction_obs('%s.obs' % \
#                                      path.splitext(path.basename(in_filename))[0])
