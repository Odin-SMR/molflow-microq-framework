""" Views that render site pages
"""
from flask import render_template
from flask.views import MethodView


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
    """Get jobstatus as html"""
    def get(self):
        """GET"""
        return render_template('index.html')


class ProjectStatusHumanReadable(MethodView):
    """Get project status as html"""
    def get(self, project):
        """GET"""
        data = dict(project=project)
        return render_template('project_status.html', data=data)
