#!/usr/bin/env python

from setuptools import setup

with open('README.rst') as readme_file:
    long_description = readme_file.read()

setup(
    name='rgkit',
    version='0.5.0',
    description='Game Engine for Robot Game',
    maintainer='Peter Wen',
    maintainer_email='peter@whitehalmos.org',
    url='https://github.com/RobotGame/rgkit',
    packages=['rgkit', 'rgkit.render'],
    package_data={'rgkit': ['bots/*.py', 'maps/*.py']},
    license='Unlicense',
    long_description=long_description,
    entry_points={
        'console_scripts': [
            'rgrun = rgkit.run:main',
            'rgmap = rgkit.mapeditor:main'
        ]
    },
)
