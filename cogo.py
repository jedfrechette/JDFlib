#!/usr/bin/env python
"""Perform coordinate geometry calculations."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "11 February 2008"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

from enthought.traits.api import HasTraits, Button, BaseFloat, BaseInt, \
    Float
from enthought.traits.ui.api import View, Item
from scipy import arctan, ceil, cos, floor, pi, sin, sqrt
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
    """An angle in ddegrees, minutes seconds."""
    degrees = DegreeInt
    minutes = MinuteInt
    seconds = SecondFloat
    __decimal_degrees = Float
    __radians = Float
    
    def _dd2rad(self):
        """Convert decimal degrees to radians."""
        self.__radians = self.__decimal_degrees * pi/180
        
    def _dms2dd(self):
        """Convert degrees, minutes, seconds to decimal degrees."""
        self.__decimal_degrees = self.degrees + self.minutes/60.0 \
                                 + self.seconds/3600.0
            
    def _anytrait_changed(self, name):
        if name in ('degrees', 'minutes', 'seconds'):
            self._dms2dd()
            self._dd2rad()


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
