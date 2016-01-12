""" Basic views for REST api that require job id
"""
from flask import jsonify, request, abort
from basic_views import BasicView, AuthView


class BasicJobView(BasicView):
    """Base class for views that require job id"""
    def get(self, version, job_id):
        """GET, a commin sanity checking"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)

        auth = request.args.get('auth')
        if not self._authenticate(auth):
            abort(401)
        else:
            return self._get_view(version, job_id)

    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class AuthJobView(AuthView):
    """The class which views requiring authentication and job id can inherit
    from."""
    def get(self, version, job_id):
        """GET, a commin sanity checking"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)

        auth = request.args.get('auth')
        if not self._authenticate(auth):
            abort(401)
        else:
            return self._get_view(version, job_id)

    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class JobData(BasicJobView):
    """Get data needed for job"""
    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class JobStatus(BasicJobView):
    """Get jobstatus as JSON object"""
    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class JobStatusHumanReadable(BasicJobView):
    """Get jobstatus as html"""
    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class JobStatusUpdate(AuthJobView):
    """Update jobstatus"""
    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class JobClaim(AuthJobView):
    """Claim job"""
    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class JobLock(AuthJobView):
    """Lock job"""
    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class JobUnlock(AuthJobView):
    """Unlock job"""
    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class JobDeliver(AuthJobView):
    """Deliver results from completed job"""
    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)
