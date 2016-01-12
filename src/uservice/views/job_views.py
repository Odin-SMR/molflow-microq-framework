""" Basic views for REST api that require job id
"""
from flask import jsonify, request, abort
from basic_views import BasicView


class BasicJobView(BasicView):
    """Base class for views that require job id"""
    def get(self, version, job_id):
        """GET"""
        self._check_version(version)

        if self._authenticate():
            return self._get_view(version, job_id)

    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)


class AuthJobView(BasicJobView):
    """The class which views requiring authentication and job id can inherit
    from."""
    def put(self, version, job_id):
        """PUT"""
        self._check_version(version)

        if self._authenticate():
            return self._put_view(version, job_id)

    def delete(self, version, job_id):
        """DELETE"""
        self._check_version(version)

        if not self._authenticate():
            return self._delete_view(version, job_id)

    def _get_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id, Call="PUT")

    def _delete_view(self, version, job_id):
        """Dummy method which should be over loaded by derived classes"""
        return jsonify(Version=version, ID=job_id, Call="DELETE")

    def _authenticate(self):
        """Dummy method that should be made more intelligent."""
        auth = request.args.get('auth')

        if auth is None:
            abort(401)
        else:
            return True


class JobData(AuthJobView):
    """Get data needed for job and deliver results when done"""
    def _get_view(self, version, job_id):
        """Used to get data for processing"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Used to deliver data when job is done"""
        return jsonify(Version=version, ID=job_id, Call="PUT")


class JobStatus(AuthJobView):
    """Get and set jobstatus as JSON object"""
    def _get_view(self, version, job_id):
        """Used to get job status"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Used to update job status"""
        return jsonify(Version=version, ID=job_id, Call="PUT")


class JobClaim(AuthJobView):
    """Claim job"""
    def _get_view(self, version, job_id):
        """Used to see which Worker has claimed job and at what time"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Used to claim job for Worker"""
        return jsonify(Version=version, ID=job_id, Call="PUT")


class JobLock(AuthJobView):
    """Lock and unlock job"""
    def _get_view(self, version, job_id):
        """Used to get lock status"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Used to set lock status"""
        return jsonify(Version=version, ID=job_id, Call="PUT")


class JobStatusHumanReadable(BasicJobView):
    """Get jobstatus as html"""
    def _get_view(self, version, job_id):
        """Used to get a human readable status for job"""
        return jsonify(Version=version, ID=job_id)
