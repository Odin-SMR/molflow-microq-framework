"""A simple datamodel implementation"""

from flask import Flask
from uservice.basic_views import BasicView, AuthView
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
