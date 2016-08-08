"""A simple datamodel implementation"""

import os
from uservice.core.app import app, user_db


def start_server():
    """Default function"""
    if not os.path.exists('user_db.sqlite'):
        user_db.create_all()

    app.run(
        host='0.0.0.0',
        debug='MOLFLOW_MICRO_QUEUE' not in os.environ,
        threaded=True
        )
