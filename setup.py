from setuptools import setup

with open('README.md') as readme_file:
    long_description = readme_file.read()

setup(
    name='rgkit',
    version='0.3.6',
    description='Robot Game Testing Kit',
    maintainer='Peter Wen',
    maintainer_email='peter@whitehalmos.org',
    url='https://github.com/WhiteHalmos/rgkit',
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
