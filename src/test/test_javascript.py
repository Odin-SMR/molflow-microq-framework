"""Integration of JavaScript tests with pytest"""
import subprocess


def test_jasmine():
    """Tests for JavaScript functions using Jasmine

    Requires jasmine-py and PhantomJS to be installed, e.g.:
        $ pip install jasmine
        $ npm install phantomjs
    """
    retval = subprocess.call(["jasmine-ci", "-l", "-b", "phantomjs"])
    assert retval == 0
