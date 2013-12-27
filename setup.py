from setuptools import setup

setup(
    name='rgkit',
    version='0.2.5',
    description='Robot Game Testing Kit',
    maintainer='Peter Wen',
    maintainer_email='peter@whitehalmos.org',
    url='https://github.com/WhiteHalmos/rgkit',
    packages=['rgkit'],
    package_data={'rgkit': ['bots/*.py', 'render/*.py', 'maps/*.py']},
    license='Unlicense',
    entry_points={
        'console_scripts': [
            'rgrun = rgkit.run:main',
            'rgmap = rgkit.mapeditor:main'
        ]
    },
)
