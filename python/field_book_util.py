#!/usr/bin/env python
"""Manipulate and simplify SOKKIA text field books."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "6 February 2009"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

# Local imports.
from cogo import AngleDMS, avg_angles, dd2dms

# Standard library imports.
import csv
import datetime
import re
import sys
from copy import copy
from glob import glob
from optparse import OptionParser
from os import name, path

# Numpy imports.
from numpy import empty, mean, ptp

# Enthought library imports.
from enthought.traits.api import Date, Dict, Bool, Enum, File, Float, \
                                 HasTraits, Instance, Int, List, String, Time

class TerminalController:
    """
    A class that can be used to portably generate formatted output to
    a terminal.  
    
    `TerminalController` defines a set of instance variables whose
    values are initialized to the control sequence necessary to
    perform a given action.  These can be simply included in normal
    output to the terminal:

        >>> term = TerminalController()
        >>> print 'This is '+term.GREEN+'green'+term.NORMAL

    Alternatively, the `render()` method can used, which replaces
    '${action}' with the string required to perform 'action':

        >>> term = TerminalController()
        >>> print term.render('This is ${GREEN}green${NORMAL}')

    If the terminal doesn't support a given action, then the value of
    the corresponding instance variable will be set to ''.  As a
    result, the above code will still work on terminals that do not
    support color, except that their output will not be colored.
    Also, this means that you can test whether the terminal supports a
    given action by simply testing the truth value of the
    corresponding instance variable:

        >>> term = TerminalController()
        >>> if term.CLEAR_SCREEN:
        ...     print 'This terminal supports clearning the screen.'

    Finally, if the width and height of the terminal are known, then
    they will be stored in the `COLS` and `LINES` attributes.
    
    Copied from the Python Cookbook Recipe 475116:
    Using terminfo for portable color output & cursor control
    """
    # Cursor movement:
    BOL = ''             #: Move the cursor to the beginning of the line
    UP = ''              #: Move the cursor up one line
    DOWN = ''            #: Move the cursor down one line
    LEFT = ''            #: Move the cursor left one char
    RIGHT = ''           #: Move the cursor right one char

    # Deletion:
    CLEAR_SCREEN = ''    #: Clear the screen and move to home position
    CLEAR_EOL = ''       #: Clear to the end of the line.
    CLEAR_BOL = ''       #: Clear to the beginning of the line.
    CLEAR_EOS = ''       #: Clear to the end of the screen

    # Output modes:
    BOLD = ''            #: Turn on bold mode
    BLINK = ''           #: Turn on blink mode
    DIM = ''             #: Turn on half-bright mode
    REVERSE = ''         #: Turn on reverse-video mode
    NORMAL = ''          #: Turn off all modes

    # Cursor display:
    HIDE_CURSOR = ''     #: Make the cursor invisible
    SHOW_CURSOR = ''     #: Make the cursor visible

    # Terminal size:
    COLS = None          #: Width of the terminal (None for unknown)
    LINES = None         #: Height of the terminal (None for unknown)

    # Foreground colors:
    BLACK = BLUE = GREEN = CYAN = RED = MAGENTA = YELLOW = WHITE = ''
    
    # Background colors:
    BG_BLACK = BG_BLUE = BG_GREEN = BG_CYAN = ''
    BG_RED = BG_MAGENTA = BG_YELLOW = BG_WHITE = ''
    
    _STRING_CAPABILITIES = """
    BOL=cr UP=cuu1 DOWN=cud1 LEFT=cub1 RIGHT=cuf1
    CLEAR_SCREEN=clear CLEAR_EOL=el CLEAR_BOL=el1 CLEAR_EOS=ed BOLD=bold
    BLINK=blink DIM=dim REVERSE=rev UNDERLINE=smul NORMAL=sgr0
    HIDE_CURSOR=cinvis SHOW_CURSOR=cnorm""".split()
    _COLORS = """BLACK BLUE GREEN CYAN RED MAGENTA YELLOW WHITE""".split()
    _ANSICOLORS = "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE".split()

    def __init__(self, term_stream=sys.stdout):
        """
        Create a `TerminalController` and initialize its attributes
        with appropriate values for the current terminal.
        `term_stream` is the stream that will be used for terminal
        output; if this stream is not a tty, then the terminal is
        assumed to be a dumb terminal (i.e., have no capabilities).
        """
        # Curses isn't available on all platforms
        try: import curses
        except: return

        # If the stream isn't a tty, then assume it has no capabilities.
        if not term_stream.isatty(): return

        # Check the terminal type.  If we fail, then assume that the
        # terminal has no capabilities.
        try: curses.setupterm()
        except: return

        # Look up numeric capabilities.
        self.COLS = curses.tigetnum('cols')
        self.LINES = curses.tigetnum('lines')
        
        # Look up string capabilities.
        for capability in self._STRING_CAPABILITIES:
            (attrib, cap_name) = capability.split('=')
            setattr(self, attrib, self._tigetstr(cap_name) or '')

        # Colors
        set_fg = self._tigetstr('setf')
        if set_fg:
            for i,color in zip(range(len(self._COLORS)), self._COLORS):
                setattr(self, color, curses.tparm(set_fg, i) or '')
        set_fg_ansi = self._tigetstr('setaf')
        if set_fg_ansi:
            for i,color in zip(range(len(self._ANSICOLORS)), self._ANSICOLORS):
                setattr(self, color, curses.tparm(set_fg_ansi, i) or '')
        set_bg = self._tigetstr('setb')
        if set_bg:
            for i,color in zip(range(len(self._COLORS)), self._COLORS):
                setattr(self, 'BG_'+color, curses.tparm(set_bg, i) or '')
        set_bg_ansi = self._tigetstr('setab')
        if set_bg_ansi:
            for i,color in zip(range(len(self._ANSICOLORS)), self._ANSICOLORS):
                setattr(self, 'BG_'+color, curses.tparm(set_bg_ansi, i) or '')

    def _tigetstr(self, cap_name):
        # String capabilities can include "delays" of the form "$<2>".
        # For any modern terminal, we should be able to just ignore
        # these, so strip them out.
        import curses
        cap = curses.tigetstr(cap_name) or ''
        return re.sub(r'\$<\d+>[/*]?', '', cap)

    def render(self, template):
        """
        Replace each $-substitutions in the given template string with
        the corresponding terminal control string (if it's defined) or
        '' (if it's not).
        """
        return re.sub(r'\$\$|\${\w+}', self._render_sub, template)

    def _render_sub(self, match):
        s = match.group()
        if s == '$$': return s
        else: return getattr(self, s[2:-1])

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
                    if time[0] != 12:
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

    def export_azimuth_obs(self, output_filename, az_offset=0, za_offset=0):
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
                if az_offset == 0:
                    az = record.north_horizontal
                else:
                    az = record.north_horizontal.decimal_degrees + az_offset
                    if az >= 360:
                        az -= 360
                    az = dd2dms(az)
                if za_offset == 0:
                    za = record.east_vertical
                else:
                    za = record.east_vertical.decimal_degrees + za_offset
                    za = dd2dms(za)
                row.append('%.3i%.2i%07.4f' % (az.degrees,
                                               az.minutes,
                                               az.seconds))
                row.append('%g' % self.tps_model.horizontal_sd)
                row.append('%.3i%.2i%07.4f' % (za.degrees,
                                               za.minutes,
                                               za.seconds))
                row.append('%g' % self.tps_model.zenith_sd)
                row.append(record.elevation_distance)
                row.append('%g' % self.tps_model.chord_sd)
                row.append(instrument_height)
                row.append(target_height)
                rows.append(row)
        writer = csv.writer(out_file, delimiter=';', lineterminator='\n')
        writer.writerows(rows)
                
def get_args():
    """Return a list of filenames to process."""
    parser = OptionParser(usage='%prog INPUT_FILES',
                          description=' '.join(__doc__.split()),
                          version=__version__)
    parser.add_option('-l', '--log', dest='log',
                      action="store_true",
                      help="Log input measurements' range of values.")
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
    return opts, args

def average_code_obs(in_book,
                  horizontal_tol='0:1:0.0', vertical_tol='0:1:0.0',
                  distance_tol=0.01):
    """Average observations with the same code."""
    term = TerminalController()
                
    out_book = copy(in_book)
    out_book.point_count = 0
    out_book.record_list = []
    
    code_dict = {}
    sorted_codes = []
    for record in in_book.record_list:
        if record.code not in sorted_codes:
            code_dict[record.code] = [record]
            sorted_codes.append(record.code)
        else:
            code_dict[record.code].append(record)
    ranges = []
    for code in sorted_codes:
        code_records = code_dict[code]
        if code_records[0].record_type == 'OBS':
            avg_record = SOKKIARecord(record_type = code_records[0].record_type,
                                      point_id = code_records[0].point_id,
                                      dc = 'F1',
                                      code = code)
            h_angles = []
            v_angles = []
            distances = []
            for record in code_records:
                if record.dc == 'F1':
                    h_angles.append(record.north_horizontal)
                    v_angles.append(record.east_vertical)
                    distances.append(record.elevation_distance)
                elif record.dc == 'F2': 
                    reverse = record.north_horizontal.decimal_degrees + 180
                    if reverse >= 360:
                        reverse -= 360
                    h_angles.append(dd2dms(reverse))
                    v_angles.append(dd2dms(360 \
                                           - record.east_vertical.decimal_degrees))
                    distances.append(record.elevation_distance)
                
            avg_record.north_horizontal, range_horizontal = avg_angles(h_angles)
            avg_record.east_vertical, range_vertical = avg_angles(v_angles)
            avg_record.elevation_distance = mean(distances)
            range_distance = ptp(distances)
            
            d, m, s = horizontal_tol.split(':')
            angle_tol = AngleDMS(degrees=int(d),
                                 minutes=int(m),
                                 seconds=float(s))
            if min([360 - range_horizontal.decimal_degrees,
                   range_horizontal.decimal_degrees]) > angle_tol.decimal_degrees:
                print u'WARNING: Horizontal angle tolerance (%s) exceeded.' \
                        % angle_tol
                print u'%s HAR difference: %s%s%s\n' % (avg_record.code,
                                                        term.RED,
                                                        range_horizontal,
                                                        term.NORMAL)
            d, m, s = vertical_tol.split(':')
            angle_tol = AngleDMS(degrees=int(d),
                                 minutes=int(m),
                                 seconds=float(s))
            if range_vertical.decimal_degrees > angle_tol.decimal_degrees:
                print u'WARNING: Zenith angle tolerance (%s) exceeded.' % angle_tol
                print u'%s ZA difference: %s%s%s\n' % (avg_record.code,
                                                       term.YELLOW,
                                                       range_vertical,
                                                       term.NORMAL)
            if range_distance > distance_tol:
                print 'WARNING: Slope distance tolerance (%.4f) exceeded.' \
                       % distance_tol
                print '%s S difference: %s%.4f%s\n' % (avg_record.code,
                                                       term.MAGENTA,
                                                       range_distance,
                                                       term.NORMAL)
            ranges.append([v_angles[0].decimal_degrees - v_angles[1].decimal_degrees,
                           h_angles[0].decimal_degrees - h_angles[1].decimal_degrees,
                           distances[0] - distances[1],
                           code])
            out_book.record_list.append(avg_record)
            out_book.point_count += 1
        else:
            for record in code_records:
                out_book.record_list.append(record)
                out_book.point_count += 1
    return out_book, ranges

if __name__ == '__main__':
    OPTS, ARGS = get_args()
    for in_filename in ARGS:
        BOOK = SOKKIABook()
        BOOK.load(in_filename)
        AVG_BOOK, RANGES = average_code_obs(BOOK)
#        AVG_BOOK.export_hor_obs('%s.obs' % \
#                                path.splitext(path.basename(in_filename))[0],
#                                bs_station='north')
        AVG_BOOK.export_azimuth_obs('%s.obs' % \
                                    path.splitext(path.basename(in_filename))[0])
#        AVG_BOOK.export_direction_obs('%s.obs' % \
#                                      path.splitext(path.basename(in_filename))[0])
        if OPTS.log:
            l_handle = open(path.splitext(path.basename(in_filename))[0]+'.log',
                            'wb')
            l_handle.write('range_ZA_dd range_HAR_dd range_S code\n')
            try:
                lines = ["%.6f %.6f %.4f %s\n" % tuple(v) for v in RANGES]
                l_handle.writelines(lines)
            except:
                raise
            finally:
                l_handle.close()