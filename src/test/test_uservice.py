import urllib
from datetime import datetime, timedelta

import requests
from test.testbase import BaseTest, BaseWithWorkerUser, BaseInsertedJobs


class BaseJobsTest(BaseWithWorkerUser):

    JOBS = [
        {'id': '1',
         'type': 'test',
         'source_url': BaseTest.TEST_URL,
         'worker': 'worker1',
         'added_timestamp': '2000-01-01 10:00',
         'claimed_timestamp': '2000-01-01 10:00',
         'finished_timestamp': '2000-01-01 10:00',
         'current_status': 'FINISHED',
         'processing_time': 300
         },
        {'id': '2',
         'type': 'test',
         'source_url': BaseTest.TEST_URL,
         'worker': 'worker2',
         'added_timestamp': '2000-01-01 10:00',
         'claimed_timestamp': '2000-01-01 10:00',
         'failed_timestamp': '2000-01-01 10:00',
         'current_status': 'FAILED',
         'processing_time': 200
         },
        {'id': '3',
         'type': 'test',
         'source_url': BaseTest.TEST_URL,
         'worker': 'worker1',
         'added_timestamp': '2000-01-01 10:00',
         'claimed_timestamp': '2000-01-01 11:00',
         'finished_timestamp': '2000-01-01 11:00',
         'current_status': 'FINISHED',
         'processing_time': 300
         },
        {'id': '4',
         'type': 'test',
         'source_url': BaseTest.TEST_URL,
         'added_timestamp': '2000-01-01 10:00',
         }
    ]

    @classmethod
    def setUpClass(cls):
        super(BaseJobsTest, cls).setUpClass()
        try:
            for job in cls.JOBS:
                status_code = cls._insert_job(job)
                assert status_code == 201, status_code
        except Exception as e:
            super(BaseJobsTest, cls).tearDownClass()
            raise e


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
        try:
            status_code = cls._insert_job(
                {'id': '42', 'type': 'test_type',
                 'source_url': BaseTest.TEST_URL})
            assert status_code == 201, status_code
        except Exception as e:
            super(TestAuthentication, cls).tearDownClass()
            raise e

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
        self.maxDiff = None
        self.assertEqual(r.json()["Job"], {
            u'JobID': u'42',
            u'Environment': {},
            u'URLS': {
                u'URL-image': None,
                u'URL-source': BaseTest.TEST_URL,
                u'URL-target': BaseTest.TEST_URL,
                u'URL-claim': self._apiroot + u'/v4/project/jobs/42/claim',
                u'URL-output': self._apiroot + u'/v4/project/jobs/42/output',
                u'URL-status': self._apiroot + u'/v4/project/jobs/42/status'
            }})

        project_data = {'environment': {'v': 1},
                        'processing_image_url': BaseTest.TEST_URL + '/image'}
        r = requests.put(self._apiroot + '/v4/project',
                         json=project_data, auth=self._auth)
        self.assertEqual(r.status_code, 204)

        r = requests.get(self._apiroot + "/v4/project/jobs/fetch",
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)
        self.maxDiff = None
        self.assertEqual(r.json()["Job"], {
            u'JobID': u'42',
            u'Environment': {'v': 1},
            u'URLS': {
                u'URL-image': BaseTest.TEST_URL + '/image',
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
         'view_result_url': BaseTest.TEST_URL + '/view_result'},
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

    def test_bad_job_insert(self):
        """Test requests with bad job fields"""
        bad_jobs = [
            # Missing input_url
            {'id': '1'},
            # Unsupported field
            {'id': '1', 'input_url': BaseTest.TEST_URL, 'unknown': 's'}
        ]
        for job in bad_jobs:
            self.assertEqual(self._insert_job(job), 400)

    def test_list_all(self):
        """Test requesting list of jobs without parameters."""
        r = requests.get(self._apiroot + "/v4/project/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), len(self.JOBS))

    def test_job_contents(self):
        """Test that listed jobs have the correct contents"""
        r = requests.get(self._apiroot + "/v4/project/jobs?status=available")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), 1)
        job = r.json()["Jobs"][0]
        job.pop('Added')
        self.maxDiff = None
        self.assertEqual(job, {
            'Id': '1',
            'Type': 'test_type',
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
                'URL-Result': BaseTest.TEST_URL + '/view_result'}})

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
        self._delete_test_project(project='other')
        self._delete_test_project(project='nojobs')

        r = requests.get(self._apiroot + "/v4/projects")
        self.assertEqual(r.status_code, 200)
        self.nr_orig_projects = len(r.json()['Projects'])

        r = requests.get(self._apiroot + "/v4/projects?only_active=1")
        self.assertEqual(r.status_code, 200)
        self.nr_orig_active_projects = len(r.json()['Projects'])
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

        r = requests.get(self._apiroot + "/v4/projects?only_active=1")
        self.assertEqual(r.status_code, 200)
        projects = r.json()['Projects']
        self.assertEqual(len(projects) - self.nr_orig_active_projects, 2)


class TestProjectsPrio(BaseJobsTest):

    def setUp(self):
        self._delete_test_project(project='myproject')

    def tearDown(self):
        self._delete_test_project(project='myproject')

    def _get_project(self, project='project'):
        r = requests.get(self._apiroot + "/v4/projects")
        self.assertEqual(r.status_code, 200)
        for p in r.json()['Projects']:
            if p['Id'] == project:
                return p

    def test_projects_prio_score(self):
        """Test calculation of prio score"""
        # Prio should be 1 when no deadline
        r = requests.put(self._apiroot + "/v4/project", auth=self._auth,
                         json={'deadline': None})
        self.assertEqual(r.status_code, 204)

        self.assertEqual(self._get_project()['PrioScore'], 1)

        # Deadline passed
        r = requests.put(self._apiroot + "/v4/project", auth=self._auth,
                         json={'deadline': '2011-01-01 10:00'})
        self.assertEqual(r.status_code, 204)

        prio_deadline_passed = self._get_project()['PrioScore']
        self.assertAlmostEqual(prio_deadline_passed, 800/3.)

        # Future deadline
        r = requests.put(
            self._apiroot + "/v4/project", auth=self._auth,
            json={'deadline': (
                datetime.utcnow() + timedelta(seconds=100)).isoformat()})
        self.assertEqual(r.status_code, 204)

        prio_future_deadline = self._get_project()['PrioScore']
        self.assertAlmostEqual(
            prio_future_deadline, prio_deadline_passed/100, 1)

        # Prio should be zero when no jobs are available
        r = requests.put(self._apiroot + "/v4/myproject", auth=self._auth,
                         json={'name': 'My Project',
                               'deadline': '2011-01-01 10:00'})
        self.assertEqual(r.status_code, 201)
        prio_no_jobs = self._get_project('myproject')['PrioScore']
        self.assertAlmostEqual(prio_no_jobs, 0)

    def test_fetch_job_prio(self):
        """Test fetch of job from any project weighted by prio score"""
        # Project with one available job, but no processed jobs and deadline
        # passed
        status_code = self._insert_job(
            {'id': '1', 'source_url': BaseTest.TEST_URL}, 'myproject')
        self.assertEqual(status_code, 201)
        r = requests.put(self._apiroot + "/v4/myproject", auth=self._auth,
                         json={'deadline': '2011-01-01 10:00'})
        self.assertEqual(r.status_code, 204)

        r = requests.put(self._apiroot + "/v4/project", auth=self._auth,
                         json={'deadline': '2011-01-01 10:00'})
        self.assertEqual(r.status_code, 204)

        # Prio scores
        self.assertAlmostEqual(self._get_project()['PrioScore'], 800/3.)
        self.assertAlmostEqual(
            self._get_project('myproject')['PrioScore'], 3600)

        project_count = {'project': 0, 'myproject': 0}

        for _ in xrange(100):
            r = requests.get(self._apiroot + "/v4/projects/jobs/fetch",
                             auth=self._auth)
            self.assertEqual(r.status_code, 200)
            project_count[r.json()['Project']] += 1

        # p_project = (800/3)/(800/3 + 3600) = 0.069
        # Probability to get zero jobs from project:
        # binom.pmf(0, 100, p_project) = 0.0008
        self.assertGreater(project_count['project'], 0)
        self.assertGreater(
            project_count['myproject'], project_count['project'])


class TestUpdateProject(BaseWithWorkerUser):

    def setUp(self):
        self._delete_test_project(project='myproject')

    def tearDown(self):
        self._delete_test_project(project='myproject')

    def _get_my_project(self):
        r = requests.get(self._apiroot + "/v4/projects")
        self.assertEqual(r.status_code, 200)
        for p in r.json()['Projects']:
            if p['Id'] == 'myproject':
                return p

    def test_update_project(self):
        """Test create and update project"""
        self.maxDiff = None
        r = requests.put(self._apiroot + "/v4/myproject", auth=self._auth,
                         json={'name': 'My Project'})
        self.assertEqual(r.status_code, 201)

        p = self._get_my_project()
        self.assertTrue(isinstance(p.pop('CreatedAt'), basestring))
        self.assertEqual(p, {
            u'Id': u'myproject',
            u'Name': u'My Project',
            u'Environment': {},
            u'CreatedBy': self._username,
            u'LastJobAddedAt': None,
            u'NrJobsAdded': 0,
            u'LastJobClaimedAt': None,
            u'NrJobsClaimed': 0,
            u'Deadline': None,
            u'NrJobsFinished': 0,
            u'NrJobsFailed': 0,
            u'TotalProcessingTime': 0.0,
            u'PrioScore': 0.0,
            u'URLS': {
                u'URL-Status': self._apiroot + '/v4/myproject',
                u'URL-Processing-image': None
            }
        })

        r = requests.put(self._apiroot + "/v4/myproject", auth=self._auth,
                         json={'name': 'Your Project',
                               'deadline': '2001-01-01 10:00',
                               'processing_image_url': self.TEST_URL,
                               'environment': {'var': 10}})
        self.assertEqual(r.status_code, 204)

        p = self._get_my_project()
        self.assertTrue(isinstance(p.pop('CreatedAt'), basestring))
        self.assertEqual(p, {
            u'Id': u'myproject',
            u'Name': u'Your Project',
            u'Environment': {'var': 10},
            u'CreatedBy': self._username,
            u'LastJobAddedAt': None,
            u'NrJobsAdded': 0,
            u'LastJobClaimedAt': None,
            u'NrJobsClaimed': 0,
            u'Deadline': u'2001-01-01T10:00:00',
            u'NrJobsFinished': 0,
            u'NrJobsFailed': 0,
            u'TotalProcessingTime': 0.0,
            u'PrioScore': 0.0,
            u'URLS': {
                u'URL-Status': self._apiroot + '/v4/myproject',
                u'URL-Processing-image': self.TEST_URL
            }
        })

        # Not allowed to update some data
        r = requests.put(self._apiroot + "/v4/myproject", auth=self._auth,
                         json={'created_by_user': 'cannot_do_this'})
        self.assertEqual(r.status_code, 400)


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

    def _get_nr_claimed(self):
        project_info = requests.get(self._apiroot + "/v4/project").json()
        return project_info['NrJobsClaimed']

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
        self.assertEqual(self._get_nr_claimed(), 1)
        # Should not be able to claim same job again
        r = requests.put(job["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self._get_nr_claimed(), 1)
        # Should be able to claim after release of job
        r = requests.delete(job["Job"]["URLS"]["URL-claim"],
                            auth=self._auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._get_nr_claimed(), 0)
        r = requests.put(job["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._get_nr_claimed(), 1)

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
            u'Version': u'v4',
            u'Project': u'project',
            u'Name': u'project',
            u'CreatedBy': u'worker1',
            u'Id': u'project',
            u'ETA': u'0:30:00',
            u'Environment': {},
            u'NrJobsAdded': 4,
            u'NrJobsClaimed': 3,
            u'NrJobsFailed': 1,
            u'NrJobsFinished': 2,
            u'Deadline': None,
            u'PrioScore': None,
            u'TotalProcessingTime': 800.0,
            u'JobStates': {u'Available': 1, u'Failed': 1, u'Finished': 2},
            u'URLS': {
                u'URL-DailyCount': (
                    u'http://localhost:5000/rest_api/v4/project/jobs/count?'
                    u'period=daily'),
                u'URL-Jobs': (
                    u'http://localhost:5000/rest_api/v4/project/jobs'),
                u'URL-Workers': (
                    u'http://localhost:5000/rest_api/v4/project/workers'),
                u'URL-Status': u'http://localhost:5000/rest_api/v4/project',
                u'URL-Processing-image': None
            }
        }
        data = r.json()
        data.pop('LastJobAddedAt')
        data.pop('LastJobClaimedAt')
        data.pop('CreatedAt')
        self.assertEqual(data, expected)
