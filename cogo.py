#!/usr/bin/env python
"""Perform coordinate geometry calculations."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "27 February 2008"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

# Standard library imports.
import csv

# Enthought library imports.
from enthought.traits.api import BaseFloat, BaseInt, Float, HasTraits, \
    Instance, Property, cached_property, String
from enthought.traits.ui.api import View, Group, HGroup, Item
from enthought.traits.ui.menu import LiveButtons

from numpy import cos, floor, mean, radians, sin

class DegreeInt(BaseInt):
    """An integer >= 0 and < 360 representing an angle in degrees."""
    info_text = 'an integer >= 0 and < 360'
    def validate(self, object, name, value):
        value = super(DegreeInt, self).validate(object, name, value)
        if 0 <= value < 360:
            return value
        self.error(object, name, value)
        
class MinuteInt(BaseInt):
    """An integer >= 0 and < 60 representing an angle in minutes."""
    info_text = 'an integer >= 0 and < 60'
    def validate(self, object, name, value):
        value = super(MinuteInt, self).validate(object, name, value)
        if 0 <= value < 60:
            return value
        self.error(object, name, value)

class SecondFloat(BaseFloat):
    """A float >= 0 and < 60 representing an angle in seconds."""
    info_text = 'a float >= 0 and < 60'
    def validate(self, object, name, value):
        value = super(SecondFloat, self).validate(object, name, value)
        if 0 <= value < 60:
            return value
        self.error(object, name, value)

class AngleDMS(HasTraits):
    """An angle in degrees, minutes, and seconds."""
    degrees = DegreeInt
    minutes = MinuteInt
    seconds = SecondFloat
    decimal_degrees = Property(depends_on='degrees, minutes, seconds')
    radians = Property(depends_on='decimal_degrees')
    
    @cached_property 
    def _get_decimal_degrees(self):
        return self.degrees + self.minutes/60.0 + self.seconds/3600.0
    
    @cached_property
    def _get_radians(self):
        return radians(self.decimal_degrees)
    
    view = View(HGroup(Item('degrees'), Item('minutes'), Item('seconds')))

class BaseStation(HasTraits):
    """A station at the origin of a survey."""
    id = String
    y = Float
    x = Float
    z = Float
    z_offset = Float
    horizontal_angle_offset = Instance(AngleDMS, kw={'degrees': 0,
                                                     'minutes': 0,
                                                     'seconds': 0})
    view = View(Item('x'),
                Item('y'),
                HGroup(Item('z'), Item('z_offset')),
                Item('horizontal_angle_offset', style='custom'))
    
class TargetStation(HasTraits):
    """A station with coordinates calulated relative to a BaseStation."""
    id = String
    base = Instance(BaseStation, kw={'x': 0,
                                     'y': 0,
                                     'z': 0,
                                     'z_offset': 0})
    zenith_angle = Instance(AngleDMS, kw={'degrees': 90,
                                          'minutes': 0,
                                          'seconds': 0})
    horizontal_angle = Instance(AngleDMS, kw={'degrees': 0,
                                              'minutes': 0,
                                              'seconds': 0})
    z_offset = Float
    slope_distance = Float
    horizontal_distance = Property(depends_on='zenith_angle.radians, \
                                               horizontal_angle.radians, \
                                               slope_distance')
    vertical_distance = Property(depends_on='zenith_angle.radians, \
                                             horizontal_angle.radians, \
                                             slope_distance')
    y = Property(depends_on='base.y, \
                             base.horizontal_angle_offset.radians,\
                             zenith_angle.radians, \
                             horizontal_angle.radians, \
                             slope_distance, \
                             z_offset')
    x = Property(depends_on='base.x, \
                             base.horizontal_angle_offset.radians,\
                             zenith_angle.radians, \
                             horizontal_angle.radians, \
                             slope_distance, \
                             z_offset')
    z = Property(depends_on='base.z, \
                             base.z_offset, \
                             base.horizontal_angle_offset.radians,\
                             zenith_angle.radians, \
                             horizontal_angle.radians, \
                             slope_distance, \
                             z_offset')
    
    @cached_property
    def _get_horizontal_distance(self):
        return self.slope_distance * sin(self.zenith_angle.radians)
    
    @cached_property
    def _get_vertical_distance(self):
        return self.slope_distance * cos(self.zenith_angle.radians)
    
    @cached_property
    def _get_y(self):
        return cos(self.horizontal_angle.radians
                   + self.base.horizontal_angle_offset.radians) \
               * self.horizontal_distance + self.base.y
    
    @cached_property
    def _get_x(self):
        return sin(self.horizontal_angle.radians
                   + self.base.horizontal_angle_offset.radians) \
               * self.horizontal_distance + self.base.x
    
    @cached_property
    def _get_z(self):
        return self.slope_distance * cos(self.zenith_angle.radians) \
               + self.base.z \
               + self.base.z_offset - self.z_offset
    
    view = View(Item('base', style='custom'),
                Group(Item('horizontal_angle', style='custom'),
                      Item('zenith_angle', style='custom'),
                      Item('slope_distance'),
                      label='Shot to target',
                      show_border=True),
                Group(Item('z_offset'),
                      HGroup(Item('x',
                                  format_str='%.3f',
                                  springy = True),
                             Item('y',
                                  format_str='%.3f',
                                  springy = True),
                             Item('z',
                                  format_str='%.3f',
                                  springy = True))),
                buttons=LiveButtons)
                      
def gui():
    """Run the interactive converter."""
#    import enthought.traits.ui.wx.view_application
#    enthought.traits.ui.wx.view_application.redirect_filename = 'cogo_wx.log'
#    Uncomment the next line to start interactive debugger.
#    from enthought.developer.helper.fbi import bp; bp()
    target = TargetStation()
    target.configure_traits()
    
def load_measurements(filename):
    """Load survey measurements from a text file."""
    try:
        reader = csv.reader(open(filename, 'rb'),
                            delimiter=' ',
                            skipinitialspace=True)
        target_list = []
        base = BaseStation()
        for n_row, row in enumerate(reader):
            if row[0][0] == '#':
                continue
            if n_row == 1:
                base.id = row[0]
                base.x = float(row[1])
                base.y = float(row[2])
                base.z = float(row[3])
                base.z_offset = float(row[4])
                base.horizontal_angle_offset = parse_angle(row[5])
                
            else:
                target = TargetStation()
                target.base = base
                target.id = row[0]
                target.horizontal_angle = avg_HAR(parse_angle(row[1]),
                                                  parse_angle(row[4]))
                target.zenith_angle = avg_ZAR(parse_angle(row[2]),
                                              parse_angle(row[5]))
                target.slope_distance = mean([float(row[3]), float(row[6])])
                target.z_offset = float(row[7])
                target_list.append(target)
    except:
        print "Processing file %s failed." % filename
        raise
    
    return base, target_list

def save_coordinates(base, target_list, out_filename):
    """Save the coordinates of a base station and a list of target stations to
    a text file."""
    writer = csv.writer(open(out_filename, 'wb'), delimiter=' ')
    writer.writerow(['#id', 'x', 'y', 'z'])
    writer.writerow([base.id, base.x, base.y, base.z])
    for target in target_list:
        writer.writerow([target.id, target.x, target.y, target.z])
    
def parse_angle(angle_string):
    """ Parse a string with the format: degrees:minutes:seconds and return
    an instance of AngleDMS. """
    angle_dms = AngleDMS()
    angle_dms.degrees = int(angle_string.split(':')[0])
    angle_dms.minutes = int(angle_string.split(':')[1])
    angle_dms.seconds = float(angle_string.split(':')[2])
    return angle_dms

def avg_HAR(direct_HAR, reverse_HAR):
    """ Average direct and reverse HAR measurements and return an instance of
    AngleDMS. """
    reverse = reverse_HAR.decimal_degrees + 180
    if reverse >= 360:
        reverse -= 360
    avg_dd = mean([reverse, direct_HAR.decimal_degrees])
    return dd2dms(avg_dd)

def avg_ZAR(direct_ZAR, reverse_ZAR):
    """ Average direct and reverse ZAR measurements and return an instance of
    AngleDMS. """
    reverse = 360 -reverse_ZAR.decimal_degrees
    avg_dd = mean([reverse,
                   direct_ZAR.decimal_degrees])
    return dd2dms(avg_dd)

def dd2dms(angle_dd):
    """ Convert an angle in decimal degrees to an instance of AngleDMS. """
    angle_dms = AngleDMS()
    angle_dms.degrees = int(angle_dd)
    angle_dms.minutes = int(60 * (angle_dd - angle_dms.degrees))
    angle_dms.seconds = 60 * (60 * (angle_dd - angle_dms.degrees) - angle_dms.minutes)
    return angle_dms

def get_filenames():
    """Return a list of filenames to process."""
    from optparse import OptionParser
    from glob import glob
    from os import name
    
    parser = OptionParser(usage='%prog INPUT_FILES',
                          description=' '.join(__doc__.split()),
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
    return args

if __name__ == "__main__":
    FILENAMES = get_filenames()
    if FILENAMES:
        for in_filename in FILENAMES:
            OUT_FILENAME = '_'.join(['coordinates', in_filename])
            BASE, TARGETS = load_measurements(in_filename)
            save_coordinates(BASE, TARGETS, OUT_FILENAME)
    else:
        gui()
