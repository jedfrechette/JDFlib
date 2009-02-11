#!/usr/bin/env python
"""Plot utility usage and weather."""

__author__ = "Jed Frechette <jedfrechette@gmail.com>"
__date__ = "10 February 2009"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

# Standard library imports.
from glob import glob
from optparse import OptionParser
from os import name
from time import localtime
from urllib import urlopen
from StringIO import StringIO

# Numpy imports
from numpy import median

# Matplotlib imports
from matplotlib.pyplot import show

# TimeSeries imports
from scikits.timeseries import Date, tsfromtxt
from scikits.timeseries.lib.interpolate import backward_fill
import scikits.timeseries.lib.plotlib as tpl

def get_filenames():
    """Return a list of filenames to process."""
    parser = OptionParser(usage='%prog INPUT_FILES',
                          description=' '.join(__doc__.split()),
                          version=__version__)
    (opts, args) = parser.parse_args()
    if name == 'nt':
        args = glob(args[0])
    return args

def parse_date(packed_date):
    packed_date = str(packed_date)
    return Date('D',
                year = int(packed_date[:4]),
                month = int(packed_date[4:6]),
                day = int(packed_date[6:]))

def parse_nmsu_date(packed_date):
    m, d, y = packed_date.split('/')
    date= Date('D',
                year=int('20%s' % y),
                month=int(m),
                day=int(d))
    return date

def get_nm_climate(station='kabq', start_date = '20040101', end_date = 'today'):
    if end_date == 'today':
        end_date = localtime()
        end_date = '%i%.2i%.2i' % (end_date.tm_year,
                               end_date.tm_mon,
                               end_date.tm_mday)
    url = 'http://weather.nmsu.edu/cgi-shl/cns/stat.pl?station=%s&type=daily' \
          '&smonth=%s&sday=%s&syear=%s' \
          '&emonth=%s&eday=%s&eyear=%s' % (station,
                                           start_date[4:6],
                                           start_date[6:],
                                           start_date[2:4],
                                           end_date[4:6],
                                           end_date[6:],
                                           end_date[2:4])
    data = urlopen(url)
    data = data.readlines()
    csv_data = []
    accum_precip = 0.0
    for row in data[9:-5]:
        row = row.split('|')
        precip = float(row[19]) - accum_precip
        if precip < 0:
            precip = 0
            accum_precip = 0
        print row[0], row[19], accum_precip, precip
        accum_precip += precip
        csv_data.append(' '.join([row[0].strip(),
                                  row[1].strip(),
                                  row[3].strip(),
                                  str(precip)]))
    csv_data = '\n'.join(csv_data)
    climate = tsfromtxt(StringIO(csv_data), dtype='float', datecols=0,
                        dateconverter=parse_nmsu_date)
    return climate
    
if __name__ == "__main__":
    for in_filename in get_filenames():
        USAGE = tsfromtxt(in_filename, delimiter=',', datecols=0,
                          skiprows=6, dateconverter=parse_date)
        ELECTRIC, GAS, WATER = USAGE.split()
        START = USAGE.dates[0]
        END = USAGE.dates[-1]
        CLIMATE = get_nm_climate(start_date='%i%.2i%.2i' % (START.year,
                                                            START.month,
                                                            START.day),
                                 end_date='%i%.2i%.2i' % (END.year,
                                                          END.month,
                                                          END.day))
        CLIMATE.tofile('/tmp/test.txt')
        MAX_TEMP, MIN_TEMP, ACCUM_PRECIP = CLIMATE.split()
        
        FIG = tpl.tsfigure()
        
        FSP = FIG.add_tsplot(311)
        FSP.tsplot(backward_fill(WATER*748))
        FSP_RIGHT = FSP.add_yaxis(position='right')
        FSP_RIGHT.tsplot(ACCUM_PRECIP)
                   
        FSP = FIG.add_tsplot(312)
        FSP.tsplot(backward_fill(ELECTRIC))
        
        FSP = FIG.add_tsplot(313)
        FSP.tsplot(backward_fill(GAS))
        FSP_RIGHT = FSP.add_yaxis(position='right')
        FSP_RIGHT.tsplot(MIN_TEMP)
        FSP_RIGHT.tsplot(MAX_TEMP)
    show()