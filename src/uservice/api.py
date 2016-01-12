"""A simple datamodel implementation"""

from flask import Flask
from uservice.views.basic_views import (ListJobs, ListJobsHumanReadable,
                                        FetchNextJob)
from uservice.views.job_views import (JobClaim, JobStatus, JobStatusUpdate,
                                      JobStatusHumanReadable, JobLock,
                                      JobUnlock, JobData, JobDeliver)
from os import environ


class JobServer(Flask):
    """The main app running the job server"""
    def __init__(self, name):
        super(JobServer, self).__init__(name)
        self.add_url_rule(
            '/rest_api/<version>/jobs/',
            view_func=ListJobsHumanReadable.as_view('listjobshr')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/list/',
            view_func=ListJobs.as_view('listjobs')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/fetch/',
            view_func=FetchNextJob.as_view('fetchnextjob')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/',
            view_func=JobStatusHumanReadable.as_view('jobstatushr')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/status/',
            view_func=JobStatus.as_view('jobstatus')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/status/update/',
            view_func=JobStatusUpdate.as_view('jobstatusupdate')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/lock/',
            view_func=JobLock.as_view('joblock')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/unlock/',
            view_func=JobUnlock.as_view('jobunlock')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/claim/',
            view_func=JobClaim.as_view('jobclaim')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/data/',
            view_func=JobData.as_view('jobdata')
            )
        self.add_url_rule(
            '/rest_api/<version>/jobs/<job_id>/deliver/',
            view_func=JobDeliver.as_view('jobdeliver')
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
