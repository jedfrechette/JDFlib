"""Provide base classes and functions for storing and proccessing data commonly
used by geoscientists."""

__author__ = "Jed Frechette (jedfrechette@gmail.com)"
__version__ = "0.1"
__date__ = "Aug 16, 2006"

from time_series import slopes, smooth
import ConfigParser
import csv
import scipy


class Point(object):
    """Storage for a 3D location and optional data associated with it."""
    def __init__(self, x, y, z, data=None):
        self.x = x
        self.y = y
        self.z = z
        if data != None:
            self.data = data
            
    def calc_distance(self, x, y, z):
        """Return the distance between the point and another x, y, z point."""
        return ((self.x - x)**2 + (self.y - y)**2 + (self.z - z)**2)**0.5
    
    
class Collection(list):
    """Store a collection of other data types (e.g. Points or Samples)."""
         
    def from_pt_csv(self, file_name, config_parser):
        """Create a collection of points from a csv file."""
        coords = {'x': None, 'y': None, 'z': None}
        floats = {}
        integers = {}
        strings = {}
        for col_num in xrange(config_parser.getint('config', 'n_col')):
            flt_name = try_config(config_parser, 'float', str(col_num))
            int_name = try_config(config_parser, 'integer', str(col_num))
            str_name = try_config(config_parser, 'string', str(col_num))
            
            if flt_name != None:
                floats[flt_name] = col_num
            if int_name != None:
                integers[int_name] = col_num
            if str_name != None:
                strings[str_name] = col_num
               
        # Open the input file and read in the data line by line. Throw out any
        # lines that do not contain numbers.
        try:
            input_file = open(file_name)
            try:
                reader = csv.reader(input_file,
                                    delimiter=eval(config_parser.get('config',
                                                                     'delimiter')),
                                    skipinitialspace=True)
                for n_row, row in enumerate(reader):
                    attributes = {}
                    try:
                        for f in floats:
                            if f in coords:
                                coords[f] = float(row[floats[f]])
                            else:
                                attributes[f] = float(row[floats[f]])
                        for i in integers:
                            if i in coords:
                                coords[i] = int(row[integers[i]])
                            else:
                                attributes[i] = int(row[integers[i]])
                        for s in strings:
                            attributes[s] = row[strings[s]]
                    except ValueError:
                        print "Bad value skipping row: " + str(n_row)
                        continue
                    
                    try:
                        for key in coords:
                            if key == None:
                                raise KeyError
                    except KeyError:
                        print 'Columns for x, y, and z must be specified.'
                    self.append(Point(coords['x'],
                                      coords['y'],
                                      coords['z'],
                                      attributes))
            finally:
                input_file.close()
        except IOError:
            print "Opening file '" + file_name +"' failed."
        self.pt_keys = {'coordinates': coords.keys(),
                        'floats': floats.keys(),
                        'integers': integers.keys(),
                        'strings': strings.keys()}
    
    def value_list(self, value):
        """Return a list constructed by extracting the passed value from every
        member of the collection."""
        try:
            return [eval('.'.join(['m', value])) for m in self]
        except AttributeError:
            return [m.data[value] for m in self]
        

class TimeSeries(dict):
    """2D timeseries data."""
    def __init__(self, x=None, y=None):
        super(TimeSeries, self).__init__()
        if x == None:
            self['x'] = []
        else:
            self['x'] = x
        if y == None:
            self['y'] = []
        else:
            self['y'] = y
        
    def from_csv(self,
                 file_name,
                 x_col=0,
                 y_col=1,
                 delimiter=' ',
                 start_row=None,
                 end_row=None):
        """Build a time series from a csv file."""
        # Open the input file and read in the data line by line. Throw out any
        # lines that do not contain numbers.
        if start_row == None:
            start_row = 0
        if end_row == None:
            end_row = len(open(file_name, 'rU').readlines())
        try:
            input_file = open(file_name)
            try:
                reader = csv.reader(input_file,
                                    delimiter=delimiter,
                                    skipinitialspace=True)
                for n_row, row in enumerate(reader):
                    if start_row <= n_row <= end_row:
                        try:
                            if row == []:
                                raise ValueError
                            x = float(row[x_col])
                            y = float(row[y_col])
                        except ValueError:
                            print "Bad value skipping row: " + str(n_row)
                            continue
                        self['x'].append(x)
                        self['y'].append(y)
            finally:
                input_file.close()
        except IOError:
            print "Opening file '" + file_name +"' failed."
    
    def dy_dx(self, x=None, y=None):
        """Calculate an estimate of the slope using the slopes method."""
        if x == None:
            x = self['x']
        if y == None:
            y = self['y']
        self['yp'] = slopes(x, y)
    
    def running_mean(self, n, x=None, y=None):
        """Calculate a moving average using a 'n' point window. Averages are
        not calculated for the tails of the series where a 'n' point window
        can't be achieved. This code assumes that x values are evenly spaced."""
        if x == None:
            x = self['x']
        if y == None:
            y = self['y']
        self[str(n) + 'pt_avg'], self[str(n) + 'pt_x'] = smooth(y, n, x, )

def try_config(config_parser, section, key):
    """Try to read a key from a specified section of a config file or fail
    silently."""
    try:
        return config_parser.get(section, key)
    except ConfigParser.NoOptionError:
        pass
    
    

if __name__ == '__main__':
    print "This module is not intended for standalone use."