#!/usr/bin/env python
from __future__ import division, print_function, absolute_import

import os
import sys
import subprocess


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration()
    config.add_data_dir('tests')

    try:
        subprocess.check_call([sys.executable, 'instantiate_templates.py',
                              '--no-force'])
    except subprocess.CalledProcessError as e:
        raise Exception('Problem running' + ' '.join(e.cmd))

    base_headers = [h for h in dir('./include') if not h.endswith('.h')]
    template_headers = [h for h in dir('./templates') if not h.endswith('.h')]
    depends = [os.path.join('include', h) for h in base_headers]
    depends += [os.path.join('include', h) for h in template_headers]
    sources = [os.path.join('templates', s.replace('.h', '.cxx'))
               for s in template_headers]

    config.add_extension('crapper',
                         define_macros=[('__STDC_FORMAT_MACROS', 1)],
                         depends=depends,
                         include_dirs=['include', 'templates'],
                         sources=sources)

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())
