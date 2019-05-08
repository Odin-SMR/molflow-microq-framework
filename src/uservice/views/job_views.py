""" Basic views for REST api that require job id
"""
from datetime import datetime
from dateutil.parser import parse as parse_datetime

from flask import jsonify, request, g

from ..utils.defs import JOB_STATES

from .basic_views import abort, BasicProjectView
from ..core.users import auth
from ..database.basedb import STATE_TO_TIMESTAMP


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
        db = self._get_jobs_database(project)
        job = db.get_job(job_id, fields=['current_status'])
        if not job:
            return abort(404)
        return jsonify(Version=version, Project=project, ID=job_id,
                       Status=job['current_status'])

    def _put_view(self, version, project, job_id):
        """Used to update job status"""
        if not request.json or 'Status' not in request.json:
            return abort(400, 'Missing "Status" field in request data')
        status = request.json['Status']
        data = {'current_status': status,
                'processing_time': request.json.get('ProcessingTime') or 0}
        if status in STATE_TO_TIMESTAMP:
            now = request.args.get('now')
            if now:
                now = parse_datetime(now)
            else:
                now = datetime.utcnow()
            data[STATE_TO_TIMESTAMP[status]] = now

        if status == JOB_STATES.finished:
            self._get_projects_database().job_finished(
                project, data['processing_time'])
        elif status == JOB_STATES.failed:
            self._get_projects_database().job_failed(
                project, data['processing_time'])

        db = self._get_jobs_database(project)
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
        db = self._get_jobs_database(project)
        job = db.get_job(job_id, fields=['worker_output'])
        if not job:
            return abort(404)
        return jsonify(Version=version, Project=project, ID=job_id,
                       Output=job['worker_output'])

    def _put_view(self, version, project, job_id):
        """Used to update job output"""
        if not request.json or 'Output' not in request.json:
            return abort(400, 'Missing "Output" field in request data')
        db = self._get_jobs_database(project)
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
        db = self._get_jobs_database(project)
        job = db.get_job(job_id, fields=[
            'claimed', 'worker', 'claimed_timestamp'])
        if not job:
            return abort(404)
        return jsonify(
            Version=version, Project=project, ID=job_id,
            Claimed=job['claimed'], ClaimedByWorker=job['worker'],
            ClaimedAtTime=(
                job['claimed_timestamp'].isoformat()
                if job['claimed_timestamp'] else None
            )
        )

    def _put_view(self, version, project, job_id):
        """
        Used to claim job for Worker. Return 409 CONFLICT if job is
        already claimed.
        """
        # TODO: Give users different roles? Some users should maybe not be
        #       allowed to claim jobs.
        if not request.json or 'Worker' not in request.json:
            return abort(400, 'Missing "Worker" field in request data')
        db = self._get_jobs_database(project)
        if not db.job_exists(job_id):
            return abort(404)
        if not db.claim_job(job_id):
            return abort(409, 'The job is already claimed')

        now = request.args.get('now')
        if now:
            now = parse_datetime(now)
        else:
            now = datetime.utcnow()
        worker = request.json['Worker']
        db.update_job(job_id, current_status=JOB_STATES.claimed,
                      claimed_timestamp=now, worker=worker)
        projects_db = self._get_projects_database()
        projects_db.job_claimed(project)
        self.log.info(
            "Job {0} in project {1} claimed by {2} to worker {3}".format(
                job_id, project, g.user.username, worker))
        return jsonify(Version=version, Project=project, ID=job_id,
                       Call="PUT", Time=now.isoformat(),
                       ClaimedBy=worker)

    def _delete_view(self, version, project, job_id):
        """Used to free a job"""
        db = self._get_jobs_database(project)
        job = db.get_job(job_id)
        if not job:
            return abort(404)
        if job['claimed']:
            db.unclaim_job(job_id)
            self.log.info("Job {0} in project {1} was unlocked by {2}.".format(
                job_id, project, g.user.username))
            projects_db = self._get_projects_database()
            projects_db.job_unclaimed(project, bool(job['failed_timestamp']))

        return jsonify(Version=version, Project=project, ID=job_id,
                       Call="DELETE")
