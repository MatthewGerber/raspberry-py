from os import path

from setuptools import setup, find_packages

TEST_REQUIREMENTS = [

]

DEV_REQUIREMENTS = [
    'bump2version==1.0.1'
]

with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='raspberry-py',
    version='0.3.0.dev0',
    description='A Python/REST interface for GPIO circuits running on the Raspberry Pi',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Matthew Gerber',
    author_email='gerber.matthew@gmail.com',
    url='https://matthewgerber.github.io/raspberry-py',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    python_requires='~=3.9',
    install_requires=[
        'numpy==1.21.5',
        'RPi.GPIO==0.7.1',
        'smbus2==0.4.1 ',
        'Flask==2.2.2',
        'Flask-Cors==3.0.10',
        'opencv-python==4.6.0.66',
        'rpi-ws281x==4.3.4'
    ],
    tests_require=TEST_REQUIREMENTS,
    extras_require={
        'test:': TEST_REQUIREMENTS,
        'dev:': TEST_REQUIREMENTS + DEV_REQUIREMENTS
    },
    entry_points={
        'console_scripts': [
            'write_component_files=raspberry_py.rest.application:write_component_files_cli'
        ]
    }
)
