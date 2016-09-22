import os
import json
from time import time, sleep
import threading
import unittest

import requests
from werkzeug.serving import BaseWSGIServer, WSGIRequestHandler
from werkzeug.wrappers import Request, Response

from test.testbase import BaseWithWorkerUser, TEST_DATA_DIR

from utils.defs import JOB_STATES
from utils.docker_util import in_docker
from uworker import uworker


class TestUWorker(BaseWithWorkerUser):

    def setUp(self):
        self.env = {
            'UWORKER_HOSTNAME': 'testhost',
            'UWORKER_CONTAINER_NAME': 'testcontainer',
            'UWORKER_JOB_CMD': 'echo test',
            'UWORKER_JOB_TYPE': 'test',
            'UWORKER_JOB_API_ROOT': self._apiroot,
            'UWORKER_JOB_API_PROJECT': self._project,
            'UWORKER_JOB_API_USERNAME': self._token,
            'UWORKER_JOB_API_PASSWORD': "",
            'UWORKER_EXTERNAL_API_USERNAME': 'test',
            'UWORKER_EXTERNAL_API_PASSWORD': 'test',
        }
        for k, v in self.env.items():
            os.environ[k] = v
        self._insert_test_jobs()

    def tearDown(self):
        self._delete_test_project()

    def test_bad_config(self):
        """Test missing environment variables"""
        optional = ['UWORKER_JOB_API_USERNAME',
                    'UWORKER_JOB_API_PASSWORD',
                    'UWORKER_EXTERNAL_API_USERNAME',
                    'UWORKER_EXTERNAL_API_PASSWORD']
        for k in self.env:
            v = os.environ.pop(k)
            if k in optional:
                uworker.UWorker()
            else:
                print('Mandatory: %s' % k)
                with self.assertRaises(uworker.UWorkerError):
                    uworker.UWorker()
            os.environ[k] = v

    def _run_once(self, expected_jobs_count=0):
        uworker.UWorker.IDLE_SLEEP = .01
        uworker.UWorker.ERROR_SLEEP = .01
        w = uworker.UWorker()
        w.alive = True
        self.assertEqual(w.job_count, 0)
        w.run(only_once=True)
        self.assertEqual(w.job_count, expected_jobs_count)
        # TODO: Check that result and output from job were stored.

    def test_run(self):
        """Test one worker run"""
        self._run_once(expected_jobs_count=1)

    def test_exit_code(self):
        """Test job command that return failure"""
        os.environ['UWORKER_JOB_CMD'] = 'ls test_exit_code'
        self._run_once(expected_jobs_count=1)

    def test_api_failure(self):
        """Test bad api url and password"""
        os.environ['UWORKER_JOB_API_USERNAME'] = 'wrong'
        self._run_once(expected_jobs_count=0)

        os.environ['UWORKER_JOB_API_ROOT'] = 'wrong'
        self._run_once(expected_jobs_count=0)

    def test_main(self):
        """Test to provide an input url argument"""
        uworker.main(['https://example.com/test'])


@unittest.skipIf(not in_docker(),
                 'Must be run in a container with a running uworker')
class TestQsmrJob(BaseWithWorkerUser):
    JOB_ID = '42'
    _apiroot = 'http://webapi:5000/rest_api'
    _project = 'testproject'

    ODINMOCK_HOST = 'localhost'
    ODINMOCK_PORT = 8888

    @property
    def odin_mock_root(self):
        return 'http://%s:%s' % (self.ODINMOCK_HOST, self.ODINMOCK_PORT)

    def setUp(self):
        super(TestQsmrJob, self).setUp()
        self.odin_api = MockOdinAPI(self.ODINMOCK_HOST, self.ODINMOCK_PORT)
        self.odin_api.start()

    def tearDown(self):
        super(TestQsmrJob, self).tearDown()
        requests.get(self.odin_mock_root + '?shutdown=1')

    def test_success(self):
        self._test_job()

    def test_failure(self):
        self._test_job(should_succeed=False)

    def _test_job(self, should_succeed=True):
        """Start a fake odin api server and run a qsmr job"""
        self._insert_qsmr_job()
        # Wait for result
        start = time()
        max_wait = 60*3
        job_status = self._get_job_status()
        while (job_status not in (JOB_STATES.finished, JOB_STATES.failed) and
               not self.odin_api.result):
            sleep(1)
            if time() - start > max_wait:
                break
            job_status = self._get_job_status()
        if self.odin_api.result:
            print('Result: %r' % self.odin_api.result.keys())
        else:
            print('No results!')

        # Wait for job to finish
        start = time()
        max_wait = 10
        job_status = self._get_job_status()
        while job_status == JOB_STATES.started:
            sleep(1)
            if time() - start > max_wait:
                break
            job_status = self._get_job_status()

        print('Job status: %r' % job_status)
        print('Job output: %r' % self._get_job_output())
        print('Job results should have been written to %s' % os.path.join(
            TEST_DATA_DIR, 'odin_result.json'))
        if should_succeed:
            self.assertEqual(job_status, JOB_STATES.finished)
            self.assertTrue(self.odin_api.result)
        else:
            self.assertEqual(job_status, JOB_STATES.failed)
            self.assertIsNone(self.odin_api.result)

    def _insert_qsmr_job(self):
        self._insert_job(
            {'id': self.JOB_ID, 'type': 'qsmr',
             'source_url': self.odin_mock_root,
             'target_url': self.odin_mock_root})

    def _get_job_status(self):
        r = requests.get(
            self._apiroot + '/v4/{}/jobs/{}/status'.format(
                self._project, self.JOB_ID),
            auth=(self._username, self._password))
        return r.json()['Status']

    def _get_job_output(self):
        r = requests.get(
            self._apiroot + '/v4/{}/jobs/{}/output'.format(
                self._project, self.JOB_ID),
            auth=(self._username, self._password))
        return r.json()


class MockOdinAPI(threading.Thread):
    """A really basic HTTP server that listens on (host, port) and serves
    static odin data and accepts posts.
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.load_data()
        self.result = None
        super(MockOdinAPI, self).__init__()

    def load_data(self):
        with open(os.path.join(TEST_DATA_DIR, 'odin_log.json')) as inp:
            self.log = json.loads(inp.read())
        self.log['Info']['URLS']['URL-spectra'] = 'http://%s:%s?spectra=1' % (
            self.host, self.port)
        with open(os.path.join(TEST_DATA_DIR, 'odin_spectra.json')) as inp:
            self.spectra = json.loads(inp.read())

    def handle_request(self, environ, start_response):
        try:
            request = Request(environ)
            if request.method.lower() == 'get':
                if request.args.get('shutdown'):
                    self.shutdown_server(environ)
                elif request.args.get('spectra'):
                    response = Response(json.dumps(self.spectra), headers={
                        'Content-Type': 'application/json'})
                else:
                    response = Response(json.dumps(self.log), headers={
                        'Content-Type': 'application/json'})
            elif request.method.lower() == 'post':
                self.result = json.loads(request.get_data(
                    cache=False, as_text=True))
                with open(os.path.join(
                        TEST_DATA_DIR, 'odin_result.json'), 'w') as out:
                    out.write(json.dumps(self.result))
                response = Response('thanks!')
            else:
                response = Response(':(', 415)
        except Exception as e:
            print('Mock odin excepted: %s' % e)
            raise
        return response(environ, start_response)

    def run(self):
        server = BaseWSGIServer(self.host, self.port, self.handle_request,
                                _QuietHandler)
        server.log = lambda *args, **kwargs: None
        server.serve_forever()

    @staticmethod
    def shutdown_server(environ):
        if 'werkzeug.server.shutdown' not in environ:
            raise RuntimeError('Not running the development server')
        environ['werkzeug.server.shutdown']()


class _QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        """Suppress request logging so as not to pollute application logs."""
        pass
