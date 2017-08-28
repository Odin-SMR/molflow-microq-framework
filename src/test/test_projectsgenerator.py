"""test of qsmrprojects"""
import unittest
import pytest
from datetime import timedelta, date
from test.testbase import system
from projectsgenerator import qsmrprojects


PROJECT_NAME = 'dummyproject'
ODIN_PROJECT = 'dummyodinproject'
PROCESSING_IMAGE_URL = '"docker2.molflow.com/devops/qsmr__:yymmdd"'
CONFIG_FILE = '/tmp/test_qsmr_snapshot_config.conf'


class BaseTest(unittest.TestCase):
    """BaseTest"""
    @staticmethod
    def _write_config(cfg):
        with open(CONFIG_FILE, 'w') as out:
            out.write(cfg)


@system
@pytest.mark.usefixtures("dockercompose")
class TestConfigValidation(BaseTest):
    """test config validation"""
    ARGS = [
        PROJECT_NAME,
        ODIN_PROJECT,
        PROCESSING_IMAGE_URL,
        CONFIG_FILE]

    def test_missing_value(self):
        """Test missing config values"""
        self._write_config((
            'JOB_API_ROOT=http://example.com\n'
            'JOB_API_USERNAME=testuser\n'
            'JOB_API_PASSWORD=\n'))
        self.assertEqual(qsmrprojects.main(self.ARGS), 1)

    def test_ok_config(self):
        """Test that ok config validates"""
        self._write_config((
            'JOB_API_ROOT=http://localhost:5000/rest_api\n'
            'JOB_API_USERNAME=admin\n'
            'JOB_API_PASSWORD=sqrrl\n'))
        config = qsmrprojects.load_config(CONFIG_FILE)
        url_project = config['JOB_API_ROOT'] + '/v4/' + PROJECT_NAME
        qsmrprojects.delete_project(url_project, config)
        self.assertEqual(qsmrprojects.main(self.ARGS), 0)

    def test_bad_api_root(self):
        """Test bad api root url"""
        self._write_config((
            'JOB_API_ROOT=http://example.com/\n'
            'JOB_API_USERNAME=testuser\n'
            'JOB_API_PASSWORD=testpw\n'))
        self.assertEqual(qsmrprojects.main(self.ARGS), 1)


@system
@pytest.mark.usefixtures("dockercompose")
class BaseTestAddProjects(BaseTest):
    """test that project can be cretated"""
    ARGS = [
        PROJECT_NAME,
        ODIN_PROJECT,
        PROCESSING_IMAGE_URL,
        CONFIG_FILE]

    def setUp(self):
        self._write_config((
            'JOB_API_ROOT=http://localhost:5000/rest_api\n'
            'JOB_API_USERNAME=admin\n'
            'JOB_API_PASSWORD=sqrrl\n'))

    def test_validate_deadline(self):
        """test that deadline must be in the future"""
        past_date = str(date.today() + timedelta(days=-10))
        self.assertEqual(
            qsmrprojects.validate_deadline(past_date), False)
        future_date = str(date.today() + timedelta(days=10))
        self.assertEqual(
            qsmrprojects.validate_deadline(future_date), True)

    def test_create_project(self):
        """test that a project can be created"""
        config = qsmrprojects.load_config(CONFIG_FILE)
        url_project = config['JOB_API_ROOT'] + '/v4/' + PROJECT_NAME
        qsmrprojects.delete_project(url_project, config)
        self.assertEqual(
            qsmrprojects.validate_project_not_exist(url_project), True)
        qsmrprojects.main(self.ARGS)
        self.assertEqual(
            qsmrprojects.validate_project_not_exist(url_project), False)
        qsmrprojects.delete_project(url_project, config)
