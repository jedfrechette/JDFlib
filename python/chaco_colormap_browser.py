from numpy import linspace, ones

from enthought.chaco.api import ArrayPlotData, Plot,  color_map_name_dict
from enthought.enable.component_editor import ComponentEditor
from enthought.traits.api import HasTraits, Array, Instance, Enum
from enthought.traits.ui.api import Item, View, Spring

class ImagePlot(HasTraits):

    plot = Instance(Plot)
    
    colormap = Enum(sorted(color_map_name_dict.keys()))
    
    data = Array

    traits_view = View(Item('colormap'),
                       Item('plot', editor=ComponentEditor(), show_label=False),
                       width=600, height=400,
                       title="Color Map")

    def __init__(self):
        # Create plot data.
        row = linspace(0, 1, 100)
        self.data = ones([10, 100]) * row
        plotdata = ArrayPlotData(imagedata = self.data)
        
        # Create a Plot and associate it with the PlotData
        plot = Plot(plotdata)
        # Create a line plot in the Plot
        plot.img_plot("imagedata", xbounds=(0,1),
                      colormap=color_map_name_dict[self.colormap])[0]
        plot.y_axis.visible =  False
        self.plot = plot
        self.plot.aspect_ratio = 5
    
    def _colormap_changed(self, new):
        colormap = color_map_name_dict[self.colormap]
        colormap = colormap(self.plot.color_mapper.range)
        self.plot.color_mapper = colormap
        self.plot.request_redraw()
        
if __name__ == "__main__":
    ImagePlot().configure_traits()