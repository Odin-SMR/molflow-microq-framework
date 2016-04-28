""" Basic views for REST api
"""
from flask import jsonify, abort, make_response, request
from flask.views import MethodView
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.users import auth
from ..core.userver_log import logging
from ..datamodel.model import Level1


class BasicView(MethodView):
    """Base class for views"""
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

    def _get_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        abort(405)

    def _put_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        abort(405)

    def _post_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        abort(405)

    def _delete_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        abort(405)

    def _check_version(self, version):
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)

    @auth.error_handler
    def unauthorized():
        return make_response(jsonify({'error': 'Unauthorized access'}), 401)

    def log(self, message, level="info"):
        if level.lower() == "debug":
            logging.debug(message)
        elif level.lower() == "info":
            logging.info(message)
        elif level.lower() == "warning":
            logging.warning(message)
        elif level.lower() == "error":
            logging.error(message)
        elif level.lower() == "critical":
            logging.critical(message)
        else:
            message += " (Unknown logging level {0})".format(level)
            logging.info(message)


class ListJobs(BasicView):
    """View for listing jobs as JSON object"""
    _translate_backend = {'B': 'AC1', 'C': 'AC2', 'AC1': 'AC1', 'AC2': 'AC2'}

    def __init__(self):
        super(ListJobs, self).__init__()
        self._engine = create_engine(
            'mysql+pymysql://odinuser:***REMOVED***@mysqlhost/smr')
        make_session = sessionmaker(bind=self._engine)
        self._session = make_session()

    def _get_view(self, version):
        """Should return a JSON object with a list of jobs with URIs for
        getting data etc."""
        jobs = self._session.query(Level1).all()
        job_list = self._make_job_list(jobs)
        return jsonify(Version=version, Jobs=job_list)

    def _make_job_list(self, jobs):
        job_list = []
        job_list.append(self._fake_job_dict())
        for j in jobs:
            job = self._make_job_dict(j)
            job_list.append(job)
        return job_list

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

    def get(self, version):
        """GET"""
        self._check_version(version)

        return self._get_view(version)

    def _get_view(self, version):
        """Should return JSON object with URI for getting/delivering data etc.
        after locking job.

        Later:
            Separate fetching and claiming, so that the returned object
            contains URIs for claming job, as well as for getting/delivering
            data.
            On the other hand, why?
            * Because it gives a neater interface, and because the claiming
              URI can be put in the object and included in the listing.
            * Easier to debug/get status if fetching can be done w/o auth
        """
        jobs = [self._session.query(Level1).first()]
        job_list = self._make_job_list(jobs)
        return jsonify(Version=version, Job=job_list[0])
