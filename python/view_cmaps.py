#!/usr/bin/env python
"""Visualize the colormaps available from Matplotlib."""

__author__ = 'Jed Frechette <jedfrechette@gmail.com>'
__date__ = '10 August 2007'

from scipy import arange, ceil, ones, vstack
import pylab

bar_height = 10
bar_width = 100
bar = ones((bar_height, bar_width)) * arange(bar_width)

fig = pylab.figure()

n_cols = 3
n_rows = ceil(len(pylab.cm.cmapnames) / float(n_cols))
plot_num = 1

for cm_name in pylab.cm.cmapnames:
    cmap = '.'.join(('pylab', 'cm', cm_name))
    plt = fig.add_subplot(n_rows, n_cols, plot_num)
    plt.imshow(bar, cmap=eval(cmap))
    plt.set_title(cm_name, verticalalignment='center', position=(.5, .5))
    plt.set_axis_off()
    plot_num += 1
pylab.show()
