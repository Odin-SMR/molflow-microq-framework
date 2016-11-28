""" Views that render site pages
"""
from os import environ
from flask import render_template, abort
from flask.views import MethodView

from uservice.database.projects import get_db as get_projects_db


class ListJobsHumanReadable(MethodView):
    """View for listing jobs as html"""
    def get(self, project):
        """GET"""
        data = dict(project=project)
        return render_template('job_list.html', data=data)


class JobStatusHumanReadable(MethodView):
    """Get jobstatus as html"""
    def get(self, project, job_id):
        """GET"""
        data = dict(project=project, job_id=job_id)
        return render_template('job_status.html', data=data)


class ServerStatusHumanReadable(MethodView):
    """Get server as html"""
    def get(self):
        """GET"""
        return render_template(
            'index.html', data=str("USERV_API_PRODUCTION" in environ))


class ProjectStatusHumanReadable(MethodView):
    """Get project status as html"""
    def get(self, project):
        """GET"""
        db = get_projects_db()
        project_data = db.get_project(project)
        if not project_data:
            abort(404)
        data = dict(project=project_data)
        return render_template('project_status.html', data=data)


class FailedHumanReadable(MethodView):
    """Get project status as html"""
    def get(self, project):
        """GET"""
        db = get_projects_db()
        project_data = db.get_project(project)
        if not project_data:
            abort(404)
        data = dict(project=project_data)
        return render_template('failed_jobs.html', data=data)
