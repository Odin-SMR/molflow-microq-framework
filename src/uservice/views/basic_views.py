""" Basic views for REST api
"""
from flask import jsonify, abort, make_response
from flask.views import MethodView
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.users import auth
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
    def delete(self, version):
        """DELETE"""
        self._check_version(version)

        return self._delete_view(version)

    def _get_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version)

    def _put_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, Call="PUT")

    def _delete_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, Call="DELETE")

    def _check_version(self, version):
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)

    @auth.error_handler
    def unauthorized():
        return make_response(jsonify({'error': 'Unauthorized access'}), 401)


class ListJobs(BasicView):
    """View for listing jobs as JSON object"""
    _translate_backend = {'B': 'AC1', 'C': 'AC2'}

    def __init__(self):
        super(ListJobs, self).__init__()
        self._engine = create_engine(
            'mysql+pymysql://odinuser:***REMOVED***@mysqlhost/hermod')
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
        for j in jobs:
            job = {}
            job['Orbit'] = j.orbit
            job['Backend'] = self._translate_backend[j.backend]
            job['CalVersion'] = j.calversion.to_eng_string()
            job['LogFile'] = {}
            try:
                job['LogFile']['FileDate'] = j.logfile[0].filedate.isoformat()
            except:
                pass
            job['HDFFile'] = {}
            try:
                job['HDFFile']['FileDate'] = j.hdffile[0].filedate.isoformat()
            except:
                pass
            job_list.append(job)
        return job_list


class FetchNextJob(ListJobs):
    """View for fetching next job from queue"""
    def __init__(self):
        super(FetchNextJob, self).__init__()

    @auth.login_required
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
