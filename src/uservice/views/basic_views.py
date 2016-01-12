""" Basic views for REST api
"""
from flask import jsonify, abort, request
from flask.views import MethodView


class BasicView(MethodView):
    """Base class for views"""
    def get(self, version):
        """GET, a commin sanity checking"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)

        auth = request.args.get('auth')
        if not self._authenticate(auth):
            abort(401)
        else:
            return self._get_view(version)

    def _get_view(self, version):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version)

    def _authenticate(self, auth):
        """Dummy method that should be over loaded by derived classes that
        support/require authentication."""
        return True


class AuthView(BasicView):
    """The class which views requiring authentication can inherit from."""
    def _authenticate(self, auth):
        """Dummy method that should be made more intelligent."""

        if auth is None:
            return False
        else:
            return True
