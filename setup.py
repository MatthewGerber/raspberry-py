from setuptools import setup, find_packages

TEST_REQUIREMENTS = [

]

DEV_REQUIREMENTS = [

]

setup(
    name='rpi',
    version='0.1.0.dev0',
    description='Raspberry Pi',
    author='Matthew Gerber',
    author_email='gerber.matthew@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    python_requires='~=3.7',
    install_requires=[
        'numpy==1.21.5',
        'RPi.GPIO==0.7.0',
        'smbus2==0.4.1 ',
        'Flask==2.2.2',
        'Flask-Cors==3.0.10'
    ],
    tests_require=TEST_REQUIREMENTS,
    extras_require={
        'test:': TEST_REQUIREMENTS,
        'dev:': TEST_REQUIREMENTS + DEV_REQUIREMENTS
    },
    entry_points={
        'console_scripts': [
            'write_component_files=rpi.rest.application:write_component_files_cli'
        ]
    }
)
