import urllib

import requests
from test.testbase import BaseTest, BaseWithWorkerUser, BaseInsertedJobs


class BaseJobsTest(BaseWithWorkerUser):

    JOBS = [
        {'id': '1',
         'type': 'test',
         'worker': 'worker1',
         'added_timestamp': '2000-01-01 10:00',
         'claimed_timestamp': '2000-01-01 10:00',
         'finished_timestamp': '2000-01-01 10:00',
         'current_status': 'FINISHED'
         },
        {'id': '2',
         'type': 'test',
         'worker': 'worker2',
         'added_timestamp': '2000-01-01 10:00',
         'claimed_timestamp': '2000-01-01 10:00',
         'failed_timestamp': '2000-01-01 10:00',
         'current_status': 'FAILED'
         },
        {'id': '3',
         'type': 'test',
         'worker': 'worker1',
         'added_timestamp': '2000-01-01 10:00',
         'claimed_timestamp': '2000-01-01 11:00',
         'finished_timestamp': '2000-01-01 11:00',
         'current_status': 'FINISHED'
         },
        {'id': '4',
         'type': 'test',
         'added_timestamp': '2000-01-01 10:00',
         }
    ]

    @classmethod
    def setUpClass(cls):
        super(BaseJobsTest, cls).setUpClass()
        for job in cls.JOBS:
            assert cls._insert_job(job) == 201


class TestAdmin(BaseTest):

    def test_adding_user(self):
        """Test adding and deleting a user"""
        # Try to add with empty username
        r = requests.post(self._apiroot + "/admin/users",
                          auth=(self._adminuser, self._adminpw),
                          headers={'Content-Type': "application/json"},
                          json={"username": "", "password": "sqrrl"})
        self.assertEqual(r.status_code, 400)

        # Try to add a valid user
        r = requests.post(self._apiroot + "/admin/users",
                          auth=(self._adminuser, self._adminpw),
                          headers={'Content-Type': "application/json"},
                          json={"username": "myworker", "password": "sqrrl"})
        self.assertEqual(r.status_code, 201)
        userid = r.json()['userid']

        # Try to add same user again
        r = requests.post(self._apiroot + "/admin/users",
                          auth=(self._adminuser, self._adminpw),
                          headers={'Content-Type': "application/json"},
                          json={"username": "myworker", "password": "sqrrl"})
        self.assertEqual(r.status_code, 400)

        # Try to add new user with none admin user
        r = requests.post(self._apiroot + "/admin/users",
                          auth=("myworker", "sqrrl"),
                          headers={'Content-Type': "application/json"},
                          json={"username": "other", "password": "sqrrl"})
        self.assertEqual(r.status_code, 403)

        r = requests.delete(self._apiroot + "/admin/users/{}".format(userid),
                            auth=(self._adminuser, self._adminpw))
        self.assertEqual(r.status_code, 204)


class TestAuthentication(BaseWithWorkerUser):

    @classmethod
    def setUpClass(cls):
        super(TestAuthentication, cls).setUpClass()
        cls._insert_job({'id': '42', 'type': 'test_type'})

    def test_user_password_authentication(self):
        """Test authenticating by user and password"""
        r = requests.put(self._apiroot + "/v4/project/jobs/42/status",
                         json={"Status": "42"},
                         headers={'Content-Type': "application/json"},
                         auth=(self._username, self._password))
        self.assertEqual(r.status_code, 200)

        r = requests.put(self._apiroot + "/v4/project/jobs/42/status",
                         json={"Status": "42"},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqd"))
        self.assertEqual(r.status_code, 401)

    def test_token_authentication(self):
        """Test authenticating by token"""
        r0 = requests.get(self._apiroot + "/token",
                          auth=(self._username, self._password))
        token = r0.json()["token"]
        r1 = requests.put(self._apiroot + "/v4/project/jobs/42/status",
                          json={"Status": "42"},
                          headers={'Content-Type': "application/json"},
                          auth=(token, ""))
        self.assertEqual(r0.status_code, 200)
        self.assertEqual(r1.status_code, 200)


class TestFetchJob(BaseInsertedJobs):

    def test_fetch_job(self):
        """Test requesting a free job."""
        # Should need auth
        r = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        self.assertEqual(r.status_code, 401)

        r = requests.get(self._apiroot + "/v4/project/jobs/fetch",
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["Job"]["JobID"], '42')
        self.maxDiff = None
        self.assertEqual(r.json()["Job"], {
            u'JobID': u'42',
            u'Environment': {},
            u'URLS': {
                u'URL-image': BaseTest.TEST_URL,
                u'URL-source': BaseTest.TEST_URL,
                u'URL-target': BaseTest.TEST_URL,
                u'URL-claim': self._apiroot + u'/v4/project/jobs/42/claim',
                u'URL-output': self._apiroot + u'/v4/project/jobs/42/output',
                u'URL-status': self._apiroot + u'/v4/project/jobs/42/status'
            }})


class TestListJobs(BaseJobsTest):

    JOBS = [
        {'id': '1', 'type': 'test_type',
         'source_url': BaseTest.TEST_URL + '/source',
         'target_url': BaseTest.TEST_URL + '/target',
         'view_result_url': BaseTest.TEST_URL + '/view_result',
         'image_url': BaseTest.TEST_URL + '/image',
         'environment': {'env1': 'e1', 'env2': 'e2'}},
        {'id': '2', 'type': 'test_type',
         'source_url': BaseTest.TEST_URL,
         'target_url': BaseTest.TEST_URL,
         'claimed_timestamp': '2016-01-01 10:00',
         'current_status': 'CLAIMED',
         'worker': 'worker1'},
        {'id': '3', 'type': 'test_type',
         'source_url': BaseTest.TEST_URL,
         'target_url': BaseTest.TEST_URL,
         'claimed_timestamp': '2016-01-01 11:00',
         'finished_timestamp': '2016-01-01 11:10',
         'current_status': 'FINISHED',
         'worker': 'worker2'},
        {'id': '4', 'type': 'other_type',
         'source_url': BaseTest.TEST_URL,
         'target_url': BaseTest.TEST_URL,
         'claimed_timestamp': '2016-01-01 12:00',
         'failed_timestamp': '2016-01-01 12:10',
         'current_status': 'FAILED',
         'worker': 'worker2'},
    ]

    def test_bad_requests(self):
        """Test requests with bad parameters"""
        r = requests.get(self._apiroot + "/v4/project/jobs?start=a")
        self.assertEqual(r.status_code, 400)
        # When start/end is used, status must also be provided
        r = requests.get(self._apiroot + "/v4/project/jobs?start=2016-01-01")
        self.assertEqual(r.status_code, 400)
        r = requests.get(self._apiroot + "/v4/project/jobs?status=a")
        self.assertEqual(r.status_code, 400)

    def test_list_all(self):
        """Test requesting list of jobs without parameters."""
        r = requests.get(self._apiroot + "/v4/project/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), len(self.JOBS))

    def test_job_contents(self):
        r = requests.get(self._apiroot + "/v4/project/jobs?status=available")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), 1)
        job = r.json()["Jobs"][0]
        job.pop('Added')
        self.maxDiff = None
        self.assertEqual(job, {
            'Id': '1',
            'Type': 'test_type',
            'Environment': {'env1': 'e1', 'env2': 'e2'},
            'Status': 'AVAILABLE',
            'Claimed': None,
            'IsClaimed': False,
            'Failed': None,
            'Finished': None,
            'Worker': None,
            'URLS': {
                'URL-Input': BaseTest.TEST_URL + '/source',
                'URL-Output': (
                    self._apiroot + '/v4/project/jobs/1/output'),
                'URL-Result': BaseTest.TEST_URL + '/view_result',
                'URL-Image': BaseTest.TEST_URL + '/image'}})

    def test_list_matching(self):
        """Test listing jobs that match provided parameters"""
        tests = [('status=finished', 1),
                 ('worker=worker2', 2),
                 ('type=other_type', 1),
                 ('type=other_type&worker=worker1', 0)]
        for param, expected in tests:
            r = requests.get(self._apiroot + "/v4/project/jobs?{}".format(
                param))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(r.json()["Jobs"]), expected)

    def test_list_period(self):
        """Test listing jobs between start and end time"""
        tests = [('2016-01-01', '2016-01-02', 'claimed', 3),
                 ('2016-01-01 10:00', '2016-01-01 11:00', 'claimed', 1),
                 ('2016-01-01 11:00', '2016-01-01 12:00', 'failed', 0),
                 ('2016-01-01 12:00', '2016-01-01 13:00', 'failed', 1)]
        for start, end, status, expected in tests:
            param = [('status', status),
                     ('start', start),
                     ('end', end)]
            r = requests.get(
                self._apiroot + ("/v4/project/jobs?{}"
                                 "".format(urllib.urlencode(param))))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(r.json()["Jobs"]), expected)


class TestMultipleProjects(BaseWithWorkerUser):

    def setUp(self):
        self._delete_test_project()
        r = requests.get(self._apiroot + "/v4/projects")
        self.assertEqual(r.status_code, 200)
        self.nr_orig_projects = len(r.json()['Projects'])
        self._delete_test_project(project='other')
        jobs = [
            {'id': '42', 'type': 'test_type',
             'source_url': self.TEST_URL,
             'target_url': self.TEST_URL},
            {'id': '44', 'type': 'test_type',
             'source_url': self.TEST_URL,
             'target_url': self.TEST_URL}
        ]
        for job in jobs:
            self._insert_job(job)
        for job in jobs[:1]:
            self._insert_job(job, project='other')
        r = requests.put(self._apiroot + "/v4/nojobs", auth=self._auth)
        self.assertEqual(r.status_code, 201)

    def tearDown(self):
        self._delete_test_project()
        self._delete_test_project(project='other')
        self._delete_test_project(project='nojobs')

    def test_multiple_projects(self):
        """Test that multiple projects work and are separated"""
        r = requests.get(self._apiroot + "/v4/project/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), 2)

        r = requests.get(self._apiroot + "/v4/other/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), 1)

        r = requests.get(self._apiroot + "/v4/nojobs/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), 0)

        r = requests.get(self._apiroot + "/v4/projects")
        self.assertEqual(r.status_code, 200)
        projects = r.json()['Projects']
        self.assertEqual(len(projects) - self.nr_orig_projects, 3)


class TestJobViews(BaseWithWorkerUser):

    def setUp(self):
        self._delete_test_project()
        self._insert_test_jobs()

    def tearDown(self):
        self._delete_test_project()

    def test_update_job_status(self):
        """Test updating job status."""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch",
                           auth=self._auth)
        job = job.json()
        r = requests.put(job["Job"]["URLS"]["URL-status"],
                         json={"BadStatus": "Testing status update."},
                         headers={'Content-Type': "application/json"},
                         auth=self._auth)
        self.assertEqual(r.status_code, 400)
        r = requests.put(job["Job"]["URLS"]["URL-status"],
                         json={"Status": "Testing status update."},
                         headers={'Content-Type': "application/json"},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)

        # Fetch current status
        r = requests.get(self._apiroot + "/v4/project/jobs/{}/status".format(
            job['Job']['JobID']))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Status'], "Testing status update.")

        # Test fetch for none existing job
        r = requests.get(self._apiroot + "/v4/project/jobs/none/status")
        self.assertEqual(r.status_code, 404)

    def test_claim_job(self):
        """Test claiming a job."""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch",
                           auth=self._auth)
        job = job.json()
        r = requests.put(job["Job"]["URLS"]["URL-claim"],
                         json={'BadWorker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 400)

        r = requests.put(job["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)
        # Should not be able to claim same job again
        r = requests.put(job["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 409)
        # Should be able to claim after release of job
        r = requests.delete(job["Job"]["URLS"]["URL-claim"],
                            auth=self._auth)
        r = requests.put(job["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)

        # Fetch current claim data
        r = requests.get(self._apiroot + "/v4/project/jobs/{}/claim".format(
            job['Job']['JobID']))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Claimed'], True)

        # Test fetch for none existing job
        r = requests.get(self._apiroot + "/v4/project/jobs/none/claim")
        self.assertEqual(r.status_code, 404)

    def test_update_job_output(self):
        """Test updating job output"""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch",
                           auth=self._auth)
        job = job.json()
        r = requests.put(job["Job"]["URLS"]["URL-output"],
                         json={"BadOutput": "Testing output update."},
                         headers={'Content-Type': "application/json"},
                         auth=self._auth)
        self.assertEqual(r.status_code, 400)
        r = requests.put(job["Job"]["URLS"]["URL-output"],
                         json={"Output": "Testing output update."},
                         headers={'Content-Type': "application/json"},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)

        # Fetch current output
        r = requests.get(self._apiroot + "/v4/project/jobs/{}/output".format(
            job['Job']['JobID']))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Output'], "Testing output update.")

        # Test fetch for none existing job
        r = requests.get(self._apiroot + "/v4/project/jobs/none/output")
        self.assertEqual(r.status_code, 404)


class TestCountJobs(BaseJobsTest):

    def test_daily_count(self):
        """Test daily count of jobs"""
        self.maxDiff = None
        r = requests.get(
            self._apiroot + "/v4/project/jobs/count")
        self.assertEqual(r.status_code, 200)

        expected = {
            u'Project': 'project',
            u'Version': 'v4',
            u'PeriodType': 'Daily',
            u'Start': None,
            u'End': None,
            u'Counts': [{
                u'ActiveWorkers': 2,
                u'JobsClaimed': 3,
                u'JobsFailed': 1,
                u'JobsFinished': 2,
                u'Period': u'2000-01-01',
                u'URLS': {
                    u'URL-ActiveWorkers': (
                        u'http://localhost:5000/rest_api/v4/project/workers?'
                        u'start=2000-01-01T00%3A00%3A00&'
                        u'end=2000-01-02T00%3A00%3A00'),
                    u'URL-JobsClaimed': (
                        u'http://localhost:5000/rest_api/v4/project/jobs?'
                        u'status=CLAIMED&start=2000-01-01T00%3A00%3A00&'
                        u'end=2000-01-02T00%3A00%3A00'),
                    u'URL-JobsFailed': (
                        u'http://localhost:5000/rest_api/v4/project/jobs?'
                        u'status=FAILED&start=2000-01-01T00%3A00%3A00&'
                        u'end=2000-01-02T00%3A00%3A00'),
                    u'URL-JobsFinished': (
                        u'http://localhost:5000/rest_api/v4/project/jobs?'
                        u'status=FINISHED&start=2000-01-01T00%3A00%3A00&'
                        u'end=2000-01-02T00%3A00%3A00'),
                    u'URL-Zoom': (
                         u'http://localhost:5000/rest_api/v4/project/jobs/'
                         u'count?period=HOURLY&start=2000-01-01T00%3A00%3A00&'
                         u'end=2000-01-02T00%3A00%3A00')}}],
        }
        self.assertEqual(r.json(), expected)

    def test_hourly_count(self):
        """Test hourly count of jobs"""
        self.maxDiff = None
        r = requests.get(
            self._apiroot + "/v4/project/jobs/count?period=hourly")
        self.assertEqual(r.status_code, 200)

        expected = {
            u'Project': 'project',
            u'Version': 'v4',
            u'PeriodType': 'Hourly',
            u'Start': None,
            u'End': None,
            u'Counts': [
                {u'ActiveWorkers': 2,
                 u'JobsClaimed': 2,
                 u'JobsFailed': 1,
                 u'JobsFinished': 1,
                 u'Period': u'2000-01-01 10:00',
                 u'URLS': {
                     u'URL-ActiveWorkers': (
                         u'http://localhost:5000/rest_api/v4/project/workers?'
                         u'start=2000-01-01T10%3A00%3A00&'
                         u'end=2000-01-01T11%3A00%3A00'),
                     u'URL-JobsClaimed': (
                         u'http://localhost:5000/rest_api/v4/project/jobs?'
                         u'status=CLAIMED&start=2000-01-01T10%3A00%3A00&'
                         u'end=2000-01-01T11%3A00%3A00'),
                     u'URL-JobsFailed': (
                         u'http://localhost:5000/rest_api/v4/project/jobs?'
                         u'status=FAILED&start=2000-01-01T10%3A00%3A00&'
                         u'end=2000-01-01T11%3A00%3A00'),
                     u'URL-JobsFinished': (
                         u'http://localhost:5000/rest_api/v4/project/jobs?'
                         u'status=FINISHED&start=2000-01-01T10%3A00%3A00&'
                         u'end=2000-01-01T11%3A00%3A00')}},
                {u'ActiveWorkers': 1,
                 u'JobsClaimed': 1,
                 u'JobsFailed': 0,
                 u'JobsFinished': 1,
                 u'Period': u'2000-01-01 11:00',
                 u'URLS': {
                     u'URL-ActiveWorkers': (
                         u'http://localhost:5000/rest_api/v4/project/workers?'
                         u'start=2000-01-01T11%3A00%3A00&'
                         u'end=2000-01-01T12%3A00%3A00'),
                     u'URL-JobsClaimed': (
                         u'http://localhost:5000/rest_api/v4/project/jobs?'
                         u'status=CLAIMED&start=2000-01-01T11%3A00%3A00&'
                         u'end=2000-01-01T12%3A00%3A00'),
                     u'URL-JobsFinished': (
                         u'http://localhost:5000/rest_api/v4/project/jobs?'
                         u'status=FINISHED&start=2000-01-01T11%3A00%3A00&'
                         u'end=2000-01-01T12%3A00%3A00')}}],
        }
        self.assertEqual(r.json(), expected)

    def test_time_range_count(self):
        """Test count between start and end time"""
        self.maxDiff = None
        param = [
            ('period', 'hourly'),
            ('start', '2000-01-01 10:00'),
            ('end', '2000-01-01 11:00'),
        ]
        r = requests.get("{}/v4/project/jobs/count?{}".format(
            self._apiroot, urllib.urlencode(param)))
        self.assertEqual(r.status_code, 200)

        expected = {
            u'Project': 'project',
            u'Version': 'v4',
            u'PeriodType': 'Hourly',
            u'Start': '2000-01-01T10:00:00',
            u'End': '2000-01-01T11:00:00',
            u'Counts': [
                {u'ActiveWorkers': 2,
                 u'JobsClaimed': 2,
                 u'JobsFailed': 1,
                 u'JobsFinished': 1,
                 u'Period': u'2000-01-01 10:00',
                 u'URLS': {
                     u'URL-ActiveWorkers': (
                         u'http://localhost:5000/rest_api/v4/project/workers?'
                         u'start=2000-01-01T10%3A00%3A00&'
                         u'end=2000-01-01T11%3A00%3A00'),
                     u'URL-JobsClaimed': (
                         u'http://localhost:5000/rest_api/v4/project/jobs?'
                         u'status=CLAIMED&start=2000-01-01T10%3A00%3A00&'
                         u'end=2000-01-01T11%3A00%3A00'),
                     u'URL-JobsFailed': (
                         u'http://localhost:5000/rest_api/v4/project/jobs?'
                         u'status=FAILED&start=2000-01-01T10%3A00%3A00&'
                         u'end=2000-01-01T11%3A00%3A00'),
                     u'URL-JobsFinished': (
                         u'http://localhost:5000/rest_api/v4/project/jobs?'
                         u'status=FINISHED&start=2000-01-01T10%3A00%3A00&'
                         u'end=2000-01-01T11%3A00%3A00')}}]
        }
        self.assertEqual(r.json(), expected)


class TestProjectViews(BaseJobsTest):

    def test_project_status(self):
        """Test get project status"""
        self.maxDiff = None
        r = requests.get(
            self._apiroot + "/v4/project?now=2000-01-01T11%3A00%3A00")
        self.assertEqual(r.status_code, 200)
        expected = {
            u'Version': 'v4',
            u'Project': 'project',
            u'ETA': u'0:30:00',
            u'JobStates': {u'Available': 1, u'Failed': 1, u'Finished': 2},
            u'URLS': {
                u'URL-DailyCount': (
                    u'http://localhost:5000/rest_api/v4/project/jobs/count?'
                    u'period=daily'),
                u'URL-Jobs': (
                    u'http://localhost:5000/rest_api/v4/project/jobs'),
                u'URL-Workers': (
                    u'http://localhost:5000/rest_api/v4/project/workers'),
            }
        }
        self.assertEqual(r.json(), expected)
