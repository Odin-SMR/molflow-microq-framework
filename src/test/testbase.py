import os
import unittest
import requests

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')


class BaseTest(unittest.TestCase):

    TEST_URL = 'http://example.com'

    _apiroot = "http://localhost:5000/rest_api"
    _adminuser = 'admin'
    _adminpw = 'sqrrl'
    _project = 'project'
    _username = 'worker1'
    _password = 'sqrrl'
    _token = None

    @classmethod
    def tearDownClass(cls):
        cls._delete_test_project()

    @classmethod
    def _delete_test_project(cls, project=None):
        requests.delete(
            cls._apiroot + '/v4/{}'.format(project or cls._project),
            auth=(cls._token or cls._username, cls._password))

    @property
    def _auth(self):
        if self._token:
            return (self._token, '')
        return (self._username, self._password)

    @classmethod
    def _insert_test_jobs(cls, project=None):
        jobs = [
            {'id': '42', 'type': 'test_type',
             'source_url': cls.TEST_URL,
             'target_url': cls.TEST_URL}
        ]
        # TODO: Only inserting one job because authentication takes ~0.5 secs
        for job in jobs[:1]:
            status_code = cls._insert_job(job, project=project)
            assert status_code == 201, status_code

    @classmethod
    def _insert_job(cls, job, project=None):
        """Insert job and set status"""
        job = job.copy()
        id = job['id']
        worker = job.pop('worker', cls._username)
        processing_time = job.pop('processing_time', 0)
        added = job.pop('added_timestamp', None)
        claimed = job.pop('claimed_timestamp', None)
        finished = job.pop('finished_timestamp', None)
        failed = job.pop('failed_timestamp', None)
        auth = (cls._token or cls._username, cls._password)
        job.pop('claimed', None)
        job.pop('current_status', None)
        r = requests.post(
            cls._apiroot + '/v4/{}/jobs{}'.format(
                project or cls._project,
                ('?now=' + added) if added else ''),
            json=job, auth=auth)
        if r.status_code != 201:
            return r.status_code
        if claimed:
            data = {'Worker': worker}
            r_ = requests.put(
                cls._apiroot + '/v4/{}/jobs/{}/claim?now={}'.format(
                    project or cls._project, id, claimed),
                auth=auth, json=data)
            assert r_.status_code == 200, r_.status_code
        if finished or failed:
            if finished:
                status = {'Status': 'FINISHED'}
            else:
                status = {'Status': 'FAILED'}
            status['ProcessingTime'] = processing_time
            r_ = requests.put(
                cls._apiroot + '/v4/{}/jobs/{}/status?now={}'.format(
                    project or cls._project, id, finished or failed),
                auth=auth, json=status)
            assert r_.status_code == 200, r_.status_code
        return r.status_code

    @classmethod
    def _insert_worker_user(cls):
        r = requests.post(cls._apiroot + "/admin/users",
                          headers={'Content-Type': "application/json"},
                          json={"username": cls._username,
                                "password": cls._password},
                          auth=(cls._adminuser, cls._adminpw))
        assert r.status_code == 201, r.status_code
        return r.json()['userid']

    @classmethod
    def _get_worker_token(cls):
        r = requests.get(cls._apiroot + "/token",
                         auth=(cls._username, cls._password))
        assert r.status_code == 200, r.status_code
        return r.json()['token']

    @classmethod
    def _delete_user(cls, userid):
        requests.delete(cls._apiroot + "/admin/users/{}".format(userid),
                        auth=(cls._adminuser, cls._adminpw))


class BaseWithWorkerUser(BaseTest):

    @classmethod
    def setUpClass(cls):
        super(BaseWithWorkerUser, cls).setUpClass()
        cls.worker_userid = cls._insert_worker_user()
        cls._token = cls._get_worker_token()

    @classmethod
    def tearDownClass(cls):
        super(BaseWithWorkerUser, cls).tearDownClass()
        cls._delete_user(cls.worker_userid)
        cls._token = None


class BaseInsertedJobs(BaseWithWorkerUser):

    @classmethod
    def setUpClass(cls):
        super(BaseInsertedJobs, cls).setUpClass()
        cls._insert_test_jobs()
