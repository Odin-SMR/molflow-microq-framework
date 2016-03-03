""" Basic views for REST api that require job id
"""
import os
from flask import jsonify, request
from werkzeug import secure_filename
from ..views.basic_views import BasicView
from ..core.users import auth


class BasicJobView(BasicView):
    """Base class for views that require job id"""
    def get(self, version, job_id):
        """GET"""
        self._check_version(version)

        return self._get_view(version, job_id)

    @auth.login_required
    def put(self, version, job_id):
        """PUT"""
        self._check_version(version)

        return self._put_view(version, job_id)

    @auth.login_required
    def delete(self, version, job_id):
        """DELETE"""
        self._check_version(version)

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


class JobData(BasicJobView):
    """Get data needed for job and deliver results when done"""
    ALLOWED_EXTENSIONS = ["data"]
    UPLOAD_FOLDER = "/path/to/uploaded"

    def _get_view(self, version, job_id):
        """Used to get data for processing"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Used to deliver data when job is done"""
        theFile = request.files['file']
        filename = secure_filename(theFile.filename)
        if theFile and self._allowed_file(theFile.filename):
            theFile.save(os.path.join(self.UPLOAD_FOLDER, filename))
            return jsonify(Version=version, ID=job_id, Call="PUT: {0}".format(
                filename))

        return jsonify(Version=version, ID=job_id, Call="PUT: {0}".format(
            filename), Message="Error: File not allowed?")

    def _allowed_file(self, filename):
        return ('.' in filename and filename.rsplit('.', 1)[1] in
                self.ALLOWED_EXTENSIONS)


class JobStatus(BasicJobView):
    """Get and set jobstatus as JSON object"""
    def _get_view(self, version, job_id):
        """Used to get job status"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Used to update job status"""
        return jsonify(Version=version, ID=job_id, Call="PUT")


class JobClaim(BasicJobView):
    """Claim job"""
    def _get_view(self, version, job_id):
        """Used to see which Worker has claimed job and at what time"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Used to claim job for Worker"""
        return jsonify(Version=version, ID=job_id, Call="PUT")


class JobLock(BasicJobView):
    """Lock and unlock job"""
    def _get_view(self, version, job_id):
        """Used to get lock status"""
        return jsonify(Version=version, ID=job_id)

    def _put_view(self, version, job_id):
        """Used to set lock status"""
        return jsonify(Version=version, ID=job_id, Call="PUT")
