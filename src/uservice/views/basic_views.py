""" Basic views for REST api
"""
import urllib
from datetime import datetime
from collections import defaultdict
from operator import itemgetter
from dateutil.parser import parse as parse_datetime
from random import choice

from flask import jsonify, abort as flask_abort, make_response, request, g
from flask.views import MethodView

from ..utils.validate import validate_project_name
from ..utils.logs import get_logger
from ..utils.defs import JOB_STATES, TIME_PERIODS
from ..utils import analyze_worker_output

from ..core.users import auth
from ..database.basedb import get_db as get_jobs_db
from ..database.projects import get_db as get_projects_db
from ..database.sqldb import SqlJobDatabase


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
        self.log = get_logger('UService', to_stdout=True)
        super(BasicView, self).__init__()

    def _get_projects_database(self):
        return get_projects_db()

    def _get_jobs_database(self, project):
        return get_jobs_db(project, SqlJobDatabase)

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


class FetchJobBase(object):
    """Base class that can fetch an unclaimed job and format it
    for the workers.
    """

    JOB_FIELDS = ['id', 'source_url', 'target_url']
    PROJECT_FIELDS = ['processing_image_url', 'environment']

    def _get_unclaimed_job(self, version, project):
        db_jobs = self._get_jobs_database(project)
        try:
            jobs = list(db_jobs.get_jobs(
                match={'claimed': False},
                fields=self.JOB_FIELDS,
                limit=500))
            job = choice(jobs)
        except (StopIteration, IndexError):
            return abort(404, 'No unclaimed jobs available')
        db_projects = self._get_projects_database()
        project_data = db_projects.get_project(
            project, fields=self.PROJECT_FIELDS)
        job = self._make_worker_job(project, job, project_data)
        return jsonify(Version=version, Project=project, Job=job)

    def _make_worker_job(self, project, job_data, project_data):
        """Create dict that contains the data needed by the worker:

        {'JobID': str,
         'Environment': {...},
         'URLS': {
             'URL-image': str,
             'URL-source': str,
             'URL-target': str,
             'URL-claim': str,
             'URL-status': str,
             'URL-output': str,
        }}
        """
        job_id, image_url, source_url, target_url, env = (
            job_data['id'], project_data['processing_image_url'],
            job_data['source_url'], job_data['target_url'],
            project_data['environment'])
        job = {
            'JobID': job_id,
            'Environment': env,
            'URLS': {
                'URL-image': image_url,
                'URL-source': source_url,
                'URL-target': target_url}}

        for endpoint in ['claim', 'status', 'output']:
            job["URLS"]["URL-{}".format(endpoint)] = make_job_url(
                endpoint, project, job_id)
        return job


def make_project_url(project):
    return "{0}rest_api/v4/{1}".format(request.url_root, project)


def make_pretty_project(project, prio=None):
    """Transform project to json serializable dict with good looking keys"""
    project['PrioScore'] = prio
    project['URLS'] = {
        'URL-Status': make_project_url(project['id']),
        'URL-Processing-image': project.pop('processing_image_url')}
    project['Id'] = project.pop('id')
    project['Name'] = project.pop('name')
    project['Environment'] = project.pop('environment')
    project['CreatedBy'] = project.pop('created_by_user')
    project['CreatedAt'] = fix_timestamp(project.pop('created_timestamp'))
    project['LastJobAddedAt'] = fix_timestamp(
        project.pop('last_added_timestamp'))
    project['NrJobsAdded'] = project.pop('nr_added')
    project['LastJobClaimedAt'] = fix_timestamp(
        project.pop('last_claimed_timestamp'))
    project['NrJobsClaimed'] = project.pop('nr_claimed')
    project['NrJobsFinished'] = project.pop('nr_finished')
    project['NrJobsFailed'] = project.pop('nr_failed')
    project['TotalProcessingTime'] = project.pop('processing_time')
    project['Deadline'] = fix_timestamp(project.pop('deadline'))
    return project


class ListProjects(BasicView):
    """View for listing projects"""
    def _get_view(self, version):
        """
        Should return a JSON object with a list of projects.
        """
        only_active = bool(request.args.get('only_active'))
        db = self._get_projects_database()
        projects = db.get_projects(only_active=only_active)
        now = datetime.utcnow()
        projects = [make_pretty_project(p, prio=db.calc_prio_score(p, now))
                    for p in projects]
        return jsonify(Version=version, Projects=projects)


class FetchJobPrio(BasicView, FetchJobBase):
    """Fetch a job from a project chosen based on prio score"""

    @auth.login_required
    def get(self, version):
        """GET"""
        self._check_version(version)
        return self._get_view(version)

    def _get_view(self, version):
        db = self._get_projects_database()
        project = db.get_prio_project()
        if not project:
            return abort(404, 'No unclaimed jobs available')
        return self._get_unclaimed_job(version, project)


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
        'URL-Output': make_job_url('output', project, job['id']),
        'URL-Result': job.pop('view_result_url')}
    job['Id'] = job.pop('id')
    job['Type'] = job.pop('type')
    job['Status'] = job.pop('current_status')
    job['Added'] = fix_timestamp(job.pop('added_timestamp'))
    job['Claimed'] = fix_timestamp(job.pop('claimed_timestamp'))
    job['IsClaimed'] = job.pop('claimed')
    job['Failed'] = fix_timestamp(job.pop('failed_timestamp'))
    job['Finished'] = fix_timestamp(job.pop('finished_timestamp'))
    job['ProcessingTime'] = job.pop('processing_time')
    job['Worker'] = job.pop('worker')
    return job


class AnalyzeFailedJobs(BasicProjectView):
    """View for listing processing output lines for failed jobs
    as JSON object
    """

    def _get_view(self, version, project):
        start = request.args.get('start')
        end = request.args.get('end')

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

        db = self._get_jobs_database(project)
        match = {'current_status': JOB_STATES.failed}
        jobs = list(db.get_failed_jobs(
            match=match, start_time=start, end_time=end, limit=1000,
            fields=['id', 'processing_time', 'worker', 'failed_timestamp',
                    'worker_output']))
        ranked_lines = analyze_worker_output.rank_errors(jobs)

        def pretty_job(job):
            return {
                'Id': job['id'],
                'ProcessingTime': job['processing_time'],
                'Worker': job['worker'],
                'Failed': fix_timestamp(job['failed_timestamp'])
            }
        jobs = {job['id']: pretty_job(job) for job in jobs}

        def pretty_line(line):
            return {
                'Line': line['line'],
                'Score': line['score']
            }

        ranked_lines = [
            {'Score': item['score'],
             'Line': item['line'],
             'CommonLines': [
                 pretty_line(line) for line in item['common_lines']],
             'Jobs':  item['jobids']}
            for item in ranked_lines]

        return jsonify(Version=version, Project=project,
                       Start=fix_timestamp(start), End=fix_timestamp(end),
                       Lines=ranked_lines, Jobs=jobs)


class CountJobs(BasicProjectView):
    def _get_view(self, version, project):
        """Group and count jobs per time period."""
        period = request.args.get('period', TIME_PERIODS.daily).upper()
        start = request.args.get('start')
        end = request.args.get('end')
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

        db = self._get_jobs_database(project)

        def add_state_count(job_state, counts):
            state_counts = db.count_jobs_per_time_period(
                job_state, time_period=period, start_time=start, end_time=end)
            for state_count in state_counts:
                count = counts[state_count['period']]
                count['Period'] = state_count['period']
                count['Jobs%s' % job_state.title()] = state_count['count']
                param = [('status', job_state),
                         ('start', state_count['start_time'].isoformat()),
                         ('end', state_count['end_time'].isoformat())]
                count['URLS']['URL-Jobs%s' % job_state.title()] = (
                    '{}rest_api/v4/{}/jobs?{}'.format(
                        request.url_root, project, urllib.urlencode(param)))
                # TODO: Make this general for all time periods
                if period == TIME_PERIODS.daily:
                    param[0] = ('period', TIME_PERIODS.hourly)
                    count['URLS']['URL-Zoom'] = (
                        '{}rest_api/v4/{}/jobs/count?{}'.format(
                            request.url_root, project,
                            urllib.urlencode(param)))

        def add_workers_count(counts):
            worker_counts = db.count_jobs_per_time_period(
                JOB_STATES.claimed, time_period=period, start_time=start,
                end_time=end, count_field_name='current_status', distinct=True)
            for worker_count in worker_counts:
                count = counts[worker_count['period']]
                count['Period'] = worker_count['period']
                count['ActiveWorkers'] = worker_count['count']
                param = [('start', worker_count['start_time'].isoformat()),
                         ('end', worker_count['end_time'].isoformat())]
                count['URLS']['URL-ActiveWorkers'] = (
                    '{}rest_api/v4/{}/workers?{}'.format(
                        request.url_root, project, urllib.urlencode(param)))

        def get_default_count():
            return {'Period': None, 'JobsClaimed': 0, 'JobsFailed': 0,
                    'JobsFinished': 0, 'URLS': {}}

        counts = defaultdict(get_default_count)
        add_state_count(JOB_STATES.claimed, counts)
        add_state_count(JOB_STATES.failed, counts)
        add_state_count(JOB_STATES.finished, counts)
        add_workers_count(counts)

        counts = counts.values()
        counts.sort(key=itemgetter('Period'))

        return jsonify(Version=version, Project=project,
                       PeriodType=period.title(), Start=fix_timestamp(start),
                       End=fix_timestamp(end), Counts=counts)


class FetchNextJob(BasicProjectView, FetchJobBase):
    """View for fetching data needed by the worker for the next job
    in the queue.
    """

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
        return self._get_unclaimed_job(version, project)
