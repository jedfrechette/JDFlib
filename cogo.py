#!/usr/bin/env python
"""Perform coordinate geometry calculations."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "4 February 2008"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

from enthought.traits.api import HasTraits, Button, Float
from enthought.traits.ui.api import View, Item
from scipy import arctan, cos, pi, sin, sqrt

class MeasuredPoint(HasTraits):
    """A measurement.
    
    zenith_angle    = Zenith angle.
    horizontal_angle_right   = Horizontal angle measured clockwise from the rear.
    slope_distance      = Slope distance."""
    zenith_angle = Float(90)
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
     
def deg2rad(angle_degree):
    """Convert an angle in degrees to radians."""
    return angle_degree * pi/180

def rad2deg(angle_radian):
    """Convert an angle in radians to degrees."""
    return angle_radian * 180/pi

def gui():
    """Run the interactive converter."""
    point = MeasuredPoint()
    point.configure_traits()
    
if __name__ == "__main__":
    gui()
