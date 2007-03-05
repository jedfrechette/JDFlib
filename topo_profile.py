#!/usr/bin/env python
""" Plot a topographic profile using points in a csv file."""

__author__ = "Jed Frechette (jedfrechette@gmail.com)"
__version__ = "0.1"
__date__ = "4 March 2007"

from optparse import OptionParser
from os import path
import ConfigParser
import geo_data
import pyx
import pylab

class Profile(geo_data.Collection):
    """A topographic profile."""
    
    def dist_from_0(self):
        """Calculate the distance of each point in the profile from the first
        point in the profile."""
        return [p.calc_distance(self[0].x, self[0].y, self[0].z) for p in self]
    
    def cum_dist(self):
        """Calculate the cumulative distance of each point from the start
        of the profile."""
        dist = []
        cum_dist = 0
        for n, p in enumerate(self):
            if n > 0:
                cum_dist += p.calc_distance(self[n - 1].x,
                                            self[n - 1].y,
                                            self[n - 1].z, )
                dist.append(cum_dist)
            else:
                dist.append(cum_dist)
        return dist
            
        

if __name__ == '__main__':
    # Setup command line options.
    parser = OptionParser()
    parser.add_option('-i', '--input', dest='input_file', default=None,
                      help='INPUT_FILE contains the data to be plotted\
                            (REQUIRED).',
                      metavar='INPUT_FILE')   
    parser.add_option('-c', '--config', dest='config_file', default=None,
                      help='CONFIG_FILE describes the format of the INPUT_FILE\
                            (REQUIRED).',
                      metavar='CONFIG_FILE')
    (opts, args) = parser.parse_args()
    if (opts.config_file == None) | (opts.input_file == None):
        parser.error('Both -i and -c are required.')
    
    # Read in the point data.
    config = ConfigParser.SafeConfigParser()
    config.read(opts.config_file)
    if config.get('config', 'type') != 'point':
        raise IOError, 'Only point data sets can be used to create profiles'
    profile = Profile()
    profile.from_pt_csv(opts.input_file, config)
    
    # Plot the profile.
    # FIXME: Scale the results to an appropriate range.
    x =profile.cum_dist()
#    x = [((18812 / profile.cum_dist()[-1]) * (pt)) / 1000
#         for pt in profile.cum_dist() if pt != 0]
    y = profile.value_list('z')
    print max(x)
    
#    c = pyx.canvas.canvas()
#    g = c.insert(pyx.graph.graphxy(width=25,
#                               x=pyx.graph.axis.linear(title='Distance along profile (km)'),
#                               y=pyx.graph.axis.linear(title='Elevation (m)')))
#    g.plot(pyx.graph.data.list(zip(x, y), x=1, y=2),
#           [pyx.graph.style.line([pyx.style.linewidth.Thin])])
#    
#    # TODO: Redo label generation so that it is not hardcoded.
#    g.finish()
#    label_cfg = ConfigParser.SafeConfigParser()
#    label_cfg.read('sites.cfg')
#    labels = geo_data.Collection()
#    labels.from_pt_csv('site_list.csv', label_cfg)
#    for l in labels:
#        x, y = g.pos(l.data['distance'] / 1000, l.z + 40)
#        g.text(x, y, l.data['Name'], [pyx.trafo.rotate(90),
#                                      pyx.text.valign.middle])
#    
#    g.writePDFfile('.'.join([path.splitext(opts.input_file)[0], 'pdf']))
    s_profile = geo_data.TimeSeries(x, y)
    s_profile.running_mean(11)
    fig = pylab.figure()
    prof = pylab.subplot(211)
    prof.plot(s_profile['11pt_x'], s_profile['11pt_avg'])
    prof.plot(x, y)
    prof.axis('tight')
    map = pylab.subplot(212)
    map.plot(profile.value_list('x'), profile.value_list('y'))
    map.axis('equal')
#    for pt_num in xrange(len(x)):
#        if pt_num % 10 == 0:
#            pylab.text(x[pt_num],
#                       y[pt_num],
#                       str(profile.value_list('pt_num')[pt_num]))
    pylab.show()
    
    print 'Success'
