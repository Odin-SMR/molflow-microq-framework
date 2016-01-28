""" Basic views for REST api
"""
from flask import jsonify, abort, make_response
from flask.views import MethodView
from sqlalchemy import create_engine, sessionmaker
from ..core.users import auth
from ..datamode.model import Level1


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


class FetchNextJob(BasicView):
    """View for fetching next job from queue"""
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
        return jsonify(Version=version)


class ListJobs(BasicView):
    """View for listing jobs as JSON object"""
    def __init__(self):
        super(ListJobs, self).__init__()
        self._engine = create_engine(
            'mysql://odinuser:***REMOVED***@mysqlhost/hermod')
        make_session = sessionmaker(bind=self._engine)
        self._session = make_session()

    def _get_view(self, version):
        """Should return a JSON object with a list of jobs with URIs for
        getting data etc."""
        jobs = self._session.query(Level1).all()

        return jsonify(Version=version, Jobs=jobs)
