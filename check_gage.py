#!/usr/bin/env python
"""Check a USGS gage and send out an email if a threshold is exceeded."""

__author__ = 'Jed Frechette <jdfrech@unm.edu>'
__version__ = '0.1'
__date__ = '10 August 2007'

from os import popen
from textwrap import wrap
from urllib import urlopen
import csv

def check_gage(site_no, period=1):
    """Check a USGS gage and report basic discharge info.
    
    Arguments:
    site_no        The number of the site to check.
    period         The number of preceeding days to get data for (1-31)
    
    Return:
    time_stamp     Tuple listing the dates and times of measurements.
    discharge      Tuple listing measured discharges.
    site_name      The complete name for the site.
    url            A link to a graph of discharge for the last period + 1
                   days."""
    url = '&'.join(['http://waterdata.usgs.gov/nm/nwis/uv?cb_00060=on', 
                    'format=rdb', 
                    'period=%s' % period, 
                    'site_no=%s' % site_no])
    data = urlopen(url)
    time_stamp = []
    discharge = []
    n_headers = 0
    try:
        reader = csv.reader(data, delimiter='\t')
        for idx, row in enumerate(reader):
            # Skip empty rows.
            if not row:
                continue
            # Process the headers.
            elif row[0][0] == '#':
                n_headers += 1
                if idx == 14:
                    site_name = row[0][1:].strip()
                elif row[0][-32:] == 'Discharge, cubic feet per second':
                    dd_discharge = row[0][5:7]
            # Get column names.
            elif idx == n_headers:
                cols = dict(zip(row, range(len(row))))
            #Process the data.
            elif idx >= n_headers + 2:
                try:
                    d_int = int(row[cols['%s_00060' % dd_discharge]])
                except ValueError:
                    continue
                time_stamp.append(row[cols['datetime']])
                discharge.append(d_int) 
    finally:
        data.close()
    return tuple(time_stamp), tuple(discharge), \
            site_name, \
            url.replace('rdb', 'gif_default').replace('period=%s' % (period), 
                                                      'period=%s' % (period+1))
        
        
def median(m):
    """median(m) returns a median of m.
    """
    m = list(m)
    m.sort()
    index = int(len(m)/2)
    if len(m) % 2 == 1:
        return m[index]
    else:
        return (m[index-1] + m[index])/2.0 
        
            
if __name__ == '__main__':
    max_percent = 150
    gage_list = ('08329928', '08330000')
    subscribers = ('jedfrechette@gmail.com',
                   'jcoonrod@unm.edu',
                   'tfw@unm.edu',
                   'jcstorm@unm.edu')
    subject = '"%s percent of median discharge exceeded."' % max_percent
    error = ''
    body = []
    
    for gage in gage_list:
        try:
            date_time, q, site, graph_url = check_gage(gage)
        except:
            error = '\n'.join([error, 'Unable to get data for gage %s' % gage])
            continue
            
        if not q:
            continue
        elif max(q) > (max_percent / 100.0) * median(q):
            percent = 100.0 * max(q) / median(q)
            for ii, val in enumerate(q):
                if q[ii] == max(q):
                    time_max = date_time[ii]
            para = wrap('A maximum discharge of %s cfs was first recorded ' \
                        'by station %s at %s. This discharge was %i percent ' \
                        'of the median discharge between ' \
                        '%s and %s.' % (max(q), 
                                        site, time_max, percent, 
                                        date_time[0], date_time[-1]))
            para.append(graph_url)
            body.append('\n'.join(para))
            
    if body:
        # Uncomment for debugging or when running on a system without 'mail'.
#        print body
        popen('mail -s %s %s' % (subject, ' '.join(subscribers)), 
              'w').write('\n\n'.join(body))
    if error:
        # Uncomment for debugging or when running on a system without 'mail'.
#        print error
        popen('mail -s %s %s' % ('check_gage.py error', 
                                 subscribers[0]), 'w').write(error)
