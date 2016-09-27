""" Basic views for REST api
"""
from os import environ

from dateutil.parser import parse as parse_datetime

from flask import jsonify, abort as flask_abort, make_response, request
from flask.views import MethodView

from utils.validate import validate_project_name
from utils.logs import get_logger
from utils.defs import JOB_STATES

from uservice.core.users import auth
from uservice.database.basedb import get_db
from uservice.database.sqldb import SqlJobDatabase


def abort(status_code, message=None):
    """
    Return response with a certain status code and the json data:
    {error: message}
    """
    if not message:
        flask_abort(status_code)
    else:
        return make_response(jsonify(error=message), status_code)


class BasicView(MethodView):
    """Base class for views"""
    def __init__(self):
        self.log = get_logger('UService')
        super(BasicView, self).__init__()

    def get(self, version):
        """GET"""
        self._check_version(version)
        return self._get_view(version)

    @auth.login_required
    def put(self, version):
        """PUT"""
        self._check_version(version)
        return self._put_view(version)

    @auth.login_required
    def post(self, version):
        """POST"""
        self._check_version(version)
        return self._post_view(version)

    @auth.login_required
    def delete(self, version):
        """DELETE"""
        self._check_version(version)
        return self._delete_view(version)

    def _get_view(self, *args):
        """
        Dummy method which should be over loaded by derived classes
        """
        abort(405)

    def _put_view(self, *args):
        """
        Dummy method which should be over loaded by derived classes
        """
        abort(405)

    def _post_view(self, *args):
        """
        Dummy method which should be over loaded by derived classes
        """
        abort(405)

    def _delete_view(self, *args):
        """
        Dummy method which should be over loaded by derived classes
        """
        abort(405)

    def _check_version(self, version):
        """Check that a valid version of the API is requested."""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)

    @auth.error_handler
    def unauthorized():
        return make_response(jsonify({'error': 'Unauthorized access'}), 401)


class BasicProjectView(BasicView):
    """Base class for project views"""

    def _get_database(self, project):
        return get_db(
            project, SqlJobDatabase, dburl=environ['USERVICE_DATABASE_URI'])

    def get(self, version, project):
        """GET"""
        self._check_version(version)
        self._check_project(project)
        return self._get_view(version, project)

    @auth.login_required
    def put(self, version, project):
        """PUT"""
        self._check_version(version)
        self._check_project(project)
        return self._put_view(version, project)

    @auth.login_required
    def post(self, version, project):
        """POST"""
        self._check_version(version)
        self._check_project(project)
        return self._post_view(version, project)

    @auth.login_required
    def delete(self, version, project):
        """DELETE"""
        self._check_version(version)
        self._check_project(project)
        return self._delete_view(version, project)

    def _check_project(self, project):
        if not validate_project_name(project):
            abort(404)


class ListProjects(BasicView):
    """View for listing projects"""
    def _get_view(self, version):
        """
        Should return a JSON object with a list of projects.
        """
        return jsonify(Version=version)


def make_job_url(endpoint, project, job_id):
    return "{0}rest_api/v4/{1}/jobs/{2}/{3}".format(
        request.url_root, project, job_id, endpoint)


def fix_timestamp(ts):
    if not ts:
        return
    # TODO: timezone
    return ts.isoformat()


def make_pretty_job(job, project):
    """Transform job to json serializable dict with good looking keys"""
    job['URLS'] = {
        'URL-Input': job.pop('source_url'),
        'URL-Output': make_job_url('output', project, job['id'])}
    job['Id'] = job.pop('id')
    job['Type'] = job.pop('type')
    job['Status'] = job.pop('current_status')
    job['Added'] = fix_timestamp(job.pop('added_timestamp'))
    job['Claimed'] = fix_timestamp(job.pop('claimed_timestamp'))
    job['Failed'] = fix_timestamp(job.pop('failed_timestamp'))
    job['finished'] = fix_timestamp(job.pop('finished_timestamp'))
    job['Worker'] = job.pop('worker')
    return job


class ListJobs(BasicProjectView):
    """View for listing jobs as JSON object"""
    _translate_backend = {'B': 'AC1', 'C': 'AC2', 'AC1': 'AC1', 'AC2': 'AC2'}

    def _get_view(self, version, project):
        """
        Return a JSON object with a list of jobs with URIs for
        getting data etc.
        """
        job_type = request.args.get('type')
        status = request.args.get('status')
        worker = request.args.get('worker')
        start = request.args.get('start')
        end = request.args.get('end')

        match = {}
        if job_type:
            match['type'] = job_type
        if worker:
            match['worker'] = worker
        if status:
            status = status.upper()
            if status not in JOB_STATES.all_values:
                return abort(400, 'Unsupported status: %r' % status)
            match['current_status'] = status
        if start:
            try:
                start = parse_datetime(start)
            except ValueError:
                return abort(400, 'Bad time format: %r' % start)
        if end:
            try:
                end = parse_datetime(end)
            except ValueError:
                return abort(400, 'Bad time format: %r' % end)

        db = self._get_database(project)
        if start or end:
            if not status:
                return abort(400, ('Param @start and @end can only be used '
                                   'together with @status'))
            match.pop('current_status')
            if status == JOB_STATES.claimed:
                fun = db.get_claimed_jobs
            elif status == JOB_STATES.finished:
                fun = db.get_finished_jobs
            elif status == JOB_STATES.failed:
                fun = db.get_failed_jobs
            else:
                return abort(400, 'Unsupported status: %r' % status)
        else:
            fun = db.get_jobs
        jobs = list(fun(match=match, start_time=start, end_time=end,
                        fields=db.PUBLIC_LISTING_FIELDS))

        for job in jobs:
            make_pretty_job(job, project)

        return jsonify(Version=version, Project=project, Jobs=jobs,
                       Status=status, Start=start, End=end, Worker=worker)

    def _post_view(self, version, project):
        """
        Used to add jobs to the database.
        """
        job = request.json
        job_id = job['id']
        db = self._get_database(project)
        if db.job_exists(job_id):
            return abort(409, 'Job already exists')
        db.insert_job(job_id, job)
        return jsonify(Version=version, Project=project, ID=job_id), 201


class FetchNextJob(ListJobs):
    """View for fetching data needed by the worker for the next job
    in the queue.
    """
    def __init__(self):
        super(FetchNextJob, self).__init__()

    @auth.login_required
    def get(self, version, project):
        """GET"""
        self._check_version(version)
        self._check_project(project)
        return self._get_view(version, project)

    # TODO: Use url parameter 'type'
    def _get_view(self, version, project):
        """
        Should return JSON object with URI for getting/delivering data etc.

        Separate fetching and claiming, so that the returned object
        contains URIs for claming job, as well as for getting/delivering
        data.

        why?
        * Because it gives a neater interface, and because the claiming
          URI can be put in the object and included in the listing.
        * Easier to debug/get status if fetching can be done w/o auth.
        """
        db = self._get_database(project)
        try:
            job = next(db.get_jobs(match={'claimed': False},
                                   fields=['id', 'source_url', 'target_url']))
        except StopIteration:
            return abort(404, 'No unclaimed jobs available')
        job = self._make_worker_job(project, job)
        return jsonify(Version=version, Job=job)

    def _make_worker_job(self, project, job_data):
        """Create dict that contains the data needed by the worker:

        {'JobID': str,
         'URLS': {
            'URL-source': str,
            'URL-target': str,
            'URL-claim': str,
            'URL-status': str,
            'URL-output': str,
        }}
        """
        job_id, source_url, target_url = (
            job_data['id'], job_data['source_url'], job_data['target_url'])

        job = {
            'JobID': job_id,
            'URLS': {'URL-source': source_url,
                     'URL-target': target_url}}

        for endpoint in ['claim', 'status', 'output']:
            job["URLS"]["URL-{}".format(endpoint)] = make_job_url(
                endpoint, project, job_id)
        return job
