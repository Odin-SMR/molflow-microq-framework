""" Basic views for REST api that require job id
"""
import os
from flask import jsonify, request
from werkzeug import secure_filename
from ..views.basic_views import BasicView
from ..core.users import auth
from datetime import datetime


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
        # Call to handle data and get status:

        if request.headers['Content-Type'] == 'text/plain':
            message = "Text Message: " + request.data

        elif request.headers['Content-Type'] == 'application/json':
            message, status = self._put_json(version, job_id)

        # elif request.headers['Content-Type'] == 'application/octet-stream':
        #     message, status = self._put_file(version, job_id)

        else:
            message = "415 Unsupported Media Type: {0}".format(
                request.headers['Content-Type'])

        # Update job list etc.
        # TODO

        # Return status:
        return jsonify(Version=version, ID=job_id, Call="PUT",
                       Message=message)

    def _put_json(self, version, job_id):
        """Used to deliver JSON data when job is done"""
        return request.json, 0

    def _put_file(self, version, job_id):
        """Used to deliver file data when job is done"""
        theFile = request.files['file']
        filename = secure_filename(theFile.filename)
        if theFile and self._allowed_file(theFile.filename):
            theFile.save(os.path.join(self.UPLOAD_FOLDER, filename))
            return "Uploaded {0}".format(filename), 0

        return "Error: File not allowed?", -1

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
        """Used to claim job for Worker. Should return error if job is already
        claimed."""
        worker_id = request.files['worker']
        if self._verify_worker(worker_id):
            time = datetime.utcnow().isoformat()
            return jsonify(Version=version, ID=job_id, Call="PUT", Time=time,
                           ClaimedBy=worker_id)
        else:
            return jsonify(Version=version, ID=job_id, Call="PUT",
                           Message="Worker ID not recognised.")

    def _delete_view(self, version, job_id):
        """Used to free a job"""
        return jsonify(Version=version, ID=job_id, Call="DELETE")

    def _verify_worker(self, worker_id):
        """Used to verify the worker ID"""
        return True
