import urllib
from datetime import timedelta
from collections import defaultdict
from operator import itemgetter

from flask import request, jsonify, g

from utils.defs import JOB_STATES, TIME_PERIODS, TIME_PERIOD_TO_DELTA
from uservice.views.basic_views import BasicProjectView


class ProjectStatus(BasicProjectView):
    """Get and create projects"""

    def _get_view(self, version, project):
        """Used to get project status"""
        period = request.args.get('period', TIME_PERIODS.hourly).upper()

        db = self._get_jobs_database(project)

        def add_state_count(job_state, counts):
            state_counts = db.count_jobs_per_time_period(
                job_state, time_period=period)
            for state_count in state_counts:
                count = counts[state_count['period']]
                count['Period'] = state_count['period']
                count['Jobs%s' % job_state.title()] = state_count['count']
                param = [('status', job_state),
                         ('start', state_count['start_time'].isoformat()),
                         ('end', state_count['end_time'].isoformat())]
                count['URLS']['URL-Jobs%s' % job_state.title()] = (
                    '{}rest_api/v4/{}/jobs?{}'.format(
                        request.url_root, project, urllib.urlencode(param)))

        def add_workers_count(counts):
            worker_counts = db.count_jobs_per_time_period(
                JOB_STATES.claimed, time_period=period,
                count_field_name='current_status', distinct=True)
            for worker_count in worker_counts:
                count = counts[worker_count['period']]
                count['Period'] = worker_count['period']
                count['ActiveWorkers'] = worker_count['count']
                param = [('start', worker_count['start_time'].isoformat()),
                         ('end', worker_count['end_time'].isoformat())]
                count['URLS']['URL-ActiveWorkers'] = (
                    '{}rest_api/v4/{}/workers?{}'.format(
                        request.url_root, project, urllib.urlencode(param)))

        def get_default_count():
            return {'Period': None, 'JobsClaimed': 0, 'JobsFailed': 0,
                    'JobsFinished': 0, 'URLS': {}}

        counts = defaultdict(get_default_count)
        add_state_count(JOB_STATES.claimed, counts)
        add_state_count(JOB_STATES.failed, counts)
        add_state_count(JOB_STATES.finished, counts)
        add_workers_count(counts)

        status = {
            'JobStates': db.count_jobs(),
            '%sCount' % period.title(): sorted(counts.values(),
                                               key=itemgetter('Period')),
        }
        if not counts:
            status['ETA'] = None
        else:
            nr_jobs = status['JobStates'].get(JOB_STATES.available, 0)
            claimed_last_complete_period = status[
                '%sCount' % period.title()][-2:][0]['JobsClaimed']
            eta_periods = float(nr_jobs)/claimed_last_complete_period
            eta_secs = TIME_PERIOD_TO_DELTA[period].total_seconds()*eta_periods
            status['ETA'] = str(timedelta(seconds=int(eta_secs)))
        return jsonify(Version=version, Project=project, Status=status)

    def _put_view(self, version, project):
        """Used to create project"""
        db = self._get_projects_database()
        if db.project_exists(project):
            return jsonify(Version=version, Project=project)
        db.insert_project(project, g.user.username)
        self._get_jobs_database(project)
        return jsonify(Version=version, Project=project), 201

    def _delete_view(self, version, project):
        """Used to delete project"""
        db = self._get_projects_database()
        db.remove_project(project)
        self._get_jobs_database(project).drop()
        return jsonify(Version=version, Project=project)
