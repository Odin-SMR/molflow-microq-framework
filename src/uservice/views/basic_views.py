""" Basic views for REST api
"""
from flask import jsonify, abort, make_response
from flask.views import MethodView
from flask.ext.httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()


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


class ListJobs(BasicView):
    """View for listing jobs as JSON object"""


class ListJobsHumanReadable(BasicView):
    """View for listing jobs as html"""
    def get(self):
        """GET"""

        return self._get_view()

    def _get_view(self):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Hello="ListJobsHumanReadable")
