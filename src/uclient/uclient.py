import json
import argparse as ap


def load_credentials(filename="credentials.json"):
    """Load credentials from credentials file.

    Not very secure."""
    with open(filename) as fp:
        credentials = json.load(fp)

    return credentials


def get_credentials(args):
    """Get credentials from arguments or file.

    If both file and user has been supplied, use the manually entered user and
    password.
    """
    if args.user != "":
        return {"user": args.user, "password": args.password}
    elif args.credentials != "":
        return load_credentials(args.credentials)
    else:
        return -1


def get_job_list(url):
    """Request list of jobs from server."""
    pass


def fetch_job(uri):
    """Request an uprocessed job from server."""
    pass


def claim_job(uri, credentials, token=None):
    """Claim job from server"""
    pass


def get_data(uri):
    """Get data to work with"""
    pass


def do_work(data):
    """Do work, or at least pretend to."""
    pass


def update_status(status, uri, credentials, token=None):
    """Update status of job."""
    pass


def renew_token(uri, credentials):
    """Renew token for token based authorization.

    Might not be necessary.
    """
    pass


def deliver_job(result, uri, credentials, token=None):
    """Deliver finished job."""
    pass


def main(args):
    get_job_list(args.uri)
    fetch_job(args.uri + "fetch/")
    credentials = get_credentials(args)
    if credentials == -1:
        return -1

    # The guys below should use different uris:
    claim_job(args.uri, credentials)
    update_status({"Message": "Claimed job."}, args.uri, credentials)
    data = get_data(args.uri)
    update_status({"Message": "Got data."}, args.uri, credentials)
    result = do_work(data)
    update_status({"Message": "Work done."}, args.uri, credentials)
    deliver_job(result, args.uri, credentials)


if __name__ == "__main__":
    parser = ap.ArgumentParser()
    args = parser.parse_args()
    exit(main(args))
