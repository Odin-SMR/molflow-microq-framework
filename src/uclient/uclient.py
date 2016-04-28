#! /usr/bin/env python
import json
import requests
import argparse as ap


VERBOSE = False


def assert_status(status, expected, name=""):
    if status != expected:
        print "{2} got unexpected status code {0}, expected {1}".format(
            status, expected, name)
    else:
        print "{2} got status code {0} (OK)".format(
            status, expected, name)


def renew_token(uri, credentials):
    """Renew token for token based authorization.

    Might not be necessary.
    """
    pass


def load_credentials(filename="credentials.json"):
    """Load credentials from credentials file.

    Not very secure."""
    with open(filename) as fp:
        credentials = json.load(fp)
    if VERBOSE:
        print "loaded credentials from '{0}'".format(filename)

    return credentials


def get_credentials(args):
    """Get credentials from arguments or file.

    If both file and user has been supplied, use the manually entered user and
    password.
    """
    if args.user is not None:
        return {"user": args.user, "password": args.password}
    elif args.credentials is not None:
        return load_credentials(args.credentials)
    else:
        return -1


def get_job_list(uri):
    """Request list of jobs from server."""
    r = requests.get(uri + "/v4/jobs")
    if VERBOSE:
        print r.text
    return r


def fetch_job(uri):
    """Request an uprocessed job from server."""
    r = requests.get(uri + "/v4/jobs/fetch")
    if VERBOSE:
        print r.text
    return r


def claim_job(uri, credentials, token=None):
    """Claim job from server"""
    r = requests.put(uri, data={"worker1": "hello world!"},
                     auth=(credentials['user'], credentials['password']))
    if VERBOSE:
        print r.text
    return r


def get_data(uri):
    """Get data to work with"""
    r = requests.get(uri)
    if VERBOSE:
        print r.text
    return r


def do_work(data):
    """Do work, or at least pretend to."""
    l2i_prototype = {
        "L2i": {
            "BLineOffset": [range(12)] * 4,
            "ChannelId": [range(639)] * 1,
            "FitsSpectrum": [range(639)] * 1,
            "FreqMode": 0,
            "FreqOffset": 0.0,
            "InvMode": "",
            "LOFreq": [range(12)] * 1,
            "MinLmFactor": 0,
            "PointOffset": 0.0,
            "Residual": 0.0,
            "STW": [range(1)] * 12,
            "ScanId": 0,
        }
    }
    return l2i_prototype


def update_status(status, uri, credentials, token=None):
    """Update status of job."""
    r = requests.post(uri, json=status,
                      headers={'Content-Type': "application/json"},
                      auth=(credentials['user'], credentials['password']))
    if VERBOSE:
        print r.text
    return r


def deliver_job(result, uri, credentials, token=None):
    """Deliver finished job."""
    r = requests.post(uri, json=result,
                      headers={'Content-Type': "application/json"},
                      auth=(credentials['user'], credentials['password']))
    if VERBOSE:
        print r.text
    return r


def main(args):
    r = get_job_list(args.apiroot)
    assert_status(r.status_code, 200, "get_job")

    r = fetch_job(args.apiroot)
    assert_status(r.status_code, 200, "fetch_job")
    job = r

    # The guys below should use different uris:
    credentials = {"user": "snoopy", "password": "ace"}
    r = claim_job(r.json()["Job"]["URLS"]["URL-claim"], credentials)
    assert_status(r.status_code, 401, "claim_job")

    credentials = get_credentials(args)
    if credentials == -1:
        print "no valid credentials! quitting..."
        return -1

    r = claim_job(job.json()["Job"]["URLS"]["URL-claim"], credentials)
    assert_status(r.status_code, 200, "claim_job")

    r = update_status({"Message": "Claimed job."},
                      job.json()["Job"]["URLS"]["URL-status"], credentials)
    assert_status(r.status_code, 200, "update_status")

    r = get_data(job.json()["Job"]["URLS"]["URL-spectra"])
    data = r.json()
    assert_status(r.status_code, 200, "get_data")

    r = update_status({"Message": "Got data."},
                      job.json()["Job"]["URLS"]["URL-status"], credentials)
    assert_status(r.status_code, 200, "update_status")

    result = do_work(data)

    r = update_status({"Message": "Work done."},
                      job.json()["Job"]["URLS"]["URL-status"], credentials)
    assert_status(r.status_code, 200, "update_status")

    r = deliver_job(result, job.json()["Job"]["URLS"]["URL-deliver"],
                    credentials)
    assert_status(r.status_code, 200, "deliver_job")

    r = update_status({"message": "Work delivered."},
                      job.json()["Job"]["URLS"]["URL-status"], credentials)
    assert_status(r.status_code, 200, "update_status")


if __name__ == "__main__":
    parser = ap.ArgumentParser()
    parser.add_argument('-u', "--user", help="user name")
    parser.add_argument('-p', "--password", default="", help="user password")
    parser.add_argument('-c', "--credentials", default="credentials.json",
                        help="credentials file to load")
    parser.add_argument('-a', "--apiroot",
                        default="http://localhost:5000/rest_api",
                        help="URI of the API root")
    parser.add_argument('-v', "--verbose", help="use verbose output",
                        action="store_true")
    args = parser.parse_args()
    VERBOSE = args.verbose
    exit(main(args))
