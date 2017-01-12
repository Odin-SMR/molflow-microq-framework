""" Molflow uService """
from setuptools import setup

setup(
    name='Molflow uService',
    version='1.0',
    long_description=__doc__,
    packages=['uservice', 'uservice.views', 'utils'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'flask-bootstrap',
        'flask-httpauth',
        'flask-restful',
        'passlib',
        'flask-sqlalchemy',
        'sqlalchemy',
        'sqlalchemy-migrate',
        'pymysql',
        'jsonschema',
        'jsl',
        'ConcurrentLogHandler',
        'python-dateutil'
    ]
)
