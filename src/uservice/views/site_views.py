""" Views that render site pages
"""
from os import environ
from flask import render_template, abort
from flask.views import MethodView

from uservice.database.projects import get_db as get_projects_db


def get_template_data(**kwargs):
    if "USERV_API_PRODUCTION" not in environ:
        kwargs['DEBUG'] = True
    return kwargs


class ListJobsHumanReadable(MethodView):
    """View for listing jobs as html"""
    def get(self, project):
        """GET"""
        data = get_template_data(project=project)
        return render_template('job_list.html', data=data)


class JobStatusHumanReadable(MethodView):
    """Get jobstatus as html"""
    def get(self, project, job_id):
        """GET"""
        data = get_template_data(project=project, job_id=job_id)
        return render_template('job_status.html', data=data)


class ServerStatusHumanReadable(MethodView):
    """Get server as html"""
    def get(self):
        """GET"""
        return render_template(
            'index.html', data=get_template_data())


class ProjectStatusHumanReadable(MethodView):
    """Get project status as html"""
    def get(self, project):
        """GET"""
        db = get_projects_db()
        project_data = db.get_project(project)
        if not project_data:
            abort(404)
        data = get_template_data(project=project_data)
        return render_template('project_status.html', data=data)


class FailedHumanReadable(MethodView):
    """Get project status as html"""
    def get(self, project):
        """GET"""
        db = get_projects_db()
        project_data = db.get_project(project)
        if not project_data:
            abort(404)
        data = get_template_data(project=project_data)
        return render_template('failed_jobs.html', data=data)
