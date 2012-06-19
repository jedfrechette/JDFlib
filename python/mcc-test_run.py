#!/usr/bin/env python

"""Test spacing and threshold parameters for mcc-lidar.

This program runs mcc-lidar using the specified parameters, then uses
gdal to generate a slope map that can be used to evaluate the
effectiveness of the parameters. All steps, including the time required for
the mcc-lidar run are recorded in a log file. All output files will be named
based on the name of the input dataset and the date and time the program was
run.
"""

__author__ = "Jed Frechette <jedfrechette@gmail.com>"
__date__ = "17 June 2012"

import argparse
from datetime import datetime
from os import path, times
from subprocess import check_output, STDOUT

def parse_cmd():
    """Parse the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file', type=file)
    parser.add_argument('-s','--spacing', dest='spacing', type=float,
                       required=True, help='spacing for scale domain 2')
    parser.add_argument('-t', '--threshold', dest='threshold', type=float,
                       required=True, help='curvature threshold')
    parser.add_argument('-c', '--cell_size', dest='cell_size', type=float,
                       required=True, help='cell size of output rasters')
    
    return parser.parse_args()

def run_mcc(input_file, base_name, spacing, threshold, cell_size):
    """Run mcc-lidar."""
    start_time = times()
    mcc_output = check_output(['mcc-lidar',
                               '-s', '%f' % spacing,
                               '-t', '%f' % threshold,
                               '-c', '%f' % cell_size,
                               input_file,
                               '%s.csv' % base_name,
                               '%s.asc' % base_name])
    end_time = times()
    start_time = start_time[2] + start_time[3]
    end_time = end_time[2] +end_time[3]
    return mcc_output, end_time-start_time

def make_slope_map(base_name):
    """Make a slope map."""
    slope_output = check_output(['gdaldem',
                                 'slope',
                                 '%s.asc' % base_name,
                                 '%s-slope.tif' % base_name])
    
def main():
    args = parse_cmd()
    start_time = datetime.now()
    base_name = '-'.join((path.splitext(path.split(args.input_file.name)[1])[0],
                          start_time.strftime('%Y%m%d%H%M%S')))
    log_handle = open('%s.log' % base_name, 'wb')
    log_handle.writelines(['='*80, '\n',
                           'mcc-lidar %s\n' % start_time.isoformat(),
                           '='*80, '\n',
                           '\n',
                           ':spacing: %f\n' % args.spacing,
                           ':threshold: %f\n' % args.threshold])
    
    output, process_time = run_mcc(args.input_file.name, base_name,
                                   args.spacing, args.threshold, args.cell_size)
    log_handle.writelines([':process time: %f\n' % process_time,
                           '\n',
                           '-'*80,
                           '\n'])
    log_handle.write(output)
    
    make_slope_map(base_name)
    log_handle.close()
    print "Log saved to: %s.log" % base_name
    
if __name__ == '__main__':
    main()
