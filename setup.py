from setuptools import setup, find_packages

with open('README.rst') as f:
    description = f.read()

setup(
    name='knitty-gritty',
    version='0.0.2',
    description='A tool for managing knitting machine patterns',
    long_description=description,
    url='https://github.com/mhallin/knitty-gritty',

    author='Magnus Hallin',
    author_email='mhallin@gmail.com',

    license='BSD',

    packages=find_packages(),

    install_requires=[
        'click>=2.4,<2.5',
        'Pillow>=2.5,<2.6',
        'pyserial>=2.7,<2.8',
    ],

    extras_require={
        'dev': [
            'flake8>=2.2,<2.3',
            'mccabe>=0.2,<0.3',
            'pep8>=1.5,<1.6',
            'pip-tools>=0.3,<0.4',
            'pyflakes>=0.8.1,<0.9',
            'wheel>=0.24,<0.25',
        ],
    },

    entry_points={
        'console_scripts': [
            'knitty-gritty = knittygritty.main:cli'
        ],
    },
)
