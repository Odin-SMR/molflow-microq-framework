"""Base classes for tests of uService"""
import os
import unittest
import requests
import pytest
from types import StringTypes


class _Any:
    def __eq__(self, other):
        return True


class _AnyString:
    def __eq__(self, other):
        return isinstance(other, StringTypes)


ANY = _Any()
ANY_STRING = _AnyString()

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')


ADMINUSER = 'admin'
ADMINPW = 'sqrrl'
TEST_URL = 'http://example.com'


class ApiSession:
    _adminuser = ADMINUSER
    _adminpw = ADMINPW
    _project = 'project'
    username = 'worker1'
    _password = 'sqrrl'
    _test_jobs = [
        {
            'id': '42', 'type': 'test_type', 'source_url': TEST_URL,
            'target_url': TEST_URL,
        },
    ]

    def __init__(self, microq_service):
        self._apiroot = "{}/rest_api/v4".format(microq_service)
        self._adminroot = "{}/rest_api/admin".format(microq_service)
        self._tokenurl = "{}/rest_api/token".format(microq_service)
        self._projects = []
        self._jobs = []
        self._users = []
        self._token = None

    @property
    def auth(self):
        if self._token:
            return (self._token, '')
        return (self.username, self._password)

    @property
    def token_auth(self):
        return (self._token if self._token else '', '')

    @property
    def user_auth(self):
        return (self.username, self._password)

    @property
    def admin_auth(self):
        return (self._adminuser, self._adminpw)

    def get_projects(self, options=None):
        if options:
            return requests.get("{}/projects?{}".format(
                self._apiroot, options,
            ))

        return requests.get("{}/projects".format(self._apiroot))

    def get_project_url(self, project=None):
        if project is None:
            project = self._project
        return "{}/{}".format(self._apiroot, project)

    def put_project(self, project=None, json=None):
        if project not in self._projects:
            self._projects.append(project)
        return requests.put(
            self.get_project_url(project), auth=self.auth, json=json,
        )

    def delete_projects(self):
        while self._projects:
            self.delete_project(self._projects[0])

    def delete_project(self, project=None):
        r = requests.delete(
            self.get_project_url(project),
            auth=self.auth,
        )
        self._projects.remove(project)
        self._jobs = [j for j in self._jobs if j[0] != project]
        return r

    def get_project(self, project=None, options=None):
        if options:
            return requests.get("{}?{}".format(
                self.get_project_url(project), options
            ))

        return requests.get(self.get_project_url(project))

    def insert_test_jobs(self, project=None):
        for job in self._test_jobs[:1]:
            status_code = self.insert_job(job, project=project)
            assert status_code == 201, status_code

    def insert_job(self, job, project=None):
        """Insert job and set status"""
        if project not in self._projects:
            self._projects.append(project)
        projecturl = self.get_project_url(project)
        job = job.copy()
        id = job['id']
        worker = job.pop('worker', self.username)
        processing_time = job.pop('processing_time', 0)
        added = job.pop('added_timestamp', None)
        claimed = job.pop('claimed_timestamp', None)
        finished = job.pop('finished_timestamp', None)
        failed = job.pop('failed_timestamp', None)
        job.pop('claimed', None)
        job.pop('current_status', None)
        r = requests.post(
            '{}/jobs{}'.format(
                projecturl, '?now={}'.format(added) if added else ''
            ),
            json=job, auth=self.auth)
        if r.status_code != 201:
            return r.status_code
        self._jobs.append((project, job['id']))
        if claimed:
            data = {'Worker': worker}
            r_ = requests.put(
                '{}/jobs/{}/claim?now={}'.format(projecturl, id, claimed),
                auth=self.auth, json=data,
            )
            assert r_.status_code == 200, r_.status_code
        if finished or failed:
            if finished:
                status = {'Status': 'FINISHED'}
            else:
                status = {'Status': 'FAILED'}
            status['ProcessingTime'] = processing_time
            r_ = requests.put(
                '{}/jobs/{}/status?now={}'.format(
                    projecturl, id, finished or failed,
                ),
                auth=self.auth, json=status,
            )
            assert r_.status_code == 200, r_.status_code
        return r.status_code

    def get_project_jobs(self, options=None, project=None, use_auth=True):
        if options:
            url = "{}?{}".format(self.get_jobs_url(project), options)
        else:
            url = "{}".format(self.get_jobs_url(project))

        return requests.get(url, auth=self.auth if use_auth else None)

    def fetch_project_job(self, options=None, project=None, use_auth=True):
        if options:
            url = "{}/fetch?{}".format(self.get_jobs_url(project), options)
        else:
            url = "{}/fetch".format(self.get_jobs_url(project))

        return requests.get(url, auth=self.auth if use_auth else None)

    def fetch_specific_job(self, job, project=None):
        return requests.get(
            "{}/{}/fetch".format(self.get_jobs_url(project), job),
            auth=self.auth,
        )

    def fetch_job(self):
        return requests.get(
            "{}/projects/jobs/fetch".format(self._apiroot),
            auth=self.auth,
        )

    def put_job_status(self, job, status, project=None, auth=None):
        if auth is None:
            auth = self.auth
        url = "{}/{}/status".format(self.get_jobs_url(project), job)
        return requests.put(url, json=status, auth=auth)

    def get_jobs_url(self, project=None):
        if project is None:
            project = self._project
        return "{}/{}/jobs".format(self._apiroot, project)

    @property
    def jobscount(self):
        return len(self._jobs)

    def get_jobs_count(self, project=None, options=None):
        if options:
            return requests.get("{}/count?{}".format(
                self.get_jobs_url(project), options
            ))

        return requests.get("{}/count".format(self.get_jobs_url(project)))

    def get_failed(self, project=None):
        return requests.get(
            "{}/failures".format(self.get_project_url(project)),
        )

    def add_user(self, user, password, auth=None, use_auth=True):
        admin_auth = auth if auth else (self._adminuser, self._adminpw)
        if not use_auth:
            admin_auth = None
        r = requests.post(
            "{}/users".format(self._adminroot),
            json={"username": user, "password": password},
            auth=admin_auth,
        )
        if r.status_code == 201:
            userid = r.json()['userid']
            self._users.append(userid)
        return r

    def add_user_worker(self):
        r = requests.post(
            "{}/users".format(self._adminroot),
            headers={'Content-Type': "application/json"},
            json={"username": self.username, "password": self._password},
            auth=(self._adminuser, self._adminpw),
        )
        assert r.status_code == 201, r.status_code
        userid = r.json()['userid']
        self._users.append(userid)
        self._token = self.get_worker_token()
        return userid

    def get_worker_token(self):
        r = requests.get(self._tokenurl, auth=self.user_auth)
        assert r.status_code == 200, r.status_code
        return r.json()['token']

    def delete_users(self):
        while self._users:
            self.delete_user(self._users[0])

    def delete_user(self, userid):
        r = requests.delete(
            "{}/users/{}".format(self._adminroot, userid),
            auth=self.admin_auth,
        )
        self._users.remove(userid)
        return r

    def cleanup(self):
        self.delete_projects()
        self.delete_users()
