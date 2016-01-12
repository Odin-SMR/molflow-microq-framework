""" Basic views for REST api
"""
from flask import jsonify, abort, request
from flask.views import MethodView


class BasicView(MethodView):
    """Base class for views"""
    def get(self, version):
        """GET"""
        self._check_version(version)

        if self._authenticate():
            return self._get_view(version)

    def _get_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version)

    def _authenticate(self, auth):
        """Dummy method that should be over loaded by derived classes that
        support/require authentication."""
        return True

    def _check_version(self, version):
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)


class AuthView(BasicView):
    """The class which views requiring authentication can inherit from."""
    def put(self, version):
        """PUT"""
        self._check_version(version)

        if self._authenticate():
            return self._put_view(version)

    def delete(self, version):
        """DELETE"""
        self._check_version(version)

        auth = request.args.get('auth')
        if not self._authenticate(auth):
            abort(401)
        else:
            return self._delete_view(version)

    def _put_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, Call="PUT")

    def _delete_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, Call="DELETE")

    def _authenticate(self):
        """Dummy method that should be made more intelligent."""
        auth = request.args.get('auth')

        if auth is None:
            abort(401)
        else:
            return True


class ListJobs(BasicView):
    """View for listing jobs as JSON object"""


class ListJobsHumanReadable(BasicView):
    """View for listing jobs as html"""


class FetchNextJob(BasicView):
    """View for fetching next job from queue"""
