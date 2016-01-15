"""A simple datamodel implementation"""

import os
from core.app import app, db


def start_server():
    """Default function"""
    if not os.path.exists('db.sqlite'):
        db.create_all()

    app.run(
        host='0.0.0.0',
        debug='MOLFLOW_MICRO_QUEUE' not in os.environ,
        threaded=True
        )
