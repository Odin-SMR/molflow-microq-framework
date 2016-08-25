""" Hermod uService """
from setuptools import setup

setup(
    name='Hermod uService',
    version='1.0',
    long_description=__doc__,
    packages=['uservice', 'uservice.views', 'uclient'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask']
)
