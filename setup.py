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

    base_headers = [h for h in glob.glob('base/*.h')]
    template_headers = [h for h in glob.glob('templates/example.h')]
    depends = base_headers + template_headers

    print(base_headers)
    print(template_headers)
    print(depends)

    sources = [s.replace('.h', '.cxx') for s in template_headers]
    sources += [os.path.join('base', 'sparsetools.cxx')]
    print(sources)

    import generate_functions
    generate_functions.main(template_headers, '')
    # try:
    #     subprocess.check_call([sys.executable, 'generate_functions.py',
    #                           '--no-force'])
    # except subprocess.CalledProcessError as e:
    #     raise Exception('Problem running' + ' '.join(e.cmd))

    config.add_extension('crapper',
                         define_macros=[('__STDC_FORMAT_MACROS', 1)],
                         depends=depends,
                         include_dirs=['base', 'templates'],
                         sources=sources)
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
