from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import urllib.error

import pytest
import requests

from test.testbase import TEST_URL, ANY, ANY_STRING

JOBS = [
    {'id': '1',
     'type': 'test',
     'source_url': TEST_URL,
     'worker': 'worker1',
     'added_timestamp': '2000-01-01 10:00',
     'claimed_timestamp': '2000-01-01 10:00',
     'finished_timestamp': '2000-01-01 10:00',
     'current_status': 'FINISHED',
     'processing_time': 300
     },
    {'id': '2',
     'type': 'test',
     'source_url': TEST_URL,
     'worker': 'worker2',
     'added_timestamp': '2000-01-01 10:00',
     'claimed_timestamp': '2000-01-01 10:00',
     'failed_timestamp': '2000-01-01 10:00',
     'current_status': 'FAILED',
     'processing_time': 200
     },
    {'id': '3',
     'type': 'test',
     'source_url': TEST_URL,
     'worker': 'worker1',
     'added_timestamp': '2000-01-01 10:00',
     'claimed_timestamp': '2000-01-01 11:00',
     'finished_timestamp': '2000-01-01 11:00',
     'current_status': 'FINISHED',
     'processing_time': 300
     },
    {'id': '4',
     'type': 'test',
     'source_url': TEST_URL,
     'added_timestamp': '2000-01-01 10:00',
     }
]


@pytest.fixture(scope='function')
def apiwithworker(api):
    api.add_user_worker()
    return api


@pytest.fixture(scope='function')
def apiwithproject(apiwithworker):
    apiwithworker.insert_test_jobs()
    return apiwithworker


@pytest.fixture(scope='function')
def apiwithjobs(apiwithworker):
    for job in JOBS:
        status_code = apiwithworker.insert_job(job)
        assert status_code == 201, status_code
    return apiwithworker


@pytest.mark.system
class TestAdmin:

    def test_adding_user(self, api):
        """Test adding and deleting a user"""
        # No user name
        r = api.add_user(user="", password="sqrrl")
        assert r.status_code == 400

        # No credentials
        r = api.add_user(user="myworker", password="sqrrl", use_auth=False)
        assert r.status_code == 401

        # Try to add a valid user
        r = api.add_user(user="myworker", password="sqrrl")
        assert r.status_code == 201
        userid = r.json()['userid']

        # Try to add same user again
        r = api.add_user(user="myworker", password="sqrrl")
        assert r.status_code == 400

        # Try to add new user with none admin user
        r = api.add_user(
            user="other", password="sqrrl", auth=("myworker", "sqrrl"),
        )
        assert r.status_code == 403

        r = api.delete_user(userid)
        assert r.status_code == 204


@pytest.mark.system
class TestAuthentication:

    @pytest.fixture(scope='function')
    def myapi(self, apiwithworker):
        status_code = apiwithworker.insert_job(
            {'id': '42', 'type': 'test_type', 'source_url': TEST_URL},
        )
        assert status_code == 201, status_code
        return apiwithworker

    def test_user_password_authentication(self, myapi):
        """Test authenticating by user and password"""

        r = myapi.put_job_status(42, {"Status": "42"}, auth=myapi.user_auth)
        assert r.status_code == 200

    def test_baduser_password_auth(self, myapi):

        r = myapi.put_job_status(42, {"Status": "42"}, auth=("worker1", "sqd"))
        assert r.status_code == 401, r.json()

    def test_token_authentication(self, myapi):
        """Test authenticating by token"""
        r = myapi.put_job_status(42, {"Status": "42"}, auth=myapi.token_auth)
        assert r.status_code == 200


@pytest.mark.system
class TestFetchJob:

    def test_fetch_job(self, apiwithproject):
        """Test requesting a free job."""
        # Should need auth
        r = apiwithproject.fetch_project_job(use_auth=False)
        assert r.status_code == 401

        r = apiwithproject.fetch_project_job()
        r.raise_for_status()
        jobid = r.json()['Job']['JobID']

        joburl = "{}/{}".format(apiwithproject.get_jobs_url(), jobid)

        assert r.json()["Job"] == {
            u'JobID': u'42',
            u'Environment': {},
            u'URLS': {
                u'URL-image': None,
                u'URL-source': TEST_URL,
                u'URL-target': TEST_URL,
                u'URL-claim': u'{}/claim'.format(joburl),
                u'URL-output': u'{}/output'.format(joburl),
                u'URL-status': u'{}/status'.format(joburl),
            },
        }

        project_data = {
            'environment': {'v': 1},
            'processing_image_url': TEST_URL + '/image'
        }
        r = apiwithproject.put_project(json=project_data)
        assert r.status_code == 204

        r = apiwithproject.fetch_project_job()
        r.raise_for_status()
        jobid = r.json()['Job']['JobID']

        assert r.json()["Job"] == {
            u'JobID': u'42',
            u'Environment': {'v': 1},
            u'URLS': {
                u'URL-image': TEST_URL + '/image',
                u'URL-source': TEST_URL,
                u'URL-target': TEST_URL,
                u'URL-claim': u'{}/claim'.format(joburl),
                u'URL-output': u'{}/output'.format(joburl),
                u'URL-status': u'{}/status'.format(joburl),
            }
        }


@pytest.mark.system
class TestListJobs:

    @pytest.fixture(scope='function')
    def myapi(self, apiwithworker):
        jobs = [
            {
                'id': '1', 'type': 'test_type',
                'source_url': TEST_URL + '/source',
                'target_url': TEST_URL + '/target',
                'view_result_url': TEST_URL + '/view_result',
            },
            {
                'id': '2', 'type': 'test_type',
                'source_url': TEST_URL,
                'target_url': TEST_URL,
                'claimed_timestamp': '2016-01-01 10:00',
                'current_status': 'CLAIMED',
                'worker': 'worker1',
            },
            {
                'id': '3', 'type': 'test_type',
                'source_url': TEST_URL,
                'target_url': TEST_URL,
                'claimed_timestamp': '2016-01-01 11:00',
                'finished_timestamp': '2016-01-01 11:10',
                'current_status': 'FINISHED',
                'worker': 'worker2',
            },
            {
                'id': '4', 'type': 'other_type',
                'source_url': TEST_URL,
                'target_url': TEST_URL,
                'claimed_timestamp': '2016-01-01 12:00',
                'failed_timestamp': '2016-01-01 12:10',
                'current_status': 'FAILED',
                'worker': 'worker2',
            },
        ]
        for job in jobs:
            apiwithworker.insert_job(job)
        return apiwithworker

    def test_bad_requests(self, myapi):
        """Test requests with bad parameters"""

        r = myapi.get_project_jobs(options="start=a")
        assert r.status_code == 400, r.json()
        # When start/end is used, status must also be provided
        r = myapi.get_project_jobs(options="start=2016-01-01")
        assert r.status_code == 400
        r = myapi.get_project_jobs(options="status=a")
        assert r.status_code == 400

    def test_bad_job_insert(self, myapi):
        """Test requests with bad job fields"""
        bad_jobs = [
            # Missing input_url
            {'id': '1'},
            # Unsupported field
            {'id': '1', 'input_url': TEST_URL, 'unknown': 's'}
        ]
        for job in bad_jobs:
            assert myapi.insert_job(job) == 400

    def test_list_all(self, myapi):
        """Test requesting list of jobs without parameters."""
        r = myapi.get_project_jobs()
        r.raise_for_status()
        assert len(r.json()["Jobs"]) == myapi.jobscount

    def test_job_contents(self, myapi):
        """Test that listed jobs have the correct contents"""
        r = myapi.get_project_jobs(options="status=available")
        r.raise_for_status()
        assert len(r.json()["Jobs"]) == 1
        job = r.json()["Jobs"][0]
        assert job == {
            'Added': ANY,
            'Id': '1',
            'Type': 'test_type',
            'Status': 'AVAILABLE',
            'Claimed': None,
            'IsClaimed': False,
            'Failed': None,
            'Finished': None,
            'ProcessingTime': None,
            'Worker': None,
            'URLS': {
                'URL-Input': TEST_URL + '/source',
                'URL-Output': '{}/1/output'.format(myapi.get_jobs_url()),
                'URL-Result': TEST_URL + '/view_result'
            },
        }

    def test_list_matching(self, myapi):
        """Test listing jobs that match provided parameters"""
        tests = [
            ('status=finished', 1),
            ('worker=worker2', 2),
            ('type=other_type', 1),
            ('type=other_type&worker=worker1', 0),
        ]
        for param, expected in tests:
            r = myapi.get_project_jobs(options=param)
            r.raise_for_status()
            assert len(r.json()["Jobs"]) == expected

    def test_list_period(self, myapi):
        """Test listing jobs between start and end time"""
        tests = [
            ('2016-01-01', '2016-01-02', 'claimed', 3),
            ('2016-01-01 10:00', '2016-01-01 11:00', 'claimed', 1),
            ('2016-01-01 11:00', '2016-01-01 12:00', 'failed', 0),
            ('2016-01-01 12:00', '2016-01-01 13:00', 'failed', 1)
        ]
        for start, end, status, expected in tests:
            param = [('status', status), ('start', start), ('end', end)]
            r = myapi.get_project_jobs(options=urllib.parse.urlencode(param))
            r.raise_for_status()
            assert len(r.json()["Jobs"]) == expected

    def test_analyze_failed_jobs(self, myapi):
        # Locate a/the failed job
        r = myapi.get_failed()
        r.raise_for_status()
        data = r.json()
        jobid, _ = data['Jobs'].popitem()

        # Figure out how to post output to it
        r = myapi.get_project_jobs()
        r.raise_for_status()
        job = [j for j in r.json()['Jobs'] if j['Id'] == jobid].pop()

        # Post output
        r = requests.put(
            job["URLS"]["URL-Output"],
            json={"Output": "This is a line\nAnd next...\nAnd next..."},
            auth=myapi.auth,
        )
        r.raise_for_status()

        # Get failed jobs again now with output
        r = myapi.get_failed()
        r.raise_for_status()
        data = r.json()
        assert isinstance(data['Lines'], list)
        assert data['Lines'] == [
            {
                'CommonLines': [
                    {'Line': 'This is a line', 'Score': 0.0},
                    {'Line': 'And next...', 'Score': 0.0}
                ],
                'Jobs': ['4'],
                'Line': 'This is a line',
                'Score': 0.0,
            }
        ]

    def test_analyze_failed_jobs_old(self, myapi):
        r = myapi.get_failed(project="QSMRVDS")
        r.raise_for_status()
        data = r.json()
        assert isinstance(data['Lines'], list)
        assert data['Lines']


def get_project(api, project='project'):
    r = api.get_projects()
    r.raise_for_status()
    for p in r.json()['Projects']:
        if p['Id'] == project:
            return p
    raise ValueError("Project not found")


@pytest.mark.system
class TestMultipleProjects:

    @pytest.fixture
    def myapi(self, apiwithworker):
        r = apiwithworker.get_projects()
        r.raise_for_status()
        apiwithworker.nr_orig_projects = len(r.json()['Projects'])

        r = apiwithworker.get_projects(options="only_active=1")
        r.raise_for_status()
        apiwithworker.nr_orig_active_projects = len(r.json()['Projects'])

        jobs = [
            {
                'id': '42', 'type': 'test_type', 'source_url': TEST_URL,
                'target_url': TEST_URL
            },
            {
                'id': '44', 'type': 'test_type', 'source_url': TEST_URL,
                'target_url': TEST_URL,
            },
        ]
        for job in jobs:
            apiwithworker.insert_job(job)

        apiwithworker.insert_job(jobs[0], project='other')
        r = apiwithworker.put_project("nojobs")
        assert r.status_code == 201
        return apiwithworker

    def test_multiple_projects(self, myapi):
        """Test that multiple projects work and are separated"""
        r = myapi.get_project_jobs()
        r.raise_for_status()
        assert len(r.json()["Jobs"]) == 2

        r = myapi.get_project_jobs(project='other')
        r.raise_for_status()
        assert len(r.json()["Jobs"]) == 1

        r = myapi.get_project_jobs(project='nojobs')
        r.raise_for_status()
        assert len(r.json()["Jobs"]) == 0

        r = myapi.get_projects()
        r.raise_for_status()
        projects = r.json()['Projects']
        assert len(projects) - myapi.nr_orig_projects == 3

        r = myapi.get_projects(options="only_active=1")
        r.raise_for_status()
        projects = r.json()['Projects']
        assert len(projects) - myapi.nr_orig_active_projects == 2


@pytest.mark.system
class TestProjectsPrio:

    def test_projects_prio_score(self, apiwithjobs):
        """Test calculation of prio score"""
        # Prio should be 1 when no deadline
        api = apiwithjobs

        r = api.put_project(json={'deadline': None})
        assert r.status_code == 204
        assert get_project(api)['PrioScore'] == 1

        # Deadline passed
        r = api.put_project(json={'deadline':  '2011-01-01 10:00'})
        assert r.status_code == 204
        prio_deadline_passed = get_project(api)['PrioScore']
        assert prio_deadline_passed == 800 / 3.

        # Future deadline
        r = api.put_project(
            json={
                'deadline':
                    (datetime.utcnow() + timedelta(seconds=100)).isoformat()
            },
        )
        assert r.status_code == 204
        assert get_project(api)['PrioScore'] == pytest.approx(
            prio_deadline_passed / 100., abs=0.05
        )

        # Prio should be zero when no jobs are available
        r = api.put_project(
            'myproject',
            json={'name': 'My Project', 'deadline': '2011-01-01 10:00'},
        )
        assert r.status_code == 201
        assert get_project(api, 'myproject')['PrioScore'] == 0

    def test_fetch_job_prio(self, apiwithjobs):
        """Test fetch of job from any project weighted by prio score"""
        api = apiwithjobs
        # Project with one available job, but no processed jobs and deadline
        # passed
        assert api.insert_job(
            {'id': '1', 'source_url': TEST_URL}, project='myproject'
        ) == 201
        r = api.put_project(
            project='myproject',
            json={'deadline': '2011-01-01 10:00'},
        )
        assert r.status_code == 204

        r = api.put_project(json={'deadline': '2011-01-01 10:00'})
        assert r.status_code == 204

        # Prio scores
        assert get_project(api)['PrioScore'] == 800 / 3.
        assert (
            get_project(api, 'myproject')['PrioScore'] == 3600
        )

        project_count = {'project': 0, 'myproject': 0}

        for _ in range(100):
            r = api.fetch_job()
            r.raise_for_status()
            project_count[r.json()['Project']] += 1

        # p_project = (800/3)/(800/3 + 3600) = 0.069
        # Probability to get zero jobs from project:
        # binom.pmf(0, 100, p_project) = 0.0008
        assert project_count['project'] > 0
        assert project_count['myproject'] > project_count['project']


@pytest.mark.system
class TestUpdateProject:

    def test_update_project(self, apiwithworker):
        """Test create and update project"""
        r = apiwithworker.put_project(
            project='myproject', json={'name': 'My Project'},
        )
        assert r.status_code == 201

        p = get_project(apiwithworker, 'myproject')
        assert p == {
            u'Id': u'myproject',
            u'Name': u'My Project',
            u'Environment': {},
            u'CreatedAt': ANY_STRING,
            u'CreatedBy': apiwithworker.username,
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
                u'URL-Status': apiwithworker.get_project_url('myproject'),
                u'URL-Processing-image': None
            }
        }

        r = apiwithworker.put_project(
            project='myproject',
            json={
                'name': 'Your Project',
                'deadline': '2001-01-01 10:00',
                'processing_image_url': TEST_URL,
                'environment': {'var': 10},
            },
        )
        assert r.status_code == 204

        p = get_project(apiwithworker, 'myproject')
        assert p == {
            u'Id': u'myproject',
            u'Name': u'Your Project',
            u'Environment': {'var': 10},
            u'CreatedAt': ANY_STRING,
            u'CreatedBy': apiwithworker.username,
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
                u'URL-Status': apiwithworker.get_project_url('myproject'),
                u'URL-Processing-image': TEST_URL
            }
        }

        # Not allowed to update some data
        r = apiwithworker.put_project(
            project='myproject', json={'created_by_user': 'cannot_do_this'},
        )
        assert r.status_code == 400


@pytest.mark.system
class TestJobViews:

    def test_update_job_status(self, apiwithproject):
        """Test updating job status."""
        api = apiwithproject
        r = api.fetch_project_job()
        r.raise_for_status()
        job = r.json()

        r = requests.put(
            job["Job"]["URLS"]["URL-status"],
            json={"BadStatus": "Testing status update."},
            auth=api.auth,
        )
        assert r.status_code == 400

        r = requests.put(
            job["Job"]["URLS"]["URL-status"],
            json={"Status": "Testing status update."},
            auth=api.auth,
        )
        r.raise_for_status()

        # Fetch current status
        r = requests.get(job["Job"]["URLS"]["URL-status"])
        r.raise_for_status()
        assert r.json()['Status'] == "Testing status update."

    def test_get_nonexisting_job_status(self, apiwithproject):
        # Test fetch for none-existing job
        r = apiwithproject.fetch_specific_job(job='none')
        assert r.status_code == 404

    def _get_nr_claimed(self, api):
        r = api.get_project()
        r.raise_for_status()
        return r.json()['NrJobsClaimed']

    def test_claim_job(self, apiwithproject):
        """Test claiming a job."""
        api = apiwithproject
        r = api.fetch_project_job()
        r.raise_for_status()
        job = r.json()

        assert self._get_nr_claimed(api) == 0

        r = requests.put(
            job["Job"]["URLS"]["URL-claim"],
            json={'BadWorker': api.username},
            auth=api.auth,
        )
        assert r.status_code == 400

        r = requests.put(
            job["Job"]["URLS"]["URL-claim"], json={'Worker': api.username},
            auth=api.auth,
        )
        r.raise_for_status()
        assert self._get_nr_claimed(api) == 1

        # Should not be able to claim same job again
        r = requests.put(
            job["Job"]["URLS"]["URL-claim"],
            json={'Worker': api.username},
            auth=api.auth,
        )
        assert r.status_code == 409
        assert self._get_nr_claimed(api) == 1

        # Should be able to claim after release of job
        r = requests.delete(
            job["Job"]["URLS"]["URL-claim"],
            auth=api.auth,
        )
        r.raise_for_status()

        # Get job claim data
        r = requests.get(job["Job"]["URLS"]["URL-claim"])
        r.raise_for_status()
        assert r.json()['Claimed'] is False

        assert self._get_nr_claimed(api) == 0
        r = requests.put(
            job["Job"]["URLS"]["URL-claim"], json={'Worker': api.username},
            auth=api.auth,
        )
        r.raise_for_status()
        assert self._get_nr_claimed(api) == 1

        # Get job claim data
        r = requests.get(job["Job"]["URLS"]["URL-claim"])
        r.raise_for_status()
        assert r.json()['Claimed'] is True

        # Test fetch for none existing job
        r = requests.get("{}/none/claim".format(api.get_jobs_url()))
        assert r.status_code == 404

    def test_update_job_output(self, apiwithproject):
        """Test updating job output"""
        api = apiwithproject
        r = api.fetch_project_job()
        r.raise_for_status()
        job = r.json()

        r = requests.put(
            job["Job"]["URLS"]["URL-output"],
            json={"BadOutput": "Testing output update."},
            auth=api.auth,
        )
        assert r.status_code == 400

        r = requests.put(
            job["Job"]["URLS"]["URL-output"],
            json={"Output": "Testing output update."},
            auth=api.auth,
        )
        r.raise_for_status()

        # Get current output
        r = requests.get(job["Job"]["URLS"]["URL-output"])
        r.raise_for_status()
        assert r.json()['Output'] == "Testing output update."

        # Test fetch for none existing job
        r = requests.get("{}/none/output".format(api.get_jobs_url()))
        assert r.status_code == 404


@pytest.mark.system
class TestCountJobs:

    def test_daily_count(self, apiwithjobs):
        """Test daily count of jobs"""
        r = apiwithjobs.get_jobs_count()
        r.raise_for_status()

        projecturl = apiwithjobs.get_project_url()
        assert r.json() == {
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
                        u'{}/workers?'.format(projecturl)
                        + u'start=2000-01-01T00%3A00%3A00&'
                        + u'end=2000-01-02T00%3A00%3A00'
                    ),
                    u'URL-JobsClaimed': (
                        u'{}/jobs?'.format(projecturl)
                        + u'status=CLAIMED&start=2000-01-01T00%3A00%3A00&'
                        + u'end=2000-01-02T00%3A00%3A00'
                    ),
                    u'URL-JobsFailed': (
                        u'{}/jobs?'.format(projecturl)
                        + u'status=FAILED&start=2000-01-01T00%3A00%3A00&'
                        + u'end=2000-01-02T00%3A00%3A00'
                    ),
                    u'URL-JobsFinished': (
                        u'{}/jobs?'.format(projecturl)
                        + u'status=FINISHED&start=2000-01-01T00%3A00%3A00&'
                        + u'end=2000-01-02T00%3A00%3A00'
                    ),
                    u'URL-Zoom': (
                        u'{}/jobs/'.format(projecturl)
                        + u'count?period=HOURLY&start=2000-01-01T00%3A00%3A00&'
                        + u'end=2000-01-02T00%3A00%3A00'
                    )
                }
            }],
        }

    def test_hourly_count(self, apiwithjobs):
        """Test hourly count of jobs"""
        r = apiwithjobs.get_jobs_count(options="period=hourly")
        r.raise_for_status()

        projecturl = apiwithjobs.get_project_url()
        assert r.json() == {
            u'Project': 'project',
            u'Version': 'v4',
            u'PeriodType': 'Hourly',
            u'Start': None,
            u'End': None,
            u'Counts': [
                {
                    u'ActiveWorkers': 2,
                    u'JobsClaimed': 2,
                    u'JobsFailed': 1,
                    u'JobsFinished': 1,
                    u'Period': u'2000-01-01 10:00',
                    u'URLS': {
                        u'URL-ActiveWorkers': (
                            u'{}/workers?'.format(projecturl)
                            + u'start=2000-01-01T10%3A00%3A00&'
                            + u'end=2000-01-01T11%3A00%3A00'
                        ),
                        u'URL-JobsClaimed': (
                            u'{}/jobs?'.format(projecturl)
                            + u'status=CLAIMED&start=2000-01-01T10%3A00%3A00&'
                            + u'end=2000-01-01T11%3A00%3A00'
                        ),
                        u'URL-JobsFailed': (
                            u'{}/jobs?'.format(projecturl)
                            + u'status=FAILED&start=2000-01-01T10%3A00%3A00&'
                            + u'end=2000-01-01T11%3A00%3A00'
                        ),
                        u'URL-JobsFinished': (
                            u'{}/jobs?'.format(projecturl)
                            + u'status=FINISHED&start=2000-01-01T10%3A00%3A00&'
                            + u'end=2000-01-01T11%3A00%3A00'
                        ),
                    },
                },
                {
                    u'ActiveWorkers': 1,
                    u'JobsClaimed': 1,
                    u'JobsFailed': 0,
                    u'JobsFinished': 1,
                    u'Period': u'2000-01-01 11:00',
                    u'URLS': {
                        u'URL-ActiveWorkers': (
                            u'{}/workers?'.format(projecturl)
                            + u'start=2000-01-01T11%3A00%3A00&'
                            + u'end=2000-01-01T12%3A00%3A00'
                        ),
                        u'URL-JobsClaimed': (
                            u'{}/jobs?'.format(projecturl)
                            + u'status=CLAIMED&start=2000-01-01T11%3A00%3A00&'
                            + u'end=2000-01-01T12%3A00%3A00'
                        ),
                        u'URL-JobsFinished': (
                            u'{}/jobs?'.format(projecturl)
                            + u'status=FINISHED&start=2000-01-01T11%3A00%3A00&'
                            + u'end=2000-01-01T12%3A00%3A00'
                        ),
                    },
                },
            ],
        }

    def test_time_range_count(self, apiwithjobs):
        """Test count between start and end time"""
        param = [
            ('period', 'hourly'),
            ('start', '2000-01-01 10:00'),
            ('end', '2000-01-01 11:00'),
        ]
        r = apiwithjobs.get_jobs_count(options=urllib.parse.urlencode(param))
        r.raise_for_status()

        projecturl = apiwithjobs.get_project_url()
        assert r.json() == {
            u'Project': 'project',
            u'Version': 'v4',
            u'PeriodType': 'Hourly',
            u'Start': '2000-01-01T10:00:00',
            u'End': '2000-01-01T11:00:00',
            u'Counts': [
                {
                    u'ActiveWorkers': 2,
                    u'JobsClaimed': 2,
                    u'JobsFailed': 1,
                    u'JobsFinished': 1,
                    u'Period': u'2000-01-01 10:00',
                    u'URLS': {
                        u'URL-ActiveWorkers': (
                            u'{}/workers?'.format(projecturl)
                            + u'start=2000-01-01T10%3A00%3A00&'
                            + u'end=2000-01-01T11%3A00%3A00'
                        ),
                        u'URL-JobsClaimed': (
                            u'{}/jobs?'.format(projecturl)
                            + u'status=CLAIMED&start=2000-01-01T10%3A00%3A00&'
                            + u'end=2000-01-01T11%3A00%3A00'
                        ),
                        u'URL-JobsFailed': (
                            u'{}/jobs?'.format(projecturl)
                            + u'status=FAILED&start=2000-01-01T10%3A00%3A00&'
                            + u'end=2000-01-01T11%3A00%3A00'
                        ),
                        u'URL-JobsFinished': (
                            u'{}/jobs?'.format(projecturl)
                            + u'status=FINISHED&start=2000-01-01T10%3A00%3A00&'
                            + u'end=2000-01-01T11%3A00%3A00'
                        ),
                    },
                },
            ],
        }


@pytest.mark.system
class TestProjectViews:

    def test_project_status(self, apiwithjobs):
        """Test get project status"""
        r = apiwithjobs.get_project(options="now=2000-01-01T11%3A00%3A00")
        r.raise_for_status()

        projecturl = apiwithjobs.get_project_url()
        assert r.json() == {
            u'Version': u'v4',
            u'Project': u'project',
            u'Name': u'project',
            u'CreatedAt': ANY_STRING,
            u'CreatedBy': u'worker1',
            u'Id': u'project',
            u'ETA': u'0:30:00',
            u'Environment': {},
            u'LastJobAddedAt': ANY,
            u'LastJobClaimedAt': ANY,
            u'NrJobsAdded': 4,
            u'NrJobsClaimed': 3,
            u'NrJobsFailed': 1,
            u'NrJobsFinished': 2,
            u'Deadline': None,
            u'PrioScore': None,
            u'TotalProcessingTime': 800.0,
            u'JobStates': {u'Available': 1, u'Failed': 1, u'Finished': 2},
            u'URLS': {
                u'URL-DailyCount':
                    u'{}/jobs/count?period=daily'.format(projecturl),
                u'URL-Jobs': u'{}/jobs'.format(projecturl),
                u'URL-Workers': u'{}/workers'.format(projecturl),
                u'URL-Status': u'{}'.format(projecturl),
                u'URL-Processing-image': None
            },
        }
