"""Provide base classes and functions for working with times series."""

__author__ = "Jed Frechette (jedfrechette@gmail.com)"
__version__ = "0.1"
__date__ = "21 September 2006"

from __future__ import division
from scipy import asarray, median, std, zeros
from itertools import islice, tee, izip
from collections import deque

def bp2cal(year, year_0=1950):
    """Convert a year specified as calendar years BP to years BC/AD, where
    years AD are positive and years BC are negative."""
    if year > 1950:
        return year_0 - year
    else:
        # There is no year 0.
        return year_0 - year - 1

def cal2bp(year, year_0=1950):
    """Convert a year, specified in calendar years, where years AD are positive
    and years BC are negative to years calendar years BP. By default years BP
    are relative to 1950."""
    if year > 0:
        return year_0 - year
    else:
        # There is no year 0.
        return year_0 - year - 1
    

def window(items, n):
    """Generator that returns an 'n' point window from 'items'."""
    it = iter(items)
    w = deque(islice(it, n-1))
    for item in it:
        w.append(item)
        yield w # for a robust implementation: yield tuple(w)
        w.popleft()
        
def moving_mean(items, n):
    """Generator that returns a 'n' point moving average from 'items'. Averages
    are not calculated for the tails of the series where a 'n' point window
    can't be achieved."""
    first_items, last_items = tee(items)
    accu = sum(islice(last_items, n-1))
    for first, last in izip(first_items, last_items):
        accu += last
        yield accu/n
        accu -= first
                
def moving_median(items, n):
    """Generator that returns a 'n' point moving median from 'items'. Medians
    are not calculated for the tails of the series where a 'n' point window
    can't be achieved."""
    for w in window(items, n):
        yield median(w)
    
def moving_std(items, n):
    """Generator that returns a 'n' point moving standard deviation from
    'items'. The standard deviation is not calculated for the tails of the
    series where a 'n' point window can't be achieved."""
    for w in window(items, n):
        yield std(w)
        
def slopes(x, y):
    """
    SLOPES calculate the slope y'(x) Given data vectors X and Y SLOPES
    calculates Y'(X), i.e the slope of a curve Y(X). The slope is
    estimated using the slope obtained from that of a parabola through
    any three consecutive points.

    This method should be superior to that described in the appendix
    of A CONSISTENTLY WELL BEHAVED METHOD OF INTERPOLATION by Russel
    W. Stineman (Creative Computing July 1980) in at least one aspect:

    Circles for interpolation demand a known aspect ratio between x-
    and y-values.  For many functions, however, the abscissa are given
    in different dimensions, so an aspect ratio is completely
    arbitrary.
    
    The parabola method gives very similar results to the circle
    method for most regular cases but behaves much better in special
    cases

    Norbert Nemec, Institute of Theoretical Physics, University or
    Regensburg, April 2006 Norbert.Nemec at physik.uni-regensburg.de

    (inspired by a original implementation by Halldor Bjornsson,
    Icelandic Meteorological Office, March 2006 halldor at vedur.is)
    """
    # Cast key variables as float.
    x = asarray(x, 'd')
    y = asarray(y, 'd')

    yp = zeros(y.shape, 'd')

    dx = x[1:] - x[:-1]
    dy = y[1:] - y[:-1]
    dydx = dy/dx
    yp[1:-1] = (dydx[:-1] * dx[1:] + dydx[1:] * dx[:-1])/(dx[1:] + dx[:-1])
    yp[0] = 2.0 * dy[0]/dx[0] - yp[1]
    yp[-1] = 2.0 * dy[-1]/dx[-1] - yp[-2]
    return yp

def smooth(y, n, x=None, method='mean'):
    """Smooth a time series using the specified method with a 'n' point moving
    window. By default a running mean will be used. Valid methods are 'mean'
    and 'median'. Smoothed values are not calculated for the tails of the
    series where a 'n' point window can't be achieved. If a 'x' list is
    specified a new list will be returned that has had the tails trimmed so
    that it is the same length as the smoothed list that is returned."""
    methods = {'mean': moving_mean(y, n),
               'median': moving_median(y, n)}
    y_smooth = [y_s for y_s in methods[method]]
    if x:
        x_trimmed = x[int(n/2) : int(n/-2)]
        return y_smooth, x_trimmed
    else:
        return y_smooth