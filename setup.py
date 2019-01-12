# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name'bag_xbase_logic',
    version='0.1',
    license='BSD 3-Clause License',
    description='BAG custom digital generators',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
    ],
    author='Zhongkai Wang',
    author_email='zhongkai@berkeley.edu',
    python_requires='>=3.7',
    install_requires=[
        'bag>=3.0',
    ],
    tests_require=[
        'pytest',
        'pytest-xdist',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
)
