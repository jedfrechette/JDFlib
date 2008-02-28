#!/usr/bin/env python
"""Perform coordinate geometry calculations."""

__author__ = "Jed Frechette <jdfrech@unm.edu>"
__date__ = "27 February 2008"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

from enthought.traits.api import BaseFloat, BaseInt, Float, HasTraits, \
    Instance, Property, cached_property
from enthought.traits.ui.api import View, Group, HGroup, Item
from enthought.traits.ui.menu import LiveButtons
from scipy import cos, pi, sin

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
        return self.decimal_degrees * pi/180
    
    view = View(HGroup(Item('degrees'), Item('minutes'), Item('seconds')))

class BaseStation(HasTraits):
    """A station at the origin of a survey."""
    northing = Float
    easting = Float
    elevation = Float
    elevation_offset = Float
    
    view = View(Item('northing'),
                Item('easting'),
                HGroup(Item('elevation'), Item('elevation_offset')))
    
class TargetStation(HasTraits):
    """A station with coordinates calulated relative to a BaseStation."""
    base = Instance(BaseStation, kw={'northing': 0,
                                     'easting': 0,
                                     'elevation': 0,
                                     'elevation_offset': 0})
    zenith_angle = Instance(AngleDMS, kw={'degrees': 90,
                                          'minutes': 0,
                                          'seconds': 0})
    horizontal_angle = Instance(AngleDMS, kw={'degrees': 0,
                                              'minutes': 0,
                                              'seconds': 0})
    horizontal_angle_offset = Instance(AngleDMS, kw={'degrees': 0,
                                                     'minutes': 0,
                                                     'seconds': 0})
    elevation_offset = Float
    slope_distance = Float
    horizontal_distance = Property(depends_on='zenith_angle.radians, \
                                               horizontal_angle.radians, \
                                               slope_distance')
    vertical_distance = Property(depends_on='zenith_angle.radians, \
                                             horizontal_angle.radians, \
                                             slope_distance')
    northing = Property(depends_on='base.northing, \
                                    zenith_angle.radians, \
                                    horizontal_angle.radians, \
                                    horizontal_angle_offset.radians,\
                                    slope_distance, \
                                    elevation_offset')
    easting = Property(depends_on='base.easting, \
                                   zenith_angle.radians, \
                                   horizontal_angle.radians, \
                                   horizontal_angle_offset.radians, \
                                   slope_distance, \
                                   elevation_offset')
    elevation = Property(depends_on='base.elevation, \
                                     base.elevation_offset, \
                                     zenith_angle.radians, \
                                     horizontal_angle.radians, \
                                     horizontal_angle_offset.radians, \
                                     slope_distance, \
                                     elevation_offset')
    
    @cached_property
    def _get_horizontal_distance(self):
        return self.slope_distance * sin(self.zenith_angle.radians)
    
    @cached_property
    def _get_vertical_distance(self):
        return self.slope_distance * cos(self.zenith_angle.radians)
    
    @cached_property
    def _get_northing(self):
        return cos(self.horizontal_angle.radians
                   + self.horizontal_angle_offset.radians) \
               * self.horizontal_distance + self.base.northing
    
    @cached_property
    def _get_easting(self):
        return sin(self.horizontal_angle.radians
                   + self.horizontal_angle_offset.radians) \
               * self.horizontal_distance + self.base.easting
    
    @cached_property
    def _get_elevation(self):
        return self.slope_distance * cos(self.zenith_angle.radians) \
               + self.base.elevation \
               + self.base.elevation_offset - self.elevation_offset
    
    view = View(Item('base', style='custom'),
                Group(Item('horizontal_angle', style='custom'),
                      Item('horizontal_angle_offset', style='custom'),
                      Item('zenith_angle', style='custom'),
                      Item('slope_distance'),
                      label='Shot to target',
                      show_border=True),
                Group(Item('elevation_offset'),
                      HGroup(Item('northing',
                                  format_str='%.3f',
                                  springy = True),
                             Item('easting',
                                  format_str='%.3f',
                                  springy = True),
                             Item('elevation',
                                  format_str='%.3f',
                                  springy = True))),
                buttons=LiveButtons)
                      
def gui():
    """Run the interactive converter."""
    import enthought.traits.ui.wx.view_application
    enthought.traits.ui.wx.view_application.redirect_filename = 'cogo_wx.log'
#    Uncomment the next line to start interactive debugger.
#    from enthought.developer.helper.fbi import bp; bp()
    target = TargetStation()
    target.configure_traits()
    
if __name__ == "__main__":
    gui()