from datetime import datetime, timedelta

from dateutil.parser import parse as parse_datetime

from flask import request, jsonify, g

from utils.defs import JOB_STATES, TIME_PERIODS, TIME_PERIOD_TO_DELTA
from uservice.views.basic_views import BasicProjectView, abort


class ProjectStatus(BasicProjectView):
    """Get and create projects"""

    def _get_view(self, version, project):
        """Used to get project status"""
        now = request.args.get('now')
        if now:
            try:
                now = parse_datetime(now)
            except ValueError:
                return abort(400, 'Bad time format: %r' % now)
        else:
            now = datetime.utcnow()

        db = self._get_jobs_database(project)
        status = {state.title(): count
                  for state, count in db.count_jobs().items()}

        nr_jobs_todo = status.get(JOB_STATES.available.title(), 0)
        if not nr_jobs_todo:
            ETA = str(timedelta(seconds=0))
        else:
            end = datetime(*now.timetuple()[:4])
            start = end - timedelta(hours=1)
            last_hour_count = db.count_jobs_per_time_period(
                JOB_STATES.claimed, time_period=TIME_PERIODS.hourly,
                start_time=start, end_time=end)
            if not last_hour_count:
                # No jobb claimed the last hour, assume that no workers
                # are active.
                ETA = None
            else:
                claimed_last_hour = last_hour_count[0]['count']
                eta_periods = float(nr_jobs_todo)/claimed_last_hour
                eta_secs = TIME_PERIOD_TO_DELTA[
                    TIME_PERIODS.hourly].total_seconds()*eta_periods
                ETA = str(timedelta(seconds=int(eta_secs)))

        urls = {
            'URL-DailyCount': (
                '{}rest_api/v4/{}/jobs/count?period=daily').format(
                    request.url_root, project),
            'URL-Jobs': '{}rest_api/v4/{}/jobs'.format(
                request.url_root, project),
            'URL-Workers': '{}rest_api/v4/{}/workers'.format(
                request.url_root, project)
        }
        return jsonify(Version=version, Project=project, JobStates=status,
                       ETA=ETA, URLS=urls)

    def _put_view(self, version, project):
        """Used to create and update project"""
        data = request.json or {}
        if 'deadline' in data:
            data['deadline'] = parse_datetime(
                data.pop('deadline'))
        db = self._get_projects_database()
        unallowed = set(data.keys()) - db.UPDATED_BY_USER
        if unallowed:
            return abort(
                400, 'Cannot update these fields: %r' % list(unallowed))
        if not db.project_exists(project):
            db.insert_project(project, g.user.username, **data)
            self._get_jobs_database(project)
            return jsonify(Version=version, ID=project), 201
        else:
            db.update_project(project, **data)
            return jsonify(Version=version, ID=project), 204

    def _delete_view(self, version, project):
        """Used to delete project"""
        db = self._get_projects_database()
        db.remove_project(project)
        self._get_jobs_database(project).drop()
        return jsonify(Version=version, Project=project)
