"""A simple datamodel implementation"""

import os
from uservice.core.app import app


def start_server():
    """Default function"""
    app.run(
        host='0.0.0.0',
        debug='MOLFLOW_MICRO_QUEUE' not in os.environ,
        threaded=True
        )
