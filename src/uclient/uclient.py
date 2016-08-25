#! /usr/bin/env python
import json
import requests
import argparse as ap


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

    def __init__(self, apiroot, username=None, password=None,
                 credentials_file=None, verbose=False):
        self.uri = apiroot.strip('/')
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
        return self._call_api(self.uri + "/v4/jobs")

    def fetch_job(self):
        """Request an unprocessed job from server."""
        return self._call_api(self.uri + "/v4/jobs/fetch")

    def claim_job(self, url, worker_name, token=None):
        """Claim job from server"""
        # TODO: Worker node info
        return self._call_api(url, 'PUT', data={"worker": worker_name},
                              auth=self.auth)

    def get_data(self, url):
        """Get data to work with"""
        return self._call_api(url)

    def update_status(self, url, status, token=None):
        """Update status of job."""
        return self._call_api(url, 'POST', json=status,
                              headers={'Content-Type': "application/json"},
                              auth=self.auth)

    def deliver_job(self, url, result, token=None):
        """Deliver finished job."""
        return self._call_api(url, 'POST', json=result,
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
    def fetch(cls, api):
        r = api.fetch_job()
        return cls(r.json(), api)

    @property
    def url_claim(self):
        return self.data["Job"]["URLS"]["URL-claim"]

    @property
    def url_status(self):
        return self.data["Job"]["URLS"]["URL-status"]

    @property
    def url_spectra(self):
        return self.data["Job"]["URLS"]["URL-spectra"]

    @property
    def url_deliver(self):
        return self.data["Job"]["URLS"]["URL-deliver"]

    def claim(self, worker='anonymous'):
        if self.claimed:
            return
        try:
            self.api.claim_job(self.url_claim, worker)
            self.claimed = True
        except UClientError:
            raise

    def send_status(self, msg):
        self.api.update_status(self.url_status, {'Message': msg})

if __name__ == "__main__":
    # TODO: Move to worker's main.
    parser = ap.ArgumentParser()
    parser.add_argument('-u', "--user", help="user name")
    parser.add_argument('-p', "--password", default="", help="user password")
    parser.add_argument('-c', "--credentials", default="credentials.json",
                        help="credentials file to load")
    parser.add_argument('-a', "--apiroot",
                        default="http://localhost:5000/rest_api",
                        help="URI of the API root")
    parser.add_argument('-v', "--verbose", help="use verbose output",
                        action="store_true")
    args = parser.parse_args()
    api = UClient(args.apiroot, args.user, args.password, args.credentials,
                  verbose=args.verbose)
