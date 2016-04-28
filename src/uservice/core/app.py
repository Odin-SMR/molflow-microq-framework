from flask import Flask, g, request, abort, jsonify, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from ..core.users import get_user_db, auth
from ..views.basic_views import ListJobs, FetchNextJob, BasicView
from ..views.job_views import JobClaim, JobStatus, JobData
from ..views.site_views import (JobStatusHumanReadable,
                                ListJobsHumanReadable,
                                ServerStatusHumanReadable)


class JobServer(Flask):
    """The main app running the job server"""
    def __init__(self, name):
        super(JobServer, self).__init__(name)

        # Debug views:
        self.add_url_rule(
            # Debug GET, PUT, DELETE authorization
            '/rest_api/<version>/auth',
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
            '/jobs',
            view_func=ListJobsHumanReadable.as_view('listjobshr'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET human readable job status
            '/jobs/<job_id>',
            view_func=JobStatusHumanReadable.as_view('jobstatushr'),
            methods=["GET"]
            )

        # Rules for worker access:
        self.add_url_rule(
            # GET list of jobs
            '/rest_api/<version>/jobs',
            view_func=ListJobs.as_view('listjobs'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET next job URI etc.
            '/rest_api/<version>/jobs/fetch',
            view_func=FetchNextJob.as_view('fetchnextjob'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET and POST job status
            '/rest_api/<version>/jobs/<job_id>',
            view_func=JobStatus.as_view('jobstatus'),
            methods=["GET", "POST"]
            )
        self.add_url_rule(
            # PUT to claim job, GET to get claim status, DELETE to free job
            '/rest_api/<version>/jobs/<job_id>/claim',
            view_func=JobClaim.as_view('jobclaim'),
            methods=["GET", "PUT", "DELETE"]
            )
        self.add_url_rule(
            # GET to get data to process, POST to deliver when done.
            '/rest_api/<version>/jobs/<job_id>/data',
            view_func=JobData.as_view('jobdata'),
            methods=["GET", "POST"]
            )


# initialisation
app = JobServer(__name__)
app.config['SECRET_KEY'] = 'verklig nytta av min hermodskurs i mord'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True


# extensions
user_db = SQLAlchemy(app)
User = get_user_db(user_db, app)


# user admininstration and authentication
@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@ app.route('/rest_api/admin/users/', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    user_db.session.add(user)
    user_db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/rest_api/admin/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/rest_api/admin/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})
