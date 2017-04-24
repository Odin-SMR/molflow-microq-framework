from os import environ

from flask import Flask, g, request, abort, jsonify, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

from uservice.core.users import User, auth, db
from uservice.views.basic_views import (
    ListProjects, CountJobs, FetchNextJob, BasicView, FetchJobPrio,
    AnalyzeFailedJobs)
from uservice.views.listjobs import ListJobs
from uservice.views.job_views import JobClaim, JobStatus, JobOutput
from uservice.views.project_views import ProjectStatus
from uservice.views.site_views import (
    JobStatusHumanReadable,
    ListJobsHumanReadable,
    ServerStatusHumanReadable,
    ProjectStatusHumanReadable,
    FailedHumanReadable)


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
            # GET human readable server status
            '/',
            view_func=ServerStatusHumanReadable.as_view('serverstatusshr'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET human readable project status
            '/<project>',
            view_func=ProjectStatusHumanReadable.as_view('projectstatusshr'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET human readable failed jobs analyzation
            '/<project>/failures',
            view_func=FailedHumanReadable.as_view('failedshr'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET human readable list of jobs
            '/<project>/jobs',
            view_func=ListJobsHumanReadable.as_view('listjobshr'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET human readable job status
            '/<project>/jobs/<job_id>',
            view_func=JobStatusHumanReadable.as_view('jobstatushr'),
            methods=["GET"]
            )

        # Rules for worker access:
        self.add_url_rule(
            # GET list of projects
            '/rest_api/<version>/projects',
            view_func=ListProjects.as_view('listprojects'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET job from a project, select project based on prio score
            '/rest_api/<version>/projects/jobs/fetch',
            view_func=FetchJobPrio.as_view('fetchjobprio'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET project info.
            # PUT to create a new project if it does not already exist.
            # DELETE to remove project and all its jobs.
            # TODO: Delete should only be allowed by privileged user.
            '/rest_api/<version>/<project>',
            view_func=ProjectStatus.as_view('projectstatus'),
            methods=["GET", "PUT", "DELETE"]
            )
        self.add_url_rule(
            # GET list of jobs, POST to add new jobs.
            '/rest_api/<version>/<project>/jobs',
            view_func=ListJobs.as_view('listjobs'),
            methods=["GET", "POST"]
            )
        self.add_url_rule(
            # GET processing output analyzation for failed jobs.
            '/rest_api/<version>/<project>/failures',
            view_func=AnalyzeFailedJobs.as_view('listfailed'),
            methods=["GET"]
            )
        self.add_url_rule(
            # Count jobs grouped by a time period and status.
            '/rest_api/<version>/<project>/jobs/count',
            view_func=CountJobs.as_view('countjobs'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET next job URI etc.
            '/rest_api/<version>/<project>/jobs/fetch',
            view_func=FetchNextJob.as_view('fetchnextjob'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET and PUT job status
            '/rest_api/<version>/<project>/jobs/<job_id>/status',
            view_func=JobStatus.as_view('jobstatus'),
            methods=["GET", "PUT"]
            )
        self.add_url_rule(
            # PUT to claim job, GET to get claim status, DELETE to free job
            '/rest_api/<version>/<project>/jobs/<job_id>/claim',
            view_func=JobClaim.as_view('jobclaim'),
            methods=["GET", "PUT", "DELETE"]
            )
        self.add_url_rule(
            # GET and PUT job stdout/stderr output
            '/rest_api/<version>/<project>/jobs/<job_id>/output',
            view_func=JobOutput.as_view('joboutput'),
            methods=["GET", "PUT"]
            )


# initialisation
app = JobServer(__name__)
app.config['SECRET_KEY'] = 'verklig nytta av min hermodskurs i mord'
app.config['SQLALCHEMY_DATABASE_URI'] = environ['USERVICE_DATABASE_URI']
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 30
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 0
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 180
app.config['SQLALCHEMY_POOL_RECYCLE'] = 600


# extensions
db.init_app(app)
DB_INITIALIZED = False


def _add_user(username, password):
    """Try to add user, return None and message if failure and return
    user id and None if success"""
    if not username or not password:
        return None, "Missing username or password"
    # TODO: password policy
    if User.query.filter_by(username=username).first() is not None:
        return None, "User already exist"
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return user.id, None


def _init_db():
    global DB_INITIALIZED
    if DB_INITIALIZED:
        return
    try:
        db.create_all()
        _add_user(environ['USERVICE_ADMIN_USER'],
                  environ['USERVICE_ADMIN_PASSWORD'])
        DB_INITIALIZED = True
    except:
        abort(503)


app.before_request(_init_db)


@app.teardown_appcontext
def close_db(error=None):
    for db in getattr(g, 'job_databases', {}).values():
        db.close()


# error handling
def handle_error(error):
    return make_response(jsonify(error=error.description), error.code)


for cls in HTTPException.__subclasses__():
    app.register_error_handler(cls, handle_error)


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


@app.route('/rest_api/admin/users', methods=['POST'])
@auth.login_required
def new_user():
    if g.user.username != environ['USERVICE_ADMIN_USER']:
        abort(403)
    username = request.json.get('username')
    password = request.json.get('password')
    user_id, msg = _add_user(username, password)
    if not user_id:
        abort(400)
    return (jsonify({'username': username, 'userid': user_id}), 201,
            {'Location': url_for('get_user', id=user_id, _external=True)})


@app.route('/rest_api/admin/users/<int:id>')
@auth.login_required
def get_user(id):
    if g.user.username != environ['USERVICE_ADMIN_USER']:
        abort(403)
    user = User.query.get(id)
    if not user:
        abort(404)
    return jsonify({'username': user.username})


@app.route('/rest_api/admin/users/<int:id>', methods=['DELETE'])
@auth.login_required
def delete_user(id):
    if g.user.username != environ['USERVICE_ADMIN_USER']:
        abort(403)
    user = User.query.get(id)
    if not user:
        abort(404)
    db.session.delete(user)
    db.session.commit()
    return '', 204


@app.route('/rest_api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})
