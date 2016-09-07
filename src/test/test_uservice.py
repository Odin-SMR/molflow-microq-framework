import requests
from test.testbase import BaseTest, BaseWithWorkerUser, BaseInsertedJobs


class TestAdmin(BaseTest):

    def test_adding_user(self):
        """Test adding and deleting a user"""
        # Try to add with empty username
        r = requests.post(self._apiroot + "/admin/users",
                          auth=("admin", "sqrrl"),
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
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)

        r = requests.put(self._apiroot + "/v4/project/jobs/42/status",
                         json={"Status": "42"},
                         headers={'Content-Type': "application/json"},
                         auth=("worker1", "sqd"))
        self.assertEqual(r.status_code, 401)

    def test_token_authentication(self):
        """Test authenticating by token"""
        r0 = requests.get(self._apiroot + "/token", auth=self._auth)
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

    def test_fetch_job(self):
        """Test requesting a free job."""
        r = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["Job"]["JobID"], '42')


class TestJobViews(BaseWithWorkerUser):

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
                         auth=self._auth)
        self.assertEqual(r.status_code, 400)
        r = requests.put(job.json()["Job"]["URLS"]["URL-status"],
                         json={"Status": "Testing status update."},
                         headers={'Content-Type': "application/json"},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)

    def test_claim_job(self):
        """Test claiming a job."""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         json={'BadWorker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 400)

        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)
        # Should not be able to claim same job again
        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 409)
        # Should be able to claim after release of job
        r = requests.delete(job.json()["Job"]["URLS"]["URL-claim"],
                            auth=self._auth)
        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         json={'Worker': self._username},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)

    def test_update_job_output(self):
        """Test updating job output"""
        job = requests.get(self._apiroot + "/v4/project/jobs/fetch")
        r = requests.put(job.json()["Job"]["URLS"]["URL-output"],
                         json={"BadOutput": "Testing output update."},
                         headers={'Content-Type': "application/json"},
                         auth=self._auth)
        self.assertEqual(r.status_code, 400)
        r = requests.put(job.json()["Job"]["URLS"]["URL-output"],
                         json={"Output": "Testing output update."},
                         headers={'Content-Type': "application/json"},
                         auth=self._auth)
        self.assertEqual(r.status_code, 200)
