#!/usr/bin/env python
"""Manipulate and simplify SOKKIA text field books."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "6 February 2009"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

# Local imports.
from cogo import AngleDMS

# Standard library imports.
import datetime
from glob import glob
from optparse import OptionParser
from os import name, path

# Numpy imports.
from numpy import ma

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
                records = ''.join(in_file.readlines()).split('-'*135 + '\r\n')
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

def findall(L, value, start=0):
    """Generator that returns index to all instances of value in L."""
    i = start - 1
    try:
        i = L.index(value, i+i)
        yield i
    except ValueError:
        print value
        print i
        pass

def get_filenames():
    """Return a list of filenames to process."""
    parser = OptionParser(usage='%prog INPUT_FILES',
                          description=' '.join(__doc__.split()),
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
    return args

def average_codes(in_book):
    """Average observations with the same code."""
    tmp = {}
    for record in in_book.record_list:
        tmp[record.code] = 1
        code_list = tmp.keys()
    
    record_codes = [rl.code for rl in in_book.record_list]
    for code in code_list:
        masked_records =  ma.masked_not_equal(ma.asarray(record_codes), code)
        masked_index = ma.arange(masked_records.size)
        masked_index.mask = masked_records.mask
        print code, masked_index.compressed()
#    return out_book

if __name__ == '__main__':
    for in_filename in get_filenames():
        BOOK = SOKKIABook()
        BOOK.load(in_filename)
        average_codes(BOOK)