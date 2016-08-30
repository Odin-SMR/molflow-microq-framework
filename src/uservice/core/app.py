from flask import Flask, g, request, abort, jsonify, url_for, make_response
from flask.ext.sqlalchemy import SQLAlchemy
from uservice.core.users import get_user_db, auth
from uservice.views.basic_views import (
    ListProjects, ListJobs, FetchNextJob, BasicView)
from uservice.views.job_views import (
    JobClaim, JobStatus, JobInput, JobResult, JobOutput)
from uservice.views.project_views import ProjectStatus
from uservice.views.site_views import (JobStatusHumanReadable,
                                       ListJobsHumanReadable,
                                       ServerStatusHumanReadable,
                                       ProjectStatusHumanReadable)


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
            # GET project info.
            # PUT to create a new project if it does not already exist.
            # DELETE to remove project and all its jobs (dangerous!)?
            '/rest_api/<version>/<project>',
            view_func=ProjectStatus.as_view('projectstatus'),
            methods=["GET", "PUT"]
            )
        self.add_url_rule(
            # GET list of jobs, POST to add new jobs.
            '/rest_api/<version>/<project>/jobs',
            view_func=ListJobs.as_view('listjobs'),
            methods=["GET", "POST"]
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
            # TODO: Remove DELETE?
            '/rest_api/<version>/<project>/jobs/<job_id>/claim',
            view_func=JobClaim.as_view('jobclaim'),
            methods=["GET", "PUT", "DELETE"]
            )
        self.add_url_rule(
            # GET job input data to process (also from fetch).
            '/rest_api/<version>/<project>/jobs/<job_id>/input',
            view_func=JobInput.as_view('jobdata'),
            methods=["GET"]
            )
        self.add_url_rule(
            # GET job result data, PUT to deliver result when done.
            # TODO: Delete to remove results and make it available for
            #       processing again?
            '/rest_api/<version>/<project>/jobs/<job_id>/result',
            view_func=JobResult.as_view('jobresult'),
            methods=["GET", "PUT"]
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True


# extensions
user_db = SQLAlchemy(app)
User = get_user_db(user_db, app)


# error handling
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(401)
def unauthorized(error):
    return make_response(jsonify({'error': 'Unauthorized'}), 401)


@app.errorhandler(403)
def forbidden(error):
    return make_response(jsonify({'error': 'Forbidden'}), 403)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(405)
def method_not_allowed(error):
    return make_response(jsonify({'error': 'Method not allowed'}), 405)


@app.errorhandler(415)
def unsupported_media_type(error):
    return make_response(jsonify({'error': 'Unsupported media type'}), 415)


@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify({'error': 'Internal server error'}), 500)


@app.errorhandler(501)
def not_implemented(error):
    return make_response(jsonify({'error': 'Not implemented'}), 501)


@app.errorhandler(503)
def service_unavailable(error):
    return service_unavailable(jsonify({'error': 'Service unavailable'}), 503)


#@app.errorhandler(507)
#def insufficient_storage(error):
#    return service_unavailable(jsonify({'error': 'Insufficient storage'}), 507)


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


@ app.route('/rest_api/admin/users', methods=['POST'])
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


@app.route('/rest_api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})
