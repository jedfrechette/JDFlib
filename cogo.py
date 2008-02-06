#!/usr/bin/env python
"""Perform coordinate geometry calculations."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "5 February 2008"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

from types import IntType, FloatType
from enthought.traits.api import HasTraits, Button, Float, Dict, Int
from enthought.traits.ui.api import View, Item
from scipy import arctan, cos, pi, sin, sqrt
import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(file('cogo.log', 'w')))
logger.setLevel(logging.DEBUG)

#class PositiveInt(Int):
#    def validate(self, object, name, value):
#        info_text = 'an integer >= 0'
#        super(PositiveInt, self).validate(object, name, value)
#        if value >= 0:
#            return value 
#        self.error(object, name, value)
#    
#class PositiveFloat(Float):
#    def validate(self, object, name, value):
#        info_text = 'a float >= 0'
#        super(PositiveFloat, self).validate(object, name, value)
#        print value
#        if value >= 0:
#            return value 
#        self.error(object, name, value)

class Angle(HasTraits):
    """An angle in decimal degrees or degrees, minutes seconds."""
    decimal_degrees = Float(0.0)
#    dms = Dict()
    degrees = Int()
    minutes = Int()
    seconds = Float()
    radians = Float()
    
    def _decimal_degrees_changed(self):
        self.radians = self.decimal_degrees * pi/180
        self.degrees = int(self.decimal_degrees)
        self.minutes = int(60 * (self.decimal_degrees - self.degrees))
        self.seconds = 60 * (60 * (self.decimal_degrees- self.degrees)
                             - self.minutes)
        
#    def _degrees_changed(self):
#        self.decimal_degrees = self.degrees + self.minutes/60.0 \
#                               + self.seconds/3600
#    
#    def _minutes_changed(self):
#        self.decimal_degrees = self.degrees + self.minutes/60.0 \
#                               + self.seconds/3600
#
#    def _seconds_changed(self):
#        self.decimal_degrees = self.degrees + self.minutes/60.0 \
#                               + self.seconds/3600
#    
#    def _radians_changed(self):
#        self.decimal_degrees = self.radians * 180/pi

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
    angle = Angle()
    angle.configure_traits()
#    point = MeasuredPoint()
#    point.configure_traits()
    
if __name__ == "__main__":
    gui()
