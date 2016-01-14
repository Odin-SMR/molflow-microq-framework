from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from users import get_user_db
from uservice.views.basic_views import ListJobs, FetchNextJob, BasicView
from uservice.views.job_views import JobClaim, JobStatus, JobData, JobLock
from uservice.views.site_views import (JobStatusHumanReadable,
                                       ListJobsHumanReadable,
                                       ServerStatusHumanReadable)


class JobServer(Flask):
    """The main app running the job server"""
    def __init__(self, name):
        super(JobServer, self).__init__(name)

        # Debug views:
        self.add_url_rule(
            # Debug GET, PUT, DELETE authorization
            '/rest_api/<version>/auth/',
            view_func=BasicView.as_view('authdebug'),
            methods=["GET", "PUT", "DELETE"]
            )

        # Rules for human readables:
        self.add_url_rule(
            # GET human readable list of jobs
            '/',
            view_func=ServerStatusHumanReadable.as_view('serverstatusshr'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET human readable list of jobs
            '/jobs/',
            view_func=ListJobsHumanReadable.as_view('listjobshr'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET human readable job status
            '/jobs/<job_id>/',
            view_func=JobStatusHumanReadable.as_view('jobstatushr'),
            methods=["GET"]
            )

        # Rules for worker access:
        self.add_url_rule(
            # GET list of jobs
            '/rest_api/<version>/jobs/',
            view_func=ListJobs.as_view('listjobs'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET next job URI etc.
            '/rest_api/<version>/jobs/fetch/',
            view_func=FetchNextJob.as_view('fetchnextjob'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET and PUT job status
            '/rest_api/<version>/jobs/<job_id>/',
            view_func=JobStatus.as_view('jobstatus'),
            methods=["GET", "PUT"]
            )
        self.add_url_rule(
            # GET lock status, PUT lock in place, and DELETE lock
            '/rest_api/<version>/jobs/<job_id>/lock/',
            view_func=JobLock.as_view('joblock'),
            methods=["GET", "PUT", "DELETE"]
            )
        self.add_url_rule(
            # PUT to claim job
            '/rest_api/<version>/jobs/<job_id>/claim/',
            view_func=JobClaim.as_view('jobclaim'),
            methods=["GET", "PUT"]
            )
        self.add_url_rule(
            # GET to get data to process, PUT to deliver when done.
            '/rest_api/<version>/jobs/<job_id>/data/',
            view_func=JobData.as_view('jobdata'),
            methods=["GET", "PUT"]
            )


# initialisation
app = JobServer(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True


# extensions
db = SQLAlchemy(app)
Users = get_user_db(db, app)
