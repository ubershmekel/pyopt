try:
    from distutils.core import setup
    print('distutils.core')
except ImportError:
    from setuptools import setup
    print('setuptools')


import os.path
import sys

from pyopt import pyopt
DOCUMENTATION = pyopt.__doc__

# THIS VERSION IS AUTO GENERATED FROM THE PYOPT.PY DOCSTRING
VERSION = '0.84'

# generate .rst file with documentation
#open(os.path.join(os.path.dirname(__file__), 'documentation.rst'), 'w').write(DOCUMENTATION)

setup(
	name='pyopt',
	packages=['pyopt'],
	version=VERSION,
	author='ubershmekel',
	author_email='ubershmekel@gmail.com',
	url='http://code.google.com/p/pyopt/',
	description='Exposing python functions to the command line',
	long_description=DOCUMENTATION,
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: BSD License',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 2',
		'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Terminals',
	]
)
