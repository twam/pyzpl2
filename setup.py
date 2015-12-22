# coding=utf-8

from setuptools import setup, find_packages
from codecs import open


setup(
    name='pyzpl2',
    version='0.1',
    description='ZPL II',
    long_description=open('README.rst', encoding='utf-8').read(),
    url='https://github.com/twam/pyzpl2',
    author='Tobias Müller',
    author_email='Tobias_Mueller@twam.info',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3.5',
        'Topic :: Printing'
    ],
    keywords='zebra zpl zpl2 zplII label',
    packages=find_packages(),
    install_requires=[''],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    platforms='any',
)
