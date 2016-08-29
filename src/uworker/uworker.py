"""
Worker that performs jobs provided by a uservice api.
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
        'api_root': os.environ['UWORKER_API_ROOT'],
        # Set by user
        'api_project': os.environ['UWORKER_API_PROJECT'],
        'api_username': os.environ.get('UWORKER_API_USERNAME'),
        'api_password': os.environ.get('UWORKER_API_PASSWORD'),
    }


class UWorkerError(Exception):
    pass


class UWorker(object):
    """
    Flow:
    1. Ask api for jobs to perform.
    2. Claim a job.
    3. Call job command with input and deliver url as arguments.
    4. Continuously send output from command to api.
    5. If command exits with code != 0, send that info to api.
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
                    self.do_job(job.url_input_data, job.url_deliver,
                                job.url_output)
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

    def do_job(self, url_input_data, url_deliver=None, url_output=None):
        cmd = self.cmd + [url_input_data]
        if url_deliver:
            cmd.append(url_deliver)
            cmd.extend(self.api.auth)

        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        stdout_lines = iter(popen.stdout.readline, "")

        last_send = 0
        send_interval = 5
        buffer = BytesIO()
        for stdout_line in stdout_lines:
            if url_output:
                buffer.write(stdout_line)
                if time() - last_send > send_interval:
                    # TODO: Limit size of buffer
                    self.api.update_output(url_output, buffer.getvalue())
            self.log.info('Job output: %s' % stdout_line)

        popen.stdout.close()
        # TODO: Kill process if it takes too long before it exits
        return_code = popen.wait()
        if return_code != 0:
            msg = 'Job exited with code %r' % return_code
            self.log.warning(msg)
            if url_output:
                buffer.write(msg)
                self.api.update_output(url_output, buffer.getvalue())


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'INPUT_DATA_URL',
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
