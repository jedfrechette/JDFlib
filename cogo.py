#!/usr/bin/env python
"""Perform coordinate geometry calculations."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "15 February 2008"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

from enthought.traits.api import HasTraits, Button, BaseFloat, BaseInt, \
    Float, Property, cached_property
from enthought.traits.ui.api import View, Item
from scipy import arctan, cos, pi, sin, sqrt
import logging

class DegreeInt(BaseInt):
    info_text = 'an integer >= 0 and < 360'
    def validate(self, object, name, value):
        value = super(DegreeInt, self).validate(object, name, value)
        if 0 <= value < 360:
            return value
        self.error(object, name, value)
        
class MinuteInt(BaseInt):
    info_text = 'an integer >= 0 and < 60'
    def validate(self, object, name, value):
        value = super(MinuteInt, self).validate(object, name, value)
        if 0 <= value < 60:
            return value
        self.error(object, name, value)

class SecondFloat(BaseFloat):
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
        return self.decimal_degrees * pi/180

class MeasuredPoint(HasTraits):
    """A measurement.
    
    zenith_angle    = Zenith angle.
    horizontal_angle_right   = Horizontal angle measured clockwise from the rear.
    slope_distance      = Slope distance."""
    zenith_angle = Float(90.0)
    horizontal_angle_right = Float()
    slope_distance = Float()
    
    x = Float()
    y = Float()
    z = Float()
    
    calculate_xyz = Button()
    calculate_angles = Button()
    
    def _calculate_xyz_fired(self):
        self.z = self.slope_distance * cos(deg2rad(self.zenith_angle))
        h_dist = self.slope_distance * sin(deg2rad(self.zenith_angle))
        self.x = sin(deg2rad(self.horizontal_angle_right)) * h_dist
        self.y = cos(deg2rad(self.horizontal_angle_right)) * h_dist
    
    def _calculate_angles_fired(self):
        h_dist = sqrt(self.x**2 + self.y**2)
        self.slope_distance = sqrt(h_dist**2 + self.z**2)
        self.horizontal_angle_right = rad2deg(arctan(self.x / self.y))
        self.zenith_angle = rad2deg(arctan(h_dist / self.z))
    
    view = View('zenith_angle',
                'horizontal_angle_right',
                'slope_distance',
                'x',
                'y',
                'z',
                Item('calculate_xyz', show_label=False),
                Item('calculate_angles', show_label=False))

class MainWindow(HasTraits):
    pass
     
def deg2rad(angle_degree):
    """Convert an angle in degrees to radians."""
    return angle_degree * pi/180

def rad2deg(angle_radian):
    """Convert an angle in radians to degrees."""
    return angle_radian * 180/pi

def gui():
    """Run the interactive converter."""
    
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(file('cogo.log', 'w')))
    logger.setLevel(logging.DEBUG)
    
#    from enthought.developer.helper.fbi import bp; bp()
    
    angle = AngleDMS()
    angle.configure_traits()
#    point = MeasuredPoint()
#    point.configure_traits()
    
if __name__ == "__main__":
    gui()
