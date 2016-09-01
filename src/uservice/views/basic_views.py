""" Basic views for REST api
"""
from datetime import datetime

from flask import jsonify, abort as flask_abort, make_response, request
from flask.views import MethodView
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.validate import validate_project_name
from utils.defs import JOB_STATES
from utils.logs import get_logger

from uservice.core.users import auth
# from uservice.datamodel.model import Level1
from uservice.database.basedb import get_db, InMemoryDatabase


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
        # TODO: Choose database based on config
        return get_db(project, InMemoryDatabase)

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


class ListJobs(BasicProjectView):
    """View for listing jobs as JSON object"""
    _translate_backend = {'B': 'AC1', 'C': 'AC2', 'AC1': 'AC1', 'AC2': 'AC2'}

    def __init__(self):
        super(ListJobs, self).__init__()
        self._engine = create_engine(
            'mysql+pymysql://odinuser:***REMOVED***@mysqlhost/smr')
        make_session = sessionmaker(bind=self._engine)
        self._session = make_session()

    # TODO: Use url parameter 'type'
    def _get_view(self, version, project):
        """
        Return a JSON object with a list of jobs with URIs for
        getting data etc.
        # TODO: Should only return unclaimed jobs?
        """
        db = self._get_database(project)
        jobs = list(db.get_jobs(fields=['id', 'meta']))
        job_list = self._make_job_list(project, jobs)
        return jsonify(Version=version, Project=project, Jobs=job_list)

    def _post_view(self, version, project):
        """
        Used to add jobs to the database.
        """
        job = request.json
        # Default values
        job['claimed'] = False
        job['current_status'] = JOB_STATES.available
        job['added_timestamp'] = datetime.now()

        job_id = job['id']
        db = self._get_database(project)
        if db.job_exists(job_id):
            return abort(409, 'Job already exists')
        db.insert_job(job_id, job)
        return jsonify(Version=version, Project=project, ID=job_id), 201

    def _make_job_list(self, project, jobs):
        return [
            self._make_job(project, job['id'], job['meta'])
            for job in jobs
        ]

    def _make_job(self, project, job_id, meta):

        def make_url(endpoint, job_id):
            return "{0}rest_api/v4/{1}/jobs/{2}/{3}".format(
                request.url_root, project, job_id, endpoint)

        if 'URLS' not in meta:
            meta['URLS'] = {}

        for endpoint in ['claim', 'result', 'status', 'output', 'input']:
            meta["URLS"]["URL-{}".format(endpoint)] = make_url(
                endpoint, job_id)
        return meta

    def _make_job_dict(self, job):
            job_dict = {}
            job_dict['Orbit'] = job.orbit
            job_dict['Backend'] = self._translate_backend[job.backend]
            # job_dict['FreqMode'] = ''
            job_dict['CalVersion'] = job.calversion.to_eng_string()
            job_dict['LogFile'] = {}
            try:
                job_dict['LogFile']['FileDate'] = (
                    job.logfile[0].filedate.isoformat())
            except:
                pass
            job_dict['HDFFile'] = {}
            try:
                job_dict['HDFFile']['FileDate'] = (
                    job.hdffile[0].filedate.isoformat())
            except:
                pass
            URLS = {}
            # URLS["URL-spectra"] = (
            #     '{0}rest_api/v4/scan/{1}/{2}/{3}/').format(
            #     request.url_root,
            #     job_dict["Backend"],
            #     job_dict["FreqMode"],
            #     job_dict["orbit"])
            # URLS['URL-ptz'] = (
            #     '{0}rest_api/v1/ptz/{1}/{2}/{3}/{4}').format(
            #     request.url_root,
            #     date,
            #     job_dict["Backend"],
            #     job_dict["FreqMode"],
            #     scanid)
            job_dict["URLS"] = URLS

            return job_dict

    def _fake_job_dict(self):
            job_dict = {}
            job_dict['ScanID'] = 7607881909
            job_dict['Backend'] = "AC1"
            job_dict['FreqMode'] = 2

            URLS = {}
            URLS["URL-spectra"] = "http://malachite.rss.chalmers.se/" + \
                "rest_api/v4/scan/AC1/2/7607881909/"
            URLS["URL-ptz"] = "http://malachite.rss.chalmers.se/" + \
                "rest_api/v4/ptz/2016-03-16/AC1/2/7607881909/"
            URLS["URL-claim"] = "{0}rest_api/v4/jobs/{1}/claim".format(
                request.url_root, job_dict['ScanID'])
            URLS["URL-deliver"] = "{0}rest_api/v4/jobs/{1}/data".format(
                request.url_root, job_dict['ScanID'])
            URLS["URL-status"] = "{0}rest_api/v4/jobs/{1}".format(
                request.url_root, job_dict['ScanID'])
            job_dict["URLS"] = URLS

            return job_dict


class FetchNextJob(ListJobs):
    """View for fetching next job from queue"""
    def __init__(self):
        super(FetchNextJob, self).__init__()

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
                                   fields=['id', 'meta']))
        except StopIteration:
            return abort(404, 'No unclaimed jobs available')
        job = self._make_job(project, job['id'], job['meta'])
        return jsonify(Version=version, Job=job)
