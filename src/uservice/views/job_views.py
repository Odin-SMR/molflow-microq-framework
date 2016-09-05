""" Basic views for REST api that require job id
"""
from datetime import datetime

from flask import jsonify, request, g

from utils.defs import JOB_STATES

from uservice.views.basic_views import abort, BasicProjectView
from uservice.core.users import auth

STATE_TO_TIMESTAMP = {
    JOB_STATES.claimed: 'claimed_timestamp',
    JOB_STATES.finished: 'finished_timestamp',
    JOB_STATES.failed: 'failed_timestamp'}


class BasicJobView(BasicProjectView):
    """Base class for views that require job id"""
    def get(self, version, project, job_id):
        """GET"""
        self._check_version(version)
        self._check_project(project)
        return self._get_view(version, project, job_id)

    @auth.login_required
    def put(self, version, project, job_id):
        """PUT"""
        self._check_version(version)
        self._check_project(project)
        return self._put_view(version, project, job_id)

    @auth.login_required
    def post(self, version, project, job_id):
        """PUT"""
        self._check_version(version)
        self._check_project(project)
        return self._post_view(version, project, job_id)

    @auth.login_required
    def delete(self, version, project, job_id):
        """DELETE"""
        self._check_version(version)
        self._check_project(project)
        return self._delete_view(version, project, job_id)


class JobStatus(BasicJobView):
    """Get and set jobstatus as JSON object"""
    def _get_view(self, version, project, job_id):
        """Used to get job status"""
        db = self._get_database(project)
        try:
            job = next(db.get_jobs(job_id=job_id, fields=['current_status']))
        except StopIteration:
            return abort(404)
        return jsonify(Status=job['current_status'])

    def _put_view(self, version, project, job_id):
        """Used to update job status"""
        if not request.json or 'Status' not in request.json:
            return abort(400, 'Missing "Status" field in request data')
        status = request.json['Status']
        data = {'current_status': status}
        if status in STATE_TO_TIMESTAMP:
            data[STATE_TO_TIMESTAMP[status]] = datetime.utcnow()
        db = self._get_database(project)
        if not db.job_exists(job_id):
            return abort(404)
        db.update_job(job_id, **data)
        self.log.info("Status of job {0} was updated by {1}.".format(
            job_id, g.user.username))
        return jsonify(Version=version, Project=project, ID=job_id,
                       Call="PUT", Status=request.json['Status'])


class JobOutput(BasicJobView):
    """Get and set job output as JSON object"""
    def _get_view(self, version, project, job_id):
        """Used to get job output"""
        db = self._get_database(project)
        try:
            job = next(db.get_jobs(job_id=job_id, fields=['worker_output']))
        except StopIteration:
            return abort(404)
        return jsonify(Output=job['worker_output'])

    def _put_view(self, version, project, job_id):
        """Used to update job output"""
        if not request.json or 'Output' not in request.json:
            return abort(400, 'Missing "Output" field in request data')
        db = self._get_database(project)
        if not db.job_exists(job_id):
            return abort(404)
        db.update_job(job_id, worker_output=request.json['Output'])
        self.log.info("Output of job {0} was updated by {1}.".format(
            job_id, g.user.username))
        return jsonify(Version=version, Project=project, ID=job_id, Call="PUT")


class JobClaim(BasicJobView):
    """Claim job"""
    def _get_view(self, version, project, job_id):
        """Used to see which Worker has claimed job and at what time"""
        db = self._get_database(project)
        try:
            job = next(db.get_jobs(job_id=job_id, fields=[
                'claimed', 'worker', 'claimed_timestamp']))
        except StopIteration:
            return abort(404)
        return jsonify(
            Version=version, Project=project, ID=job_id,
            Claimed=job['claimed'], ClaimedByWorker=job['worker'],
            ClaimedAtTime=job['claimed_timestamp'].isoformat())

    def _put_view(self, version, project, job_id):
        """
        Used to claim job for Worker. Return 409 CONFLICT if job is
        already claimed.
        """
        # TODO: Give users different roles? Some users should maybe not be
        #       allowed to claim jobs.
        if not request.json or 'Worker' not in request.json:
            return abort(400, 'Missing "Worker" field in request data')
        db = self._get_database(project)
        if not db.job_exists(job_id):
            return abort(404)
        if not db.claim_job(job_id):
            return abort(409, 'The job is already claimed')

        now = datetime.utcnow()
        worker = request.json['Worker']
        db.update_job(job_id, current_status=JOB_STATES.claimed,
                      claimed_timestamp=now, worker=worker)
        self.log.info("Job {0} claimed by {1} to worker {2}".format(
            job_id, g.user.username, worker))
        return jsonify(Version=version, Project=project, ID=job_id,
                       Call="PUT", Time=now.isoformat(),
                       ClaimedBy=worker)

    def _delete_view(self, version, project, job_id):
        """Used to free a job"""
        db = self._get_database(project)
        if not db.job_exists(job_id):
            return abort(404)
        if db.unclaim_job(job_id):
            db.update_job(job_id, claimed_timestamp=None, worker=None)
            self.log.info("Job {0} was unlocked by {1}.".format(
                job_id, g.user.username))
        return jsonify(Version=version, Project=project, ID=job_id,
                       Call="DELETE")
