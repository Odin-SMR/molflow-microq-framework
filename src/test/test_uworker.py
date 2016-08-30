import os
import unittest
from uworker import uworker


class TestUWorker(unittest.TestCase):

    def setUp(self):
        self.env = {
            'UWORKER_HOSTNAME': 'testhost',
            'UWORKER_CONTAINER_NAME': 'testcontainer',
            'UWORKER_JOB_CMD': 'echo test',
            'UWORKER_JOB_TYPE': 'test',
            'UWORKER_API_ROOT': 'http://localhost:5000/rest_api',
            'UWORKER_API_PROJECT': 'testproject',
            'UWORKER_API_USERNAME': 'worker1',
            'UWORKER_API_PASSWORD': 'sqrrl',
        }
        for k, v in self.env.items():
            os.environ[k] = v

    def test_bad_config(self):
        """Test missing environment variables"""
        optional = ['UWORKER_API_USERNAME', 'UWORKER_API_PASSWORD']
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
        w = uworker.UWorker()
        w.IDLE_SLEEP = .1
        w.ERROR_SLEEP = .1
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
        os.environ['UWORKER_API_PASSWORD'] = 'wrong'
        self._run_once(expected_jobs_count=0)

        os.environ['UWORKER_API_ROOT'] = 'wrong'
        self._run_once(expected_jobs_count=0)

    def test_main(self):
        """Test to provide an input url argument"""
        uworker.main(['https://example.com/test'])
