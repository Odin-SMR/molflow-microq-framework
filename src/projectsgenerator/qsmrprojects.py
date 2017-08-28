#!/usr/bin/env python2
"""usage: qsmrprojects.py [-h] [--deadline DEADLINE]
                           PROJECT_NAME ODIN_PROJECT PROCESSING_IMAGE_URL
                           CONFIG_FILE

Add a processing project to the microq job service.

positional arguments:
  PROJECT_NAME          Microq service project name, must only contain ascii
                        letters and digits and start with an ascii letter
  ODIN_PROJECT          the project name used in the odin api
  PROCESSING_IMAGE_URL  url to the worker processing image
  CONFIG_FILE           path to configuration file

optional arguments:
  -h, --help            show this help message and exit
  --deadline DEADLINE   The desired deadline of the project(yyyy-mm-dd).
                        Default value is 10 days from now. However, this
                        parameter is used to set the priority of the project
                        and the actual deadline can not be guaranteed.

The configuration file should contain these settings:
JOB_API_ROOT=https://example.com/job_api
JOB_API_USERNAME=<username>
JOB_API_PASSWORD=<password>
"""
from sys import stderr
from datetime import datetime, timedelta, date
import argparse
import requests


DESCRIPTION = ("Add a processing project to the microq job service.\n")

CONFIG_FILE_DOCS = """The configuration file should contain these settings:
JOB_API_ROOT=https://example.com/job_api
JOB_API_USERNAME=<username>
JOB_API_PASSWORD=<password>"""


def make_argparser():
    """argument parser setup"""
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=CONFIG_FILE_DOCS,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'PROJECT_NAME', help=(
            'Microq service project name, must only contain ascii letters '
            'and digits and start with an ascii letter'))
    parser.add_argument('ODIN_PROJECT', help=(
        'the project name used in the odin api'))
    parser.add_argument('PROCESSING_IMAGE_URL', help=(
        'url to the worker processing image'))
    parser.add_argument('CONFIG_FILE', help='path to configuration file')
    parser.add_argument('--deadline', help=(
        'The desired deadline of the project (yyyy-mm-dd).'
        'Default value is 10 days from now. However, this parameter '
        'is used to set the priority of the project and the actual '
        'deadline can not be guaranteed.'),
                        default=str(date.today() + timedelta(days=10)))
    return parser


def validate_project_not_exist(url_project):
    """Project should not already exists"""
    if requests.get(url_project).status_code == 200:
        return False
    return True


def validate_deadline(deadline):
    """validate deadline"""
    if datetime.strptime(deadline, "%Y-%m-%d") < datetime.utcnow():
        return False
    return True


def validate_config(config):
    """Return True if ok, else False"""
    def error(msg):
        """error message"""
        stderr.write(msg + '\n')
        error.ok = False
    error.ok = True
    required = [
        'JOB_API_ROOT', 'JOB_API_USERNAME', 'JOB_API_PASSWORD']
    for key in required:
        if key not in config or not config[key]:
            error('Missing in config: %s' % key)
    if not error.ok:
        return False

    url = config['JOB_API_ROOT']
    if not url.startswith('http'):
        error('JOB_API_ROOT does not look like an url')
    if url.endswith('/'):
        error('JOB_API_ROOT must not end with /')
    return error.ok


def validate_project_name(project_name):
    """Must be ascii alnum and start with letter"""
    if not project_name:
        return False
    if isinstance(project_name, unicode):
        project_name = project_name.encode('utf-8')
    if not project_name[0].isalpha():
        return False
    if not project_name.isalnum():
        return False
    return True


def load_config(config_file):
    """load config file"""
    with open(config_file) as inp:
        conf = dict(row.strip().split('=') for row in inp if row.strip())
    for parameter, value in conf.items():
        conf[parameter] = value.strip('"')
    return conf


def create_project(url_project, config, args):
    """Add a project to microq job service"""
    request = requests.put(
        url_project,
        auth=(config['JOB_API_USERNAME'], config['JOB_API_PASSWORD']),
        json={
            'processing_image_url': args.PROCESSING_IMAGE_URL,
            'deadline': args.deadline,
            'name': args.ODIN_PROJECT})
    if request.status_code != 201:
        stderr.write((
            'Project could not be created'))
        return 1


def delete_project(url_project, config):
    """Delete a project of microq servise"""
    requests.delete(
        url_project,
        auth=(config['JOB_API_USERNAME'], config['JOB_API_PASSWORD']),
    )


def main(args=None):
    """main function"""
    args = make_argparser().parse_args(args)
    if not validate_project_name(args.PROJECT_NAME):
        stderr.write((
            'Project name must only contain ascii letters and digits and '
            'start with an ascii letter\n'))
        return 1
    if not validate_deadline(args.deadline):
        stderr.write((
            'Project deadline can not be earlier than today\n'))
        return 1
    config = load_config(args.CONFIG_FILE)
    if not validate_config(config):
        return 1
    url_project = config['JOB_API_ROOT'] + '/v4/' + args.PROJECT_NAME
    if not validate_project_not_exist(url_project):
        stderr.write((
            'Project {0} already exists.\n'
            'Change PROJECT_NAME!\n'.format(args.PROJECT_NAME)))
        return 1
    create_project(url_project, config, args)
    return 0

if __name__ == '__main__':
    exit(main())
