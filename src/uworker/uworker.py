"""
Worker that performs jobs provided by a uservice api.

 ---------          --------                      --------------
 |Job API| <------> |Worker| - <Command> <------> |External API|
 ---------          --------                      --------------
"""

import os
from sys import exit
import signal
import subprocess
import argparse
from io import BytesIO
from time import sleep, time

from uclient.uclient import UClient, UClientError, Job
from utils.logs import get_logger
from utils.defs import JOB_STATES


def get_config():
    """Create config dict from environment variables"""
    return {
        # Set by start script
        'hostname': os.environ['UWORKER_HOSTNAME'],
        'container_name': os.environ['UWORKER_CONTAINER_NAME'],
        # Set by Dockerfile, should always exist.
        'job_command': os.environ['UWORKER_JOB_CMD'],
        'job_type': os.environ['UWORKER_JOB_TYPE'],
        # Default can be set by Dockerfile, can be overrided by user
        'api_root': os.environ['UWORKER_JOB_API_ROOT'],
        # Set by user
        'api_project': os.environ['UWORKER_JOB_API_PROJECT'],
        'api_username': os.environ.get('UWORKER_JOB_API_USERNAME'),
        'api_password': os.environ.get('UWORKER_JOB_API_PASSWORD'),
        'external_username': os.environ.get('UWORKER_EXTERNAL_API_USERNAME'),
        'external_password': os.environ.get('UWORKER_EXTERNAL_API_PASSWORD'),
    }


class UWorkerError(Exception):
    pass


class UWorker(object):
    """
    Worker flow
    -----------

    1. Ask job api for jobs to perform.
    2. Claim a job.
    3. Call job command with source and target url as arguments.
    4. Continuously send output from command to api.
    5. When command exits, send exit code to api and set job status to
       finished if code == 0, else set status to failed.

    The job command
    ---------------

    The worker will call the job command with an url that should
    return input data and an url that the command should send the
    results to.
    The worker can also provide the command with credentials to the
    target url if needed.

    >> /path/to/command INPUT_URL [TARGET_URL USERNAME PASSWORD]]

    The command should only exit successfully if the result was accepted
    by the target api. The worker can then set the status of the job to
    failed or finished by looking at the exit code of the command.
    """
    # Sleep this many seconds when no jobs are available
    IDLE_SLEEP = 1
    # Sleep this many seconds if something unexpected goes wrong
    ERROR_SLEEP = 60

    def __init__(self, start_service=False):
        try:
            config = get_config()
        except KeyError as e:
            raise UWorkerError('Missing config value: %s' % e)
        self.name = '{class_name}_{host}_{container}'.format(
            class_name=self.__class__.__name__,
            host=config['hostname'],
            container=config['container_name'])
        self.log = get_logger(self.name)
        self.job_count = 0
        self.log_config(config)
        self.cmd = config['job_command'].split()
        self.job_type = config['job_type']
        self.api = UClient(config['api_root'], config['api_project'],
                           username=config['api_username'],
                           password=config['api_password'])
        self.external_auth = (config['external_username'],
                              config['external_password'])
        if start_service:
            self.alive = True
            signal.signal(signal.SIGINT, self.stop)
            self.run()

    def log_config(self, config):
        self.log.info('Loaded config:')
        for k, v in sorted(config.items()):
            self.log.info('%s = %s' % (k, v))

    def run(self, only_once=False):
        self.running = True
        while self.alive:
            if only_once:
                self.alive = False
            try:
                job = Job.fetch(self.job_type, self.api)
                if not job:
                    sleep(self.IDLE_SLEEP)
                elif self.claim_job(job):
                    job.send_status(JOB_STATES.started)
                    success = self.do_job(
                        job.url_source, job.url_target, job.url_output)
                    if success:
                        job.send_status(JOB_STATES.finished)
                    else:
                        job.send_status(JOB_STATES.failed)
                    self.job_count += 1
            except Exception as e:
                self.log.exception('Unhandled exception: %s' % e)
                sleep(self.ERROR_SLEEP)
        self.running = False

    def stop(self, signal, frame):
        self.alive = False

    def claim_job(self, job, nr_trials=5):
        for _ in range(nr_trials):
            try:
                job.claim(worker=self.name)
                return True
            except UClientError as e:
                # TODO: Separate api error and already claimed error
                self.log.error('Failed job claim: %s' % e)
                sleep(self.ERROR_SLEEP)
        return False

    def do_job(self, url_source, url_target=None, url_output=None):
        cmd = self.cmd + [url_source]
        if url_target:
            cmd.append(url_target)
            cmd.extend(cred for cred in self.external_auth if cred)
        self.log.info('Starting job: %s' % cmd)
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        stdout_lines = iter(popen.stdout.readline, "")
        stderr_lines = iter(popen.stderr.readline, "")

        def write_lines(what, lines, buffer):
            buffer.write('******** %s ********\n\n' % what)
            last_send = 0
            send_interval = 5
            for line in lines:
                if url_output:
                    buffer.write(line)
                    if time() - last_send > send_interval:
                        # TODO: Limit size of buffer
                        self.api.update_output(url_output, buffer.getvalue())
                        last_send = time()
                if line.strip():
                    self.log.info('Job %s output: %s' % (what, line))

        buffer = BytesIO()
        write_lines('stdout', stdout_lines, buffer)
        write_lines('stderr', stderr_lines, buffer)

        popen.stdout.close()
        popen.stderr.close()

        # TODO: Kill process if it takes too long before it exits
        return_code = popen.wait()
        msg = 'Job exited with code %r' % return_code
        if url_output:
            buffer.write(msg + '\n')
            self.api.update_output(url_output, buffer.getvalue())
        if return_code != 0:
            self.log.warning(msg)
            return False
        else:
            self.log.info(msg)
            return True


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'INPUT_DATA_URL', nargs='?',
        help='If provided, run command on this input url and exit')
    return parser


def main(args=None):
    parser = get_argparser()
    args = parser.parse_args(args)
    if args.INPUT_DATA_URL:
        worker = UWorker()
        worker.do_job(args.INPUT_DATA_URL)
    else:
        print('Spawning worker')
        UWorker(start_service=True)

if __name__ == '__main__':
    exit(main())
