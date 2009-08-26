#!/usr/bin/env python
"""Plot utility usage and weather."""

__author__ = "Jed Frechette <jedfrechette@gmail.com>"
__date__ = "10 February 2009"
__version__ = "0.1"
__license__ = "MIT <http://opensource.org/licenses/mit-license.php>"

# Standard library imports.
from glob import glob
from optparse import OptionParser
from os import name, path
from time import localtime
from urllib import urlopen
from StringIO import StringIO

# Numpy imports
from numpy import loadtxt
from numpy.ma import masked_less

# TimeSeries imports
from scikits.timeseries import Date, time_series, tsfromtxt
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
    y, m, d = packed_date.split('-')
    return Date('D',
                year = int(y),
                month = int(m),
                day = int(d))

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
        accum_precip += precip
        csv_data.append(' '.join([row[0].strip(),
                                  row[1].strip(),
                                  row[3].strip(),
                                  str(precip)]))
    csv_data = '\n'.join(csv_data)
    climate = tsfromtxt(StringIO(csv_data), dtype='float', datecols=0,
                        missing='-999', dateconverter=parse_nmsu_date)
    return climate
    
if __name__ == "__main__":
    for IN_FILENAME in get_filenames():
        data = loadtxt(IN_FILENAME, delimiter=',', usecols=[1, 2, 3])
        data_file = open(IN_FILENAME)
        dates = []
        for row in data_file:
            if row[0] == '#':
                continue
            dates.append(row.split(',')[0])
        #dates = data[:, 0].astype(int).tolist()
        dates = [parse_date(str(d)) for d in dates]
        ELECTRIC = time_series(masked_less(data[:, 0], 0), dates)
        GAS = time_series(masked_less(data[:, 1], 0), dates)
        WATER = time_series(masked_less(data[:, 2], 0), dates)
        START = dates[0]
        END = dates[-1]
        CLIMATE = get_nm_climate(start_date='%i%.2i%.2i' % (START.year,
                                                            START.month,
                                                            START.day),
                                 end_date='%i%.2i%.2i' % (END.year,
                                                          END.month,
                                                          END.day))
        CLIMATE.tofile('/tmp/test.txt')
        MAX_TEMP, MIN_TEMP, ACCUM_PRECIP = CLIMATE.split()
        
        FIG = tpl.tsfigure(figsize=(10, 7))
        FIG.subplots_adjust(hspace = 0.1)
        
        GAS_PLOT = FIG.add_tsplot(313)
        GAS_PLOT.tsplot(backward_fill(GAS), zorder=20)
        GAS_PLOT.set_ylabel('Gas usage, therms')
        GAS_PLOT.grid(linestyle='-', color='0.9', zorder=0)
        TEMP_PLOT = GAS_PLOT.add_yaxis(position='right')
        TEMP_PLOT.tsplot(MIN_TEMP, color='0.5', zorder=10)
        TEMP_PLOT.tsplot(MAX_TEMP, color='0.5', zorder=10)
        TEMP_PLOT.set_ylabel(u'Temperature range, \u2109F')
        
        WATER_PLOT = FIG.add_tsplot(311, sharex=GAS_PLOT)
        WATER_PLOT.tsplot(backward_fill(WATER*748), zorder=20)
        WATER_PLOT.grid(linestyle='-', color='0.9', zorder=1)
        WATER_PLOT.set_xticklabels(WATER_PLOT.get_xticklabels(),
                                   visible=False)
        WATER_PLOT.set_ylabel('Water usage, gal.')
        WATER_PLOT.set_title('Utility usage for 1613 Columbia Dr. SE, ' \
                             'Albuquerque, NM\n' \
                             'Usage is given per billing period (~30 days).\n' \
                             'Daily weather data from Albuquerque International ' \
                             'Airport (KABQ)')
        PRECIP_PLOT = WATER_PLOT.add_yaxis(position='right')
        PRECIP_PLOT.tsplot(ACCUM_PRECIP, color='0.5', zorder=10)
        PRECIP_PLOT.set_ylabel('Precipitation, in.')
        PRECIP_PLOT.set_xticklabels(PRECIP_PLOT.get_xticklabels(),
                                    visible=False)
       
        #TODO: Prevent the y tick labels from overlapping the other plots.
        #TODO: Find local station with solar radiation (City of Albuquerque
        #      stations from NMSU supposedly have the data but may have been
        #      discontinued.)
        ELECTRIC_PLOT = FIG.add_tsplot(312, sharex=GAS_PLOT)
        ELECTRIC_PLOT.tsplot(backward_fill(ELECTRIC), zorder=10)
        ELECTRIC_PLOT.grid(linestyle='-', color='0.9', zorder=1)
        ELECTRIC_PLOT.set_xticklabels(ELECTRIC_PLOT.get_xticklabels(),
                                      visible=False)
        ELECTRIC_PLOT.set_ylabel('Electric usage, kWh')
        
        GAS_PLOT.set_datelimits(start_date='2004-09-01')
        GAS_PLOT.format_dateaxis()
        
        PDF_FILENAME = '.'.join([path.splitext(IN_FILENAME)[0], 'pdf'])
        FIG.savefig(PDF_FILENAME,)
        
    tpl.show()
