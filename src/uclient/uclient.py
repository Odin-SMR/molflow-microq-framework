#! /usr/bin/env python
import json
import urllib
import requests

from utils.validate import validate_project_name


class UClientError(Exception):
    def __init__(self, reason, status_code=None):
        self.status_code = status_code
        if status_code:
            msg = '{} {}'.format(status_code, reason)
        else:
            msg = reason
        super(UClientError, self).__init__(msg)


class UClient(object):
    """API to the micro service"""

    def __init__(self, apiroot, project, username=None, password=None,
                 credentials_file=None, verbose=False):
        if not validate_project_name(project):
            raise UClientError('Unsupported project name')
        self.uri = apiroot.strip('/')
        self.project = project
        self.project_uri = self.uri + '/v4/{}'.format(project)
        self.verbose = verbose
        self.credentials = self._get_credentials(
            username, password, credentials_file)

    def renew_token():
        """
        Renew token for token based authorization.

        Might not be necessary.
        """
        pass

    def _load_credentials(self, filename="credentials.json"):
        """
        Load credentials from credentials file.

        Not very secure.
        """
        with open(filename) as fp:
            credentials = json.load(fp)
        if self.verbose:
            print("loaded credentials from '{0}'".format(filename))
        return credentials

    def _get_credentials(self, username, password, credentials_file):
        """
        Get credentials from arguments or file.

        If both file and user has been supplied, use the manually entered
        user and password.
        """
        if username is not None:
            return {"username": username, "password": password}
        elif credentials_file is not None:
            return self._load_credentials(credentials_file)
        else:
            return None

    def get_job_list(self):
        """Request list of jobs from server."""
        return self._call_api(self.project_uri + "/jobs")

    def fetch_job(self, job_type=None):
        """Request an unprocessed job from server."""
        url = self.project_uri + "/jobs/fetch"
        if job_type:
            url += '?{}'.format(urllib.urlencode({'type': job_type}))
        return self._call_api(url)

    def claim_job(self, url, worker_name, token=None):
        """Claim job from server"""
        # TODO: Worker node info
        return self._call_api(url, 'PUT', json={"Worker": worker_name},
                              auth=self.auth)

    def get_data(self, url):
        """Get data to work with"""
        return self._call_api(url)

    def update_output(self, url, output, token=None):
        """Update output of job."""
        return self._call_api(url, 'PUT', json={'Output': output},
                              headers={'Content-Type': "application/json"},
                              auth=self.auth)

    def update_status(self, url, status, token=None):
        """Update status of job."""
        return self._call_api(url, 'PUT', json={'Status': status},
                              headers={'Content-Type': "application/json"},
                              auth=self.auth)

    def deliver_job(self, url, result, token=None):
        """Deliver finished job."""
        return self._call_api(url, 'PUT', json=result,
                              headers={'Content-Type': "application/json"},
                              auth=self.auth)

    def _call_api(self, url, method='GET', **kwargs):
        """Call micro service.

        Returns:
           r (requests.Response): The api response.
        Raises:
           UClientError: When api call failes.
        """
        # TODO: retry
        try:
            r = getattr(requests, method.lower())(url, **kwargs)
        except Exception as e:
            # TODO: log exception
            raise UClientError('API call to %r failed: %s' % (url, e))
        if self.verbose:
            print(r.text)
        if r.status_code > 299:
            raise UClientError(r.reason, r.status_code)
        return r

    @property
    def auth(self):
        if not self.credentials:
            raise UClientError('No credentials provided')
        return (self.credentials['username'], self.credentials['password'])


class Job(object):
    def __init__(self, data, api):
        """Init a job.

        Args:
           data (dict): Job data as returned from api.
           api (UClient): API to the micro service.
        """
        self.data = data
        self.api = api
        self.claimed = False

    @classmethod
    def fetch(cls, job_type, api):
        r = api.fetch_job(job_type)
        return cls(r.json(), api)

    @property
    def url_claim(self):
        return self.data["Job"]["URLS"]["URL-claim"]

    @property
    def url_status(self):
        return self.data["Job"]["URLS"]["URL-status"]

    @property
    def url_output(self):
        """Send output from job to this url"""
        return self.data["Job"]["URLS"]["URL-output"]

    @property
    def url_input_data(self):
        return self.data["Job"]["URLS"]["URL-input"]

    @property
    def url_deliver(self):
        return self.data["Job"]["URLS"]["URL-result"]

    def claim(self, worker='anonymous'):
        if self.claimed:
            return
        try:
            self.api.claim_job(self.url_claim, worker)
            self.claimed = True
        except UClientError:
            raise

    def send_status(self, status):
        self.api.update_status(self.url_status, status)

    def send_output(self, output):
        self.api.update_output(self.url_output, output)
