from setuptools import setup

setup(
    name='rgkit',
    version='0.1',
    description='Robot Game Testig Kit',
    maintainer='Peter Wen',
    maintainer_email='peter@whitehalmos.org',
    url='https://github.com/WhiteHalmos/rgkit',
    packages=['rgkit'],
    package_data={'rgkit': ['maps/*.py']},
    license='Unlicense',
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': [
            'rgrun = rgkit.run:main',
            'rgmap = rgkit.mapeditor:main'
        ]
    },
)
