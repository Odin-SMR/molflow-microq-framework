import unittest
import requests
from uservice.datamodel import jsonmodels


class TestAdmin(unittest.TestCase):
    def setUp(self):
        self._apiroot = "http://localhost:5000/rest_api"

    def test_adding_user(self):
        """Test adding a new user"""
        print "test_adding_user not implemented!"
        self.assertTrue(False)

    def test_user_password_authentication(self):
        """Test authenticating by user and password"""
        r = requests.post(self._apiroot + "/v4/jobs/42", json="42",
                          headers={'Content-Type': "application/json"},
                          auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)

        r = requests.post(self._apiroot + "/v4/jobs/42", json="42",
                          headers={'Content-Type': "application/json"},
                          auth=("worker1", "sqd"))
        self.assertEqual(r.status_code, 401)

    def test_token_authentication(self):
        """Test authenticating by token"""
        r = requests.post(self._apiroot + "/v4/jobs/42", json="42",
                          headers={'Content-Type': "application/json"},
                          token=42)
        self.assertEqual(r.status_code, 200)


class TestBasicViews(unittest.TestCase):
    def setUp(self):
        self._apiroot = "http://localhost:5000/rest_api"

    def test_list_jobs(self):
        """Test requesting list of jobs."""
        r = requests.get(self._apiroot + "/v4/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["Jobs"]), 482)

    def test_get_job_from_list_jobs(self):
        """Test getting a job from the list of jobs."""
        r0 = requests.get(self._apiroot + "/v4/jobs")
        r1 = requests.get(r0.json()["Jobs"][0]["URLS"]["URL-log"])
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["Info"]["ScanID"], 7002887494)

    def test_fetch_job(self):
        """Test requesting a free job."""
        r = requests.get(self._apiroot + "/v4/jobs/fetch")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["Job"]["ScanID"], 7002887494)


class TestJobViews(unittest.TestCase):
    def setUp(self):
        self._apiroot = "http://localhost:5000/rest_api"

    def test_update_job_status(self):
        """Test updating job status."""
        job = requests.get(self._apiroot + "/v4/jobs/fetch")
        r = requests.post(job.json()["Job"]["URLS"]["URL-status"],
                          json={"Message": "Testing status update."},
                          headers={'Content-Type': "application/json"},
                          auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)

    def test_claim_job(self):
        """Test claiming a job."""
        job = requests.get(self._apiroot + "/v4/jobs/fetch")
        r = requests.put(job.json()["Job"]["URLS"]["URL-claim"],
                         auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)

    def test_get_data(self):
        """Test getting data to process."""
        job = requests.get(self._apiroot + "/v4/jobs/fetch")
        r = requests.get(job.json()["Job"]["URLS"]["URL-spectra"])
        data = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(data), 35)

    def test_deliver_job_bad(self):
        """Test delivering bad job."""
        job = requests.get(self._apiroot + "/v4/jobs/fetch")
        r = requests.post(job.json()["Job"]["URLS"]["URL-deliver"],
                          json={"Message": "This is invalid data."},
                          headers={'Content-Type': "application/json"},
                          auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 400)

    def test_deliver_job_good(self):
        """Test delivering good job."""
        job = requests.get(self._apiroot + "/v4/jobs/fetch")
        r = requests.post(job.json()["Job"]["URLS"]["URL-deliver"],
                          json=jsonmodels.l2i_prototype,
                          headers={'Content-Type': "application/json"},
                          auth=("worker1", "sqrrl"))
        self.assertEqual(r.status_code, 200)
