import os
import unittest
import requests

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')


class BaseTest(unittest.TestCase):

    TEST_URL = 'http://example.com'

    _apiroot = "http://localhost:5000/rest_api"
    _project = 'project'
    _username = 'worker1'
    _password = 'sqrrl'

    @classmethod
    def setUpClass(cls):
        # TODO: Use mysql and add first user directly to db instead.
        #       Create user endpoint should need auth.
        r = requests.post(cls._apiroot + "/admin/users",
                          headers={'Content-Type': "application/json"},
                          json={"username": cls._username,
                                "password": cls._password})
        assert r.status_code == 400, r.status_code

    @classmethod
    def tearDownClass(cls):
        cls._delete_test_project()

    @classmethod
    def _delete_test_project(cls):
        requests.delete(
            cls._apiroot + '/v4/{}'.format(cls._project),
            auth=(cls._username, cls._password))

    @property
    def _auth(self):
        return (self._username, self._password)

    @classmethod
    def _insert_test_jobs(cls):
        jobs = [
            {'id': '42', 'type': 'test_type',
             'source_url': cls.TEST_URL,
             'target_url': cls.TEST_URL}
        ]
        # TODO: Only inserting one job because authentication takes ~0.5 secs
        for job in jobs[:1]:
            status_code = cls._insert_job(job)
            assert status_code == 201, status_code

    @classmethod
    def _insert_job(cls, job):
        r = requests.post(
            cls._apiroot + '/v4/{}/jobs'.format(cls._project),
            json=job, auth=(cls._username, cls._password))
        return r.status_code


class BaseInsertedJobs(BaseTest):

    @classmethod
    def setUpClass(cls):
        super(BaseInsertedJobs, cls).setUpClass()
        cls._insert_test_jobs()
