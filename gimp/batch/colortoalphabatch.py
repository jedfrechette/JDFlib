from glob import glob
from gimp import pdb

def batch_colortoalpha():
    for filename in glob('*.png'):
        image = pdb.gimp_file_load (filename, filename)
        # put your batch processing commands here.
        # for example
        #
        # pdb.gimp_threshold (image.layers[-1], 128,255)
        # would threshold the bottom layer.
        #
        pdb.plug_in_colortoalpha(image, image.active_drawable, (0, 255, 0))
        pdb.gimp_file_save (image, image.active_layer, filename, filename)
        del image
