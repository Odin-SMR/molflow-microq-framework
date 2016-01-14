"""A simple datamodel implementation"""

from os import environ
from core.app import app


def main():
    """Default function"""

    app.run(
        host='0.0.0.0',
        debug='MOLFLOW_MICRO_QUEUE' not in environ,
        threaded=True
        )

if __name__ == "__main__":
    main()
