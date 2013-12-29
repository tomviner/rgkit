from setuptools import setup

setup(
    name='rgkit',
    version='0.2.6',
    description='Robot Game Testing Kit',
    maintainer='Peter Wen',
    maintainer_email='peter@whitehalmos.org',
    url='https://github.com/WhiteHalmos/rgkit',
    packages=['rgkit', 'rgkit.render'],
    package_data={'rgkit': ['bots/*.py', 'maps/*.py']},
    license='Unlicense',
    entry_points={
        'console_scripts': [
            'rgrun = rgkit.run:main',
            'rgmap = rgkit.mapeditor:main'
        ]
    },
)
