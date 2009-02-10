#!/usr/bin/env python
"""Perform coordinate geometry calculations."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "27 February 2008"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

# Standard library imports.
import csv
from os.path import split

# Enthought library imports.
from enthought.traits.api import BaseFloat, BaseInt, Float, HasTraits, \
    Instance, Property, cached_property, String
from enthought.traits.ui.api import View, Group, HGroup, Item
from enthought.traits.ui.menu import LiveButtons

from numpy import abs, arccos, asarray, cos, degrees, dot, empty, \
                  mean, radians, sin
from numpy.linalg import norm

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
    geo_unit_vector = Property(depends_on='radians',
                               desc='X-Y unit vector defined following ' \
                                     'geographic convention, angle measured ' \
                                     'clockwise from the positive y axis ' \
                                     '(north).')
    
    @cached_property 
    def _get_decimal_degrees(self):
        return self.degrees + self.minutes/60.0 + self.seconds/3600.0
    
    @cached_property
    def _get_radians(self):
        return radians(self.decimal_degrees)
    
    @cached_property
    def _get_geo_unit_vector(self):
        return asarray([sin(self.radians), cos(self.radians)])
        
    view = View(HGroup(Item('degrees'), Item('minutes'), Item('seconds')))

class BaseSetup(HasTraits):
    """Base station setup at the origin of a survey."""
    id = String
    x = Float
    y = Float
    z = Float
    z_offset = Float
    horizontal_angle_offset = Instance(AngleDMS, kw={'degrees': 0,
                                                     'minutes': 0,
                                                     'seconds': 0})
    view = View(Group(HGroup(Item('x',
                                  springy = True),
                            Item('y',
                                 springy = True),
                            Item('z',
                                 springy = True)),
                      HGroup(Item('z_offset')),
                      Item('horizontal_angle_offset', style='custom'),
                      label='Base station setup',
                      show_border=True)
    )
    
class Observation(HasTraits):
    """Observation of horizontal angle, zenith angle, and slope distance
       collected at a BaseSetup."""
    id = String
    base = Instance(BaseSetup, kw={'x': 0,
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
    x = Property(depends_on='base.x, \
                             base.horizontal_angle_offset.radians,\
                             zenith_angle.radians, \
                             horizontal_angle.radians, \
                             slope_distance, \
                             z_offset')
    y = Property(depends_on='base.y, \
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
    def _get_x(self):
        return sin(self.horizontal_angle.radians
                   + self.base.horizontal_angle_offset.radians) \
               * self.horizontal_distance + self.base.x  
        
    @cached_property
    def _get_y(self):
        return cos(self.horizontal_angle.radians
                   + self.base.horizontal_angle_offset.radians) \
               * self.horizontal_distance + self.base.y
               
    @cached_property
    def _get_z(self):
        return self.slope_distance * cos(self.zenith_angle.radians) \
               + self.base.z \
               + self.base.z_offset - self.z_offset
    
    view = View(Item('base', style='custom', show_label=False),
                Group(Item('horizontal_angle', style='custom'),
                      Item('zenith_angle', style='custom'),
                      Item('slope_distance'),
                      Item('z_offset'),
                      label='Observation',
                      show_border=True),
                HGroup(Item('x',
                            format_str='%.3f',
                            springy = True),
                       Item('y',
                            format_str='%.3f',
                            springy = True),
                       Item('z',
                            format_str='%.3f',
                            springy = True),
                       label='Reduced coordinates',
                       show_border=True),
                buttons=LiveButtons)
                      
def gui():
    """Run the interactive converter."""
#    import enthought.traits.ui.wx.view_application
#    enthought.traits.ui.wx.view_application.redirect_filename = 'cogo_wx.log'
#    Uncomment the next line to start interactive debugger.
#    from enthought.developer.helper.fbi import bp; bp()
    obs = Observation()
    obs.configure_traits()
    
def load_measurements(filename):
    """Load survey measurements from a text file."""
    try:
        reader = csv.reader(open(filename, 'rb'),
                            delimiter=' ',
                            skipinitialspace=True)
        obs_list = []
        base = BaseSetup()
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
                obs = Observation()
                obs.base = base
                obs.id = row[0]
                obs.horizontal_angle = avg_HAR(parse_angle(row[1]),
                                               parse_angle(row[4]),
                                               obs.id)
                obs.zenith_angle = avg_ZA(parse_angle(row[2]),
                                          parse_angle(row[5]),
                                          obs.id)
                obs.slope_distance = avg_slope_distance(float(row[3]),
                                                        float(row[6]),
                                                        obs.id)
                obs.z_offset = float(row[7])
                obs_list.append(obs)
    except:
        print "Processing file %s failed." % filename
        raise
    
    return base, obs_list

def save_coordinates(base, obs_list, out_filename):
    """Save the coordinates of a base station and a list of reduced target
    coordinates to a text file."""
    writer = csv.writer(open(out_filename, 'wb'), delimiter=' ')
    writer.writerow(['#id', 'x', 'y', 'z'])
    writer.writerow([base.id, base.x, base.y, base.z])
    for obs in obs_list:
        writer.writerow([obs.id, obs.x, obs.y, obs.z])
    
def parse_angle(angle_string):
    """ Parse a string with the format: degrees:minutes:seconds and return
    an instance of AngleDMS. """
    angle_dms = AngleDMS()
    angle_dms.degrees = int(angle_string.split(':')[0])
    angle_dms.minutes = int(angle_string.split(':')[1])
    angle_dms.seconds = float(angle_string.split(':')[2])
    return angle_dms

def avg_angles(angle_list):
    """Calculate the average angle from a list."""
    
    vectors = empty([len(angle_list), 2])
    for n_row, angle in enumerate(angle_list):
        vectors[n_row, :] = angle.geo_unit_vector
    avg_vector = vectors.sum(axis=0)
    avg_vector = avg_vector / norm(avg_vector)
    
    ref = [0, 1]
    if avg_vector[0] >= 0:
        return dd2dms(degrees(arccos(dot(avg_vector, ref))))
    else:
        return dd2dms(360 - degrees(arccos(dot(avg_vector, ref))))
    
def avg_HAR(direct_HAR, reverse_HAR, observation_id='', tol='0:0:30.0'):
    """ Average direct and reverse horizontal angle right observations and
    return an instance of AngleDMS. Print a warning if the difference between
    the observations exceeds the given tolerance. The tolerance is specified in
    arcseconds"""
    reverse = reverse_HAR.decimal_degrees + 180
    if reverse >= 360:
        reverse -= 360
    reverse = dd2dms(reverse)
    
    diff = dd2dms(abs(direct_HAR.decimal_degrees - reverse.decimal_degrees))
    if diff.decimal_degrees > 180:
        diff = dd2dms(360 - diff.decimal_degrees)
    d, m, s = tol.split(':')
    angle_tol = AngleDMS(degrees=int(d), minutes=int(m), seconds=float(s))
    if diff.decimal_degrees > angle_tol.decimal_degrees:
        print u'WARNING: Horizontal angle tolerance (%i\u00B0%i\'%.4f") exceeded.' \
               % (angle_tol.degrees, angle_tol.minutes, angle_tol.seconds)
        print u'%s HAR difference: %i\u00B0%i\'%.4f"\n' % (observation_id,
                                                     diff.degrees,
                                                     diff.minutes,
                                                     diff.seconds)
    return avg_angles([reverse, direct_HAR])

def avg_ZA(direct_ZA, reverse_ZA, observation_id='', tol='0:0:30.0'):
    """ Average direct and reverse zenith angle observations and return an
    instance of AngleDMS. Print a warning if the difference between the
    observations exceeds the given tolerance. The tolerance is specified in
    degrees:minutes:seconds"""
    reverse = 360 - reverse_ZA.decimal_degrees
    reverse = dd2dms(reverse)
    
    diff = dd2dms(abs(direct_ZA.decimal_degrees - reverse.decimal_degrees))
    d, m, s = tol.split(':')
    angle_tol = AngleDMS(degrees=int(d), minutes=int(m), seconds=float(s))
    if diff.decimal_degrees > angle_tol.decimal_degrees:
        print u'WARNING: Zenith angle tolerance (%i\u00B0%i\'%.4f") exceeded.' \
               % (angle_tol.degrees, angle_tol.minutes, angle_tol.seconds)
        print u'%s ZA difference: %i\u00B0%i\'%.4f"\n' % (observation_id,
                                                     diff.degrees,
                                                     diff.minutes,
                                                     diff.seconds)

    return avg_angles([reverse, direct_ZA])

def avg_slope_distance(direct_slope_distance, reverse_slope_distance,
                       observation_id='', tol=0.01):
    """Average direct and reverse slope distance observations and return a
    float. Print a warning if the difference between the observations exceeds
    the given tolerance."""
    diff = abs(direct_slope_distance - reverse_slope_distance)
    if diff > tol:
        print 'WARNING: Slope distance tolerance (%.4f) exceeded.' % tol
        print '%s S difference: %.4f\n' % (observation_id, diff)
    return mean([direct_slope_distance, reverse_slope_distance])

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

def save_gama(observations, out_file='/tmp/test.gkf'):
    """ Save measurements to an xml file for use with the GNU Gama network
    adjustment software.
    
    ***WARNING*** This function is not complete"""
    
    from lxml import etree
    
    gama_file = open(out_file, 'w')
    gama_file.write('<?xml version="1.0" ?>\n')
    gama_file.write('<!DOCTYPE gama-local\n')
    gama_file.write('  SYSTEM "http://www.gnu.org/software/gama/gama-local.dtd">\n\n')
    
    gama_local = etree.Element('gama-local')
    network = etree.SubElement(gama_local, 'network')
    network.set('axes-xy', 'en')
    network.set('angles', 'left-handed')
    description = etree.SubElement(network, 'description')
    description.text = 'Example gama input file.'
            
    points_observations = etree.SubElement(network, 'points-observations')
    points_observations.set('direction-stdev', '5')
    points_observations.set('angle-stdev', '5')
    points_observations.set('zenith-angle-stdev', '5')
    points_observations.set('distance-stdev', '3')
    
    coordinates = etree.SubElement(points_observations, 'coordinates')
    
    point = etree.SubElement(coordinates, 'point',
                             id='CLRS',
                             x='248362.371',
                             y='4275826.433',
                             z='1715.945',
                             fix='xyz')
    
    obs = etree.SubElement(points_observations, 'obs')
    obs.set('from', BASE.id)
    for o in observations:
        angle = etree.SubElement(obs, 'angle')
        angle.set('from', o.base.id)
        angle.set('bs', 'm1a')
        angle.set('fs', o.id)
        angle.set('val', '%s-%s-%.3f' % (o.horizontal_angle.degrees,
                                       o.horizontal_angle.minutes,
                                       o.horizontal_angle.seconds))
        angle.set('from_dh', str(o.base.z_offset))
        angle.set('bs_dh', str(o.z_offset))
        angle.set('fs_dh', str(o.z_offset))
        
        
        z_angle = etree.SubElement(obs, 'z-angle')
        z_angle.set('from', o.base.id)
        z_angle.set('to', o.id)
        z_angle.set('val', '%s-%s-%.3f' % (o.zenith_angle.degrees,
                                         o.zenith_angle.minutes,
                                         o.zenith_angle.seconds))
        z_angle.set('from_dh', str(o.base.z_offset))
        z_angle.set('to_dh', str(o.z_offset))
        
        
        s_distance = etree.SubElement(obs, 's-distance')
        s_distance.set('from', o.base.id)
        s_distance.set('to', o.id)
        s_distance.set('val', str(o.slope_distance))
        s_distance.set('from_dh', str(o.base.z_offset))
        s_distance.set('to_dh', str(o.z_offset))
    
    gama_xml = etree.ElementTree(gama_local)
    gama_xml.write(gama_file,
                      pretty_print=True)
if __name__ == "__main__":
    FILENAMES = get_filenames()
    if FILENAMES:

        for in_filename in FILENAMES:
            OUT_FILENAME = '_'.join(['coordinates', split(in_filename)[-1]])
            BASE, OBSERVATIONS = load_measurements(in_filename)
            save_coordinates(BASE, OBSERVATIONS, OUT_FILENAME)
            save_gama(OBSERVATIONS)

    else:
        gui()
