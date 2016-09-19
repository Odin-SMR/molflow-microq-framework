from datetime import timedelta

from flask import request, jsonify

from utils.defs import JOB_STATES, TIME_PERIODS, TIME_PERIOD_TO_DELTA
from uservice.views.basic_views import BasicProjectView


class ProjectStatus(BasicProjectView):
    """Get and create projects"""

    def _get_view(self, version, project):
        """Used to get project status"""
        period = request.args.get('period', TIME_PERIODS.hourly).upper()

        db = self._get_database(project)
        status = {
            'JobStates': db.count_jobs(),
            'Finished%s' % period.title(): db.count_jobs_per_time_period(
                JOB_STATES.finished, time_period=period),
            'Claimed%s' % period.title(): db.count_jobs_per_time_period(
                JOB_STATES.claimed, time_period=period),
            'Failed%s' % period.title(): db.count_jobs_per_time_period(
                JOB_STATES.failed, time_period=period),
            'Workers%s' % period.title(): db.count_jobs_per_time_period(
                JOB_STATES.claimed, time_period=period,
                count_field_name='current_status', distinct=True)
        }
        if not status['Claimed%s' % period.title()]:
            status['ETA'] = None
        else:
            nr_jobs = status['JobStates'].get(JOB_STATES.available, 0)
            claimed_last_complete_period = status[
                'Claimed%s' % period.title()][-2:][0]['count']
            eta_periods = float(nr_jobs)/claimed_last_complete_period
            eta_secs = TIME_PERIOD_TO_DELTA[period].total_seconds()*eta_periods
            status['ETA'] = str(timedelta(seconds=int(eta_secs)))
        return jsonify(Version=version, Project=project, Status=status)

    def _put_view(self, version, project):
        """Used to create project"""
        self._get_database(project)
        return jsonify(Version=version, Project=project)

    def _delete_view(self, version, project):
        """Used to delete project"""
        self._get_database(project).drop()
        return jsonify(Version=version, Project=project)
