"""A simple datamodel implementation"""

from flask import Flask
from uservice.views.basic_views import BasicView, AuthView
from uservice.views.job_views import (JobClaim, JobStatus,
                                      JobStatusHumanReadable,)
from os import environ


class JobServer(Flask):
    """The main app running the job server"""
    def __init__(self, name):
        super(JobServer, self).__init__(name)
        self.add_url_rule(
            '/rest_api/<version>/jobs/',
            view_func=BasicView.as_view('basicview')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/authtest/',
            view_func=AuthView.as_view('authview')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/',
            view_func=JobStatus.as_view('jobstatus')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/status/',
            view_func=JobStatusHumanReadable.as_view('jobstatushr')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/claim/',
            view_func=JobClaim.as_view('jobclaim')
            )


def main():
    """Default function"""
    app = JobServer(__name__)
    app.run(
        host='0.0.0.0',
        debug='MOLFLOW_MICRO_QUEUE' not in environ,
        threaded=True
        )

if __name__ == "__main__":
    main()
