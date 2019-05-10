from dateutil.parser import parse as parse_datetime
from flask import jsonify, abort as flask_abort, make_response, request, g
from werkzeug.exceptions import BadRequest, Conflict

from .basic_views import (
    BasicProjectView, abort, fix_timestamp, make_pretty_job)
from ..database.basedb import DBError, DBConflictError
from ..database.sqldb import SqlJobDatabase
from ..utils.defs import JOB_STATES


class ListJobs(BasicProjectView):
    """View for listing and adding jobs as JSON object"""

    def _get_view(self, version, project):
        """
        Return a JSON object with a list of jobs with URIs for
        getting data etc.
        """
        job_type = request.args.get('type')
        status = request.args.get('status')
        worker = request.args.get('worker')
        start = request.args.get('start')
        end = request.args.get('end')
        limit = request.args.get('limit', None)

        match = {}
        if job_type:
            match['type'] = job_type
        if worker:
            match['worker'] = worker
        if status:
            status = status.upper()
            if status not in JOB_STATES.all_values:
                return abort(400, 'Unsupported status: %r' % status)
            match['current_status'] = status
        if start:
            try:
                start = parse_datetime(start)
            except ValueError:
                return abort(400, 'Bad time format: %r' % start)
        if end:
            try:
                end = parse_datetime(end)
            except ValueError:
                return abort(400, 'Bad time format: %r' % end)

        db = self._get_jobs_database(project)
        if start or end:
            if not status:
                return abort(400, ('Param @start and @end can only be used '
                                   'together with @status'))
            match.pop('current_status')
            if status == JOB_STATES.claimed:
                fun = db.get_claimed_jobs
            elif status == JOB_STATES.finished:
                fun = db.get_finished_jobs
            elif status == JOB_STATES.failed:
                fun = db.get_failed_jobs
            else:
                return abort(400, 'Unsupported status: %r' % status)
        else:
            fun = db.get_jobs
        jobs = list(fun(match=match, start_time=start, end_time=end,
                        fields=db.PUBLIC_LISTING_FIELDS, limit=limit))

        for job in jobs:
            make_pretty_job(job, project)

        return jsonify(Version=version, Project=project, Jobs=jobs,
                       Status=status, Start=fix_timestamp(start),
                       End=fix_timestamp(end), Worker=worker)

    def _post_view(self, version, project):
        """
        Used to add jobs to the database.
        """
        if isinstance(request.json, dict):
            self.add_one_job(project, request.json)
        elif isinstance(request.json, list):
            self.add_multiple_jobs(project, request.json)
        else:
            return abort(400, "Invalid input")
        return '', 201

    def add_one_job(self, project, job):
        jobs = [job]

        try:
            validate_json_job(job)
        except ValidationError as error:
            raise BadRequest(description=str(error))

        job_db = self._get_jobs_database(project)
        added_rows = self.check_for_conflicts_and_insert_one_new_job(
            job_db, job)

        projects_db = self._get_projects_database()
        if added_rows != 0:
            did_work = projects_db.job_added(project, added=added_rows)
            if not did_work:
                projects_db.insert_project(project, g.user.username)
                projects_db.job_added(project, added=added_rows)

    def add_multiple_jobs(self, project, jobs):

        try:
            validate_json_job_list(jobs)
        except ValidationError as error:
            raise BadRequest(description=str(error))

        job_db = self._get_jobs_database(project)
        added_rows = self.check_for_conflicts_and_insert_new_jobs(job_db, jobs)

        projects_db = self._get_projects_database()
        if added_rows != 0:
            did_work = projects_db.job_added(project, added=added_rows)
            if not did_work:
                projects_db.insert_project(project, g.user.username)
                projects_db.job_added(project, added=added_rows)

    def check_for_conflicts_and_insert_new_jobs(self, job_db, jobs):
        job_db.db.session.begin()
        errors = []
        added = 0
        for job_number, job in enumerate(jobs):
            try:
                added_row = self.check_for_conflicts_and_insert_one_new_job(
                    job_db, job)
                added = added + added_row
            except Conflict as error:
                errors.append(
                    "Job#{}: {}".format(job_number, error.description))
        if errors:
            raise Conflict(description="\n".join(errors))
        else:
            job_db.db.session.commit()
        return added

    def check_for_conflicts_and_insert_one_new_job(self, job_db, job):
        try:
            now = request.args.get('now')
            if now:
                job['added_timestamp'] = parse_datetime(now)
            rows = job_db.insert_job_if_not_duplicate(job['id'], job)
        except DBConflictError as error:
            raise Conflict(error)
        return rows


class ValidationError(Exception):
    pass


def validate_json_job_list(jobs):
    errors = []
    for job_number, job in enumerate(jobs):
        try:
            validate_json_job(job)
        except ValidationError as error:
            errors.append("Job#{}: {}".format(job_number, error))
    if errors:
        raise ValidationError('\n'.join(errors))


def validate_json_job(job):
    fields = set(job.keys())
    missing_required = SqlJobDatabase.REQUIRED_FIELDS - fields
    if missing_required:
        raise ValidationError(
            'Missing required fields: {}'.format(', '.join(missing_required)))
    unallowed = fields - SqlJobDatabase.SET_BY_USER
    if unallowed:
        raise ValidationError(
            'These fields do not exist or are for internal use: {}'
            .format(', '.join(unallowed)))
    if not isinstance(job['id'], str):
        raise ValidationError("Expected string in field 'id'")
