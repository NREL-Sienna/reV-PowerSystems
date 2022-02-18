from setuptools import setup
import os
import sys

_here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(_here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='rev_powersystems',
    version='0.0.1',
    description=('Construct PowerSystems timeseries from revx outputs.'),
    long_description=long_description,
    author='Joseph McKinsey',
    author_email='joseph.mckinsey@nrel.gov',
    url='https://github.com/NREL-SIIP/reV-PowerSystems/',
    license='MPL-2.0',
    packages=['rev_powersystems'],
#   no dependencies in this example
    install_requires=[
        'scipy>=1.7.1',
        'numpy>=1.21.1',
        'NREL-reVX>=0.3.39'
    ],
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.7'
    ]
)
