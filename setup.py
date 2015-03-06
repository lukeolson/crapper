#!/usr/bin/env python
from __future__ import division, print_function, absolute_import

import os
# import sys
# import subprocess
import glob


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration()
    config.add_data_dir('tests')

    sources = []
    # check for a config file in ..
    try:
        with open('../crappy.cfg', 'r') as fcfg:
            newsource = fcfg.readline().strip()
            newsource = os.path.join('..', newsource)
        if os.isfile(newsource):
            sources += [newsource]
    except IOError as e:
        print("I/O error({%d}): %s" % (e.errno, e.strerror))

    base_headers = [h for h in glob.glob('base/*.h')]
    template_headers = [h for h in glob.glob('templates/example.h')]
    depends = base_headers + template_headers

    sources += [s.replace('.h', '.cxx') for s in template_headers]
    sources += [os.path.join('base', 'crappy.cxx')]
    sources += [os.path.join('templates', 'initmodule.cxx')]

    import generate_functions
    generate_functions.main(template_headers, '')

    config.add_extension('crappy',
                         define_macros=[('__STDC_FORMAT_MACROS', 1)],
                         depends=depends,
                         include_dirs=['base', 'templates'],
                         sources=sources)
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
