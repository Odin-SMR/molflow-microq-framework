import json
from uclient.uclient import UClient, UClientError, Job
from test.testbase import BaseTest


class BaseTestUClient(BaseTest):
    def setUp(self):
        super(BaseTestUClient, self).setUp()
        self._credentials = {"username": "worker1",
                             "password": "sqrrl"}

    def get_client(self, credentials=None, project=None):
        credentials = (credentials if credentials is not None
                       else self._credentials)
        project = project if project is not None else self._project
        return UClient(self._apiroot, project, verbose=True, **credentials)


class TestErrors(BaseTestUClient):

    def test_bad_project_name(self):
        bad_names = ['', '1', 'test;']
        for name in bad_names:
            with self.assertRaises(UClientError):
                self.get_client(project=name)

    def test_api_exception(self):
        """Test api exception"""
        api = self.get_client()
        with self.assertRaises(UClientError):
            api.update_output('bad url', 'out')


class BaseTestWithInsertedJob(BaseTestUClient):

    def setUp(self):
        super(BaseTestWithInsertedJob, self).setUp()
        self._delete_test_project()
        self._insert_test_jobs()

    def tearDown(self):
        self._delete_test_project()


class TestCredentials(BaseTestWithInsertedJob):

    def test_credentials_from_file(self):
        """Test load of credentials from file"""
        credentials_file = '/tmp/credentials.json'
        with open(credentials_file, 'w') as out:
            out.write(json.dumps(self._credentials))
        api = self.get_client({'credentials_file': credentials_file})
        job = Job.fetch('test_type', api)
        job.send_status('test')

    def test_bad_credentials(self):
        """Test invalid and empty credentials"""
        # The guy below should use different uris:
        credentials = {"username": "snoopy", "password": "ace"}
        api = self.get_client(credentials)
        job = Job.fetch('test_type', api)
        with self.assertRaises(UClientError):
            job.claim()

        try:
            job.send_status('evil')
            raise AssertionError('Should have excepted!')
        except UClientError as e:
            self.assertEqual(e.status_code, 401)

        # No credentials provided
        api = self.get_client({})
        job = Job.fetch('test_type', api)
        with self.assertRaises(UClientError):
            job.claim()


class TestJob(BaseTestWithInsertedJob):

    def test_job(self):
        """Test fetch, claim and update status/output"""
        api = self.get_client()

        r = api.get_job_list()
        self.assertEqual(r.status_code, 200)

        job = Job.fetch('test_type', api)
        self.assertFalse(job.claimed)
        job.claim()
        self.assertTrue(job.claimed)
        job.claim()
        self.assertTrue(job.claimed)

        job.send_status('Claimed job')

        self.assertEqual(job.url_source, self.TEST_URL)
        self.assertEqual(job.url_target, self.TEST_URL)

        job.send_status("Got data")

        api.update_output(job.url_output, "Processing...")
        job.send_status("Work done")
