""" Hermod uService """
from setuptools import setup

setup(
    name='Hermod uService',
    version='1.0',
    long_description=__doc__,
    packages=['uservice', 'uservice.views', 'uclient', 'uworker', 'utils'],
    entry_points={
        'console_scripts': ['uworker = uworker.uworker:main']
    },
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
        'pymysql',
        'jsonschema',
        'jsl',
        'ConcurrentLogHandler',
        'python-dateutil'
    ]
)
