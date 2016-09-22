"""
Worker that performs jobs provided by a uservice api.

 ---------          --------                      --------------
 |Job API| <------> |Worker| - <Command> <------> |External API|
 ---------          --------                      --------------
"""

import os
import errno
from sys import exit
import signal
import subprocess
import argparse
from io import BytesIO
from time import sleep, time
from datetime import datetime
from threading import Thread, Lock
from numbers import Real

from uclient.uclient import UClient, UClientError, Job
from utils import debug_util
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
        'job_timeout': os.environ.get('UWORKER_JOB_TIMEOUT'),
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

    >>> /path/to/command INPUT_URL [TARGET_URL USERNAME PASSWORD]]

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
        self.log = get_logger(self.name, to_file=start_service,
                              to_stdout=not start_service)
        self.job_count = 0
        self.log_config(config)
        self.cmd = config['job_command']
        self.job_type = config['job_type']
        self.job_timeout = config['job_timeout']
        if self.job_timeout:
            self.job_timeout = int(self.job_timeout)
        self.executor = CommandExecutor(self.cmd, self.log)
        self.api = UClient(config['api_root'], config['api_project'],
                           username=config['api_username'],
                           password=config['api_password'],
                           time_between_retries=self.ERROR_SLEEP)
        self.external_auth = (config['external_username'],
                              config['external_password'])
        if start_service:
            self.alive = True
            signal.signal(signal.SIGINT, self.stop)
            signal.signal(signal.SIGTERM, self.stop)
            self.log_stacks_thread = Thread(target=self._log_stack_trace)
            self.log_stacks_thread.start()
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
                    exit_code = self.do_job(
                        job.url_source, job.url_target, job.url_output)
                    if exit_code == 0:
                        job.send_status(JOB_STATES.finished)
                    else:
                        job.send_status(JOB_STATES.failed)
                    self.job_count += 1
            except Exception as e:
                self.log.exception('Unhandled exception: %s' % e)
                sleep(self.ERROR_SLEEP)
        self.running = False

    def stop(self, signal, frame):
        # TODO: Should kill job command and unclaim current job
        self.alive = False

    def claim_job(self, job, nr_trials=5):
        for _ in range(nr_trials):
            try:
                job.claim(worker=self.name)
                return True
            except UClientError as e:
                if e.status_code == 409:
                    return False
                self.log.error('Failed job claim: %s' % e)
                sleep(self.ERROR_SLEEP)
        return False

    def do_job(self, url_source, url_target=None, url_output=None):
        args = [url_source]
        if url_target:
            args.append(url_target)
            args.extend(cred for cred in self.external_auth if cred)

        def output_callback(output):
            if url_output:
                try:
                    # TODO: Limit size of output that can be sent
                    self.api.update_output(url_output, output)
                except:
                    self.log.exception(
                        'Exception when sending output to job api:')

        self.log.info('Starting job: %s' % args)
        # TODO: Add support for letting a job override the configured timeout
        exit_code = self.executor.execute(
            args, output_callback, timeout=self.job_timeout)
        return exit_code

    def _log_stack_trace(self, log_interval=60):
        last_log = time()
        while self.alive:
            sleep(1)
            if time() - last_log > log_interval:
                for stack in debug_util.get_current_stacks():
                    self.log.info('Stacktrace snapshot:\n %s' % stack)
                last_log = time()


class ExecutorError(Exception):
    pass


class CommandExecutor(object):
    def __init__(self, cmd, log):
        self.cmd = cmd.split()
        self.log = log
        self.output_lock = Lock()

    def execute(self, command_args, output_callback, timeout=None):
        """
        Execute the command with args and monitor the progress.

        Args:
          commandd_args (list): List of arguments to provide to the command.
          output_callback (function): Call this function with output from
            the command as argument.
          timeout (int): Send TERM to the command if it has not finished
            after this many seconds. Also send KILL (9) if it still is
            alive 5 seconds after TERM was sent.
        """
        cmd = self.cmd + command_args
        if timeout:
            if not isinstance(timeout, Real) or timeout <= 0:
                raise ExecutorError(
                    'timeout must be a positive number, timeout=%r' % timeout)
            cmd = ['timeout', '--kill-after=5', str(int(timeout))] + cmd
        popen = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        self.log.info('Job process started with pid %s: %s' % (
            popen.pid, cmd))

        output = BytesIO()
        self._handle_output(popen, output, output_callback)
        exit_code, killed = self._wait_for_exit(popen)

        if killed:
            msg = ('Killed job process after timeout of {} seconds'
                   '').format(timeout)
            self._write_output('executor', msg + '\n', output)
            self.log.warning(msg)

        msg = 'Job process exited with code {}'.format(exit_code)
        self._write_output('executor', msg + '\n', output)
        output_callback(output.getvalue())
        if exit_code != 0:
            self.log.warning(msg)
        else:
            self.log.info(msg)
        return exit_code

    def _handle_output(self, popen, out_buffer, out_callback):
        stdout_lines = iter(popen.stdout.readline, "")
        stderr_lines = iter(popen.stderr.readline, "")

        t_stdout = Thread(target=self._read_lines, args=(
            'stdout', stdout_lines, out_buffer, out_callback))
        t_stderr = Thread(target=self._read_lines, args=(
            'stderr', stderr_lines, out_buffer, out_callback))
        t_stdout.start()
        t_stderr.start()
        return t_stdout, t_stderr

    def _read_lines(self, what, lines, out_buffer, out_callback):
        last_callback = 0
        callback_interval = 5
        for line in lines:
            with self.output_lock:
                self._write_output(what, line, out_buffer)
                if time() - last_callback > callback_interval:
                    out_callback(out_buffer.getvalue())
                    last_callback = time()
            if line.strip():
                self.log.info('Job process %s: %s' % (what, line))

    def _wait_for_exit(self, popen):
        exit_code = popen.poll()
        while exit_code is None:
            sleep(1)
            exit_code = popen.poll()

        killed = exit_code in (124, 128+9)

        self._reap_children(popen.pid)

        for what, stream in (('stdout', popen.stdout),
                             ('stderr', popen.stderr)):
            try:
                stream.close()
            except Exception as e:
                self.log.warning(
                    'Could not close command {}: <{}> {}'.format(
                        what, e.__class__.__name__, e))

        return exit_code, killed

    def _reap_children(self, pid):
        """Docker does not reap orphaned children, see:
        https://blog.phusion.nl/2015/01/20/docker-and-the-pid-1-zombie-reaping-problem/
        """
        try:
            this_pid, status = os.waitpid(-1, 0)
            self.log.info('Reaped child %s, exit code: %s' % (
                this_pid, status))
            while this_pid != pid:
                this_pid, status = os.waitpid(-1, 0)
                self.log.info('Reaped child %s, exit code: %s' % (
                    this_pid, status))
        except OSError as e:
            if e.errno in (errno.ECHILD, errno.ESRCH):
                return
            raise

    @staticmethod
    def _write_output(what, msg, output):
        output.write('%s - %s: %s' % (
            datetime.utcnow().isoformat(), what.upper(), msg))


def get_argparser():
    parser = argparse.ArgumentParser(
        description='Start UWorker service if no input url is provided.')
    parser.add_argument(
        'INPUT_DATA_URL', nargs='?',
        help='If provided, run job command on this input url and exit.')
    return parser


def main(args=None):
    parser = get_argparser()
    args = parser.parse_args(args)
    if args.INPUT_DATA_URL:
        worker = UWorker()
        return worker.do_job(args.INPUT_DATA_URL)
    else:
        print('Spawning worker')
        UWorker(start_service=True)

if __name__ == '__main__':
    exit(main())
