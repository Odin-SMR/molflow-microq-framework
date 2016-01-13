""" Views that render site pages
"""
from flask import render_template
from flask.views import MethodView


class ListJobsHumanReadable(MethodView):
    """View for listing jobs as html"""
    def get(self):
        """GET"""
        return render_template('job_list.html')


class JobStatusHumanReadable(MethodView):
    """Get jobstatus as html"""
    def get(self, job_id):
        """GET"""
        return render_template('job_status.html', data=job_id)


class ServerStatusHumanReadable(MethodView):
    """Get jobstatus as html"""
    def get(self):
        """GET"""
        return render_template('index.html')
