import requests
from uservice.datamodel import jsonmodels
from test.testbase import BaseTest, BaseInsertedJobs


class TestAdmin(BaseTest):

    @classmethod
    def setUpClass(cls):
        super(TestAdmin, cls).setUpClass()
        cls._insert_job({'id': '42', 'type': 'test_type'})

    def test_adding_user(self):
        """Test adding a new user"""
        r = requests.post(self._apiroot + "/admin/users",
                          auth=("skymandr", "42"),
                          headers={'Content-Type': "application/json"},
                          json={"username": "worker1", "password": "sqrrl"})
        # TODO: Empty user database in setUp/tearDown
        self.assertEqual(r.status_code, 400)

    def test_user_password_authentication(self):
        """Test authenticating by user and password"""
        r = requests.put(self._apiroot + "/v4/project/jobs/42/status",
                         json={"Status": "42"},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)

        r = requests.put(self._apiroot + "/v4/project/jobs/42/status",
                         json={"Status": "42"},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqd"))
        self.assertEqual(r.status_code, 401)

    def test_token_authentication(self):
        """Test authenticating by token"""
        r0 = requests.get(self._apiroot + "/token", auth=("worker1", "sqrrl"))
        token = r0.json()["token"]
        r1 = requests.put(self._apiroot + "/v4/project/jobs/42/status",
                          json={"Status": "42"},
                          headers={'Content-Type': "application/json"},
                          auth=(token, ""))
        self.assertEqual(r0.status_code, 200)
        self.assertEqual(r1.status_code, 200)


class TestBasicViews(BaseInsertedJobs):

    def test_list_jobs(self):
        """Test requesting list of jobs."""
        r = requests.get(self._apiroot + "/v4/project/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), 1)

    def test_get_job_from_list_jobs(self):
        """Test getting a job from the list of jobs."""
        r0 = requests.get(self._apiroot + "/v4/project/jobs")
        # TODO: Do not fetch from malachite
        r1 = requests.get(r0.json()["Jobs"][0]["URLS"]["URL-log"])
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["Info"]["ScanID"], 7002887494)

    def test_fetch_job(self):
        """Test requesting a free job."""
        r = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["Job"]["ScanID"], 7002887494)


class TestJobViews(BaseTest):

    def setUp(self):
        self._delete_test_project()
        self._insert_test_jobs()

    def tearDown(self):
        self._delete_test_project()

    def test_update_job_status(self):
        """Test updating job status."""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        r = requests.put(job.json()["Job"]["URLS"]["URL-status"],
                         json={"BadStatus": "Testing status update."},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 400)
        r = requests.put(job.json()["Job"]["URLS"]["URL-status"],
                         json={"Status": "Testing status update."},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)

    def test_claim_job(self):
        """Test claiming a job."""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         json={'BadWorker': self._username},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 400)

        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)
        # Should not be able to claim same job again
        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 409)
        # Should be able to claim after release of job
        r = requests.delete(job.json()["Job"]["URLS"]["URL-claim"],
                            auth=("worker1", "sqrrl"))
        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)

    def test_get_data(self):
        """Test getting data to process."""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        r = requests.get(job.json()["Job"]["URLS"]["URL-input"])
        data = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(data), 35)

    def test_update_job_output(self):
        """Test updating job output"""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        r = requests.put(job.json()["Job"]["URLS"]["URL-output"],
                         json={"BadOutput": "Testing output update."},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 400)
        r = requests.put(job.json()["Job"]["URLS"]["URL-output"],
                         json={"Output": "Testing output update."},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)

    def test_deliver_job_bad(self):
        """Test delivering bad job."""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        r = requests.put(job.json()["Job"]["URLS"]["URL-result"],
                         json={"Message": "This is invalid data."},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 400)

    def test_deliver_job_good(self):
        """Test delivering good job."""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        r = requests.put(job.json()["Job"]["URLS"]["URL-result"],
                         json=jsonmodels.l2i_prototype,
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)
