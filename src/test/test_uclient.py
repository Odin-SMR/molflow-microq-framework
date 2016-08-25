import json
import unittest
from uclient.uclient import UClient, UClientError, Job


class TestUClient(unittest.TestCase):
    def setUp(self):
        self._apiroot = "http://localhost:5000/rest_api"
        self._mock_results = {"L2i": {
            "BLineOffset": [range(12)] * 4,
            "ChannelId": [range(639)] * 1,
            "FitsSpectrum": [range(639)] * 1,
            "FreqMode": 0,
            "FreqOffset": 0.0,
            "InvMode": "",
            "LOFreq": [range(12)] * 1,
            "MinLmFactor": 0,
            "PointOffset": 0.0,
            "Residual": 0.0,
            "STW": [range(1)] * 12,
            "ScanId": 0,
        }}
        self._credentials = {"username": "worker1",
                             "password": "sqrrl"}

    def get_client(self, credentials=None):
        credentials = (credentials if credentials is not None
                       else self._credentials)
        return UClient(self._apiroot, verbose=True, **credentials)

    def test_api_exception(self):
        """Test api exception"""
        api = self.get_client()
        with self.assertRaises(UClientError):
            api.get_data('bad url')

    def test_credentials_from_file(self):
        """Test load of credentials from file"""
        credentials_file = '/tmp/credentials.json'
        with open(credentials_file, 'w') as out:
            out.write(json.dumps(self._credentials))
        api = self.get_client({'credentials_file': credentials_file})
        job = Job.fetch(api)
        job.send_status('test')

    def test_bad_credentials(self):
        """Test invalid and empty credentials"""
        # The guy below should use different uris:
        credentials = {"username": "snoopy", "password": "ace"}
        api = self.get_client(credentials)
        job = Job.fetch(api)
        with self.assertRaises(UClientError):
            job.claim()

        try:
            job.send_status('evil')
            raise AssertionError('Should have excepted!')
        except UClientError as e:
            self.assertEqual(e.status_code, 401)

        # No credentials provided
        api = self.get_client({})
        job = Job.fetch(api)
        with self.assertRaises(UClientError):
            job.claim()

    def test_job(self):
        """Test fetch, claim and deliver job"""
        api = self.get_client()

        r = api.get_job_list()
        self.assertEqual(r.status_code, 200)

        job = Job.fetch(api)
        self.assertFalse(job.claimed)
        job.claim()
        self.assertTrue(job.claimed)
        job.claim()
        self.assertTrue(job.claimed)

        job.send_status('Claimed job')

        r = api.get_data(job.url_spectra)
        data = r.json()
        self.assertEqual(len(data), 35)

        job.send_status("Got data")

        result = self._mock_results

        job.send_status("Work done")

        r = api.deliver_job(job.url_deliver, result)
        self.assertEqual(r.status_code, 200)

        job.send_status("Work delivered")
