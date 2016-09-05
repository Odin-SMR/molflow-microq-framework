import os
from test.testbase import BaseTest
from uworker import uworker


class TestUWorker(BaseTest):

    def setUp(self):
        self.env = {
            'UWORKER_HOSTNAME': 'testhost',
            'UWORKER_CONTAINER_NAME': 'testcontainer',
            'UWORKER_JOB_CMD': 'echo test',
            'UWORKER_JOB_TYPE': 'test',
            'UWORKER_JOB_API_ROOT': self._apiroot,
            'UWORKER_JOB_API_PROJECT': self._project,
            'UWORKER_JOB_API_USERNAME': self._username,
            'UWORKER_JOB_API_PASSWORD': self._password,
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
        os.environ['UWORKER_JOB_API_PASSWORD'] = 'wrong'
        self._run_once(expected_jobs_count=0)

        os.environ['UWORKER_JOB_API_ROOT'] = 'wrong'
        self._run_once(expected_jobs_count=0)

    def test_main(self):
        """Test to provide an input url argument"""
        uworker.main(['https://example.com/test'])
