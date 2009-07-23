#!/usr/bin/env python2.4
"""Convert an eps file to an svg file via pstoedit and skconvert."""

__author__ = "Jed Frechette <jedfrechette@gmail.com>"
__version__ = "0.1"
__date__ = "19 September 2006"

import os, subprocess, sys

file_names = sys.argv[1:]
for file in file_names:
    sk = file[:-4] + '.sk'
    svg = file[:-4] + '.svg'
    subprocess.call(['pstoedit', '-f', 'sk', file, sk])
    subprocess.call(['skconvert', sk, svg])
    os.remove(sk)
