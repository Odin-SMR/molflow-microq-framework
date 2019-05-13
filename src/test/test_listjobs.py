# pylint: disable=no-self-use
import pytest
import requests

from uservice.views.listjobs import (
    validate_json_job, validate_json_job_list, ValidationError)
from test.testbase import ADMINUSER, ADMINPW


class TestJsonJobValidation:

    @pytest.fixture
    def job(self):
        return {
            'id': 'abcd',
            'source_url': 'http://example.com/foobar',
            'view_result_url': 'http://example.com/foobaz',
            'target_url': 'http://example.com/foobiz',
        }

    def test_valid_job(self, job):
        validate_json_job(job)

    def test_id_is_not_string(self, job):
        job['id'] = 42
        with pytest.raises(ValidationError) as excinfo:
            validate_json_job(job)
        expected_error = "Expected string in field 'id'"
        assert str(excinfo.value) == expected_error

    def test_missing_field_source_url(self, job):
        del job['source_url']
        with pytest.raises(ValidationError) as excinfo:
            validate_json_job(job)
        expected_error = "Missing required fields: source_url"
        assert str(excinfo.value) == expected_error

    def test_missing_field_id(self, job):
        del job['id']
        with pytest.raises(ValidationError) as excinfo:
            validate_json_job(job)
        expected_error = "Missing required fields: id"
        assert str(excinfo.value) == expected_error

    def test_extra_field(self, job):
        job['some_extra_field'] = 'blabliblu'
        with pytest.raises(ValidationError) as excinfo:
            validate_json_job(job)
        expected_error = (
            "These fields do not exist or are for internal use: "
            "some_extra_field"
        )
        assert str(excinfo.value) == expected_error

    @pytest.fixture
    def job_list(self):
        return [
            {
                'id': 'abc',
                'source_url': 'http://example.com/abc',
            },
            {
                'id': 'xyz',
                'source_url': 'http://example.com/xyz',
            },
        ]

    def test_validate_valid_json_job_list(self, job_list):
        validate_json_job_list(job_list)

    def test_validate_invalid_json_job_list(self, job_list):
        del job_list[0]['id']
        job_list[1]['foo'] = 'bar'
        with pytest.raises(ValidationError) as excinfo:
            validate_json_job_list(job_list)
        expected_error = (
            "Job#0: Missing required fields: id\n"
            "Job#1: These fields do not exist or are for internal use: foo"
        )
        assert str(excinfo.value) == expected_error


@pytest.mark.system
class TestAddJobs:
    @pytest.fixture
    def session(self):
        requests_session = requests.Session()
        requests_session.auth = (ADMINUSER, ADMINPW)
        return requests_session

    @pytest.fixture
    def project(self, session, microq_service):
        name = 'testproject'
        url = "{}/rest_api/v4/{}".format(microq_service, name)
        session.put(url).raise_for_status()
        yield url
        if session.head(url).status_code == 200:
            session.delete(url).raise_for_status()

    def test_add_a_single_valid_job(self, session, project):
        job = {'id': '42', 'source_url': 'http://example.com/job'}
        session.post(project + '/jobs', json=job).raise_for_status()
        assert len(session.get(project + '/jobs').json()['Jobs']) == 1
        assert session.get(project).json()['NrJobsAdded'] == 1

    def test_add_a_single_valid_job_with_now(self, session, project):
        job = {'id': '42', 'source_url': 'http://example.com/job'}
        params = {'now': '2000-01-01 10:00'}
        response = session.post(project + '/jobs', params=params, json=job)
        response.raise_for_status()
        assert len(session.get(project + '/jobs').json()['Jobs']) == 1

    def test_add_a_single_invalid_job(self, session, project):
        job = {}
        response = session.post(project + '/jobs', json=job)
        assert not response.ok
        responsejson = response.json()
        assert 'error' in responsejson
        err = responsejson['error']
        assert err.startswith("Missing required fields:")
        _, missing = err.split(':', 1)
        assert {v.strip() for v in missing.split(',')} == {'id', 'source_url'}
        assert not session.get(project + '/jobs').json()['Jobs']

    def test_add_the_same_job_twice(self, session, project):
        job = {'id': '42', 'source_url': 'http://example.com/job'}
        session.post(project + '/jobs', json=job).raise_for_status()
        response = session.post(project + '/jobs', json=job)
        assert response.status_code == 201
        assert len(session.get(project + '/jobs').json()['Jobs']) == 1
        assert session.get(project).json()['NrJobsAdded'] == 1

    def test_add_a_list_of_jobs(self, session, project):
        jobs = [
            {'id': '41', 'source_url': 'http://example.com/job'},
            {'id': '42', 'source_url': 'http://example.com/job'},
        ]
        session.post(project + '/jobs', json=jobs).raise_for_status()
        assert len(session.get(project + '/jobs').json()['Jobs']) == 2
        assert session.get(project).json()['NrJobsAdded'] == 2

    def test_add_a_list_of_jobs_with_invalid_ones(self, session, project):
        jobs = [
            {'id': '41', 'source_url': 'http://example.com/job'},
            {'id': '42'},
            {'source_url': 'http://example.com/job3'},
        ]
        response = session.post(project + '/jobs', json=jobs)
        assert not response.ok
        expected_error = (
            'Job#1: Missing required fields: source_url\n'
            'Job#2: Missing required fields: id'
        )
        assert response.json() == {'error': expected_error}
        assert not session.get(project + '/jobs').json()['Jobs']

    def test_add_a_list_of_jobs_with_duplicated_id(self, session, project):
        jobs = [
            {'id': '41', 'source_url': 'http://example.com/job1'},
            {'id': '41', 'source_url': 'http://example.com/job2'},
            {'id': '42', 'source_url': 'http://example.com/job3'},
        ]
        response = session.post(project + '/jobs', json=jobs)
        assert not response.ok
        expected_error = 'Job#1: A job with id 41 already exists.'
        assert response.json() == {'error': expected_error}
        assert not session.get(project + '/jobs').json()['Jobs']

    def test_add_a_list_of_jobs_with_duplicates(self, session, project):
        jobs = [
            {'id': '41', 'source_url': 'http://example.com/job1'},
            {'id': '41', 'source_url': 'http://example.com/job1'},
            {'id': '42', 'source_url': 'http://example.com/job3'},
        ]
        response = session.post(project + '/jobs', json=jobs)
        assert response.status_code == 201
        assert len(session.get(project + '/jobs').json()['Jobs']) == 2

    def test_add_a_list_of_jobs_with_one_existing_id(self, session, project):
        job = {'id': '42', 'source_url': 'http://example.com/job'}
        session.post(project + '/jobs', json=job).raise_for_status()
        jobs = [
            {'id': '41', 'source_url': 'http://example.com/job1'},
            {'id': '42', 'source_url': 'http://example.com/job2'},
        ]
        response = session.post(project + '/jobs', json=jobs)
        assert not response.ok
        expected_error = 'Job#1: A job with id 42 already exists.'
        assert response.json() == {'error': expected_error}
        assert len(session.get(project + '/jobs').json()['Jobs']) == 1

    def test_add_a_list_of_jobs_with_one_existing_job(self, session, project):
        job = {'id': '42', 'source_url': 'http://example.com/job'}
        session.post(project + '/jobs', json=job).raise_for_status()
        jobs = [
            {'id': '41', 'source_url': 'http://example.com/job1'},
            {'id': '42', 'source_url': 'http://example.com/job'},
        ]
        response = session.post(project + '/jobs', json=jobs)
        assert response.status_code == 201
        assert len(session.get(project + '/jobs').json()['Jobs']) == 2
