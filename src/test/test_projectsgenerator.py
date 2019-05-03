"""test of qsmrprojects"""
import unittest
import pytest
from datetime import timedelta, date
from projectsgenerator import qsmrprojects


PROJECT_NAME = 'dummyproject'
ODIN_PROJECT = 'dummyodinproject'
PROCESSING_IMAGE_URL = '"docker2.molflow.com/devops/qsmr__:yymmdd"'
CONFIG_FILE = '/tmp/test_qsmr_snapshot_config.conf'


def write_config(cfg):
    with open(CONFIG_FILE, 'w') as out:
        out.write(cfg)


@pytest.mark.system
class TestConfigValidation:
    """test config validation"""
    ARGS = [
        PROJECT_NAME,
        ODIN_PROJECT,
        PROCESSING_IMAGE_URL,
        CONFIG_FILE]

    def test_missing_value(self, microq_service):
        """Test missing config values"""
        write_config((
            'JOB_API_ROOT=http://example.com\n'
            'JOB_API_USERNAME=testuser\n'
            'JOB_API_PASSWORD=\n'))
        assert qsmrprojects.main(self.ARGS) == 1

    def test_ok_config(self, microq_service):
        """Test that ok config validates"""
        write_config((
            'JOB_API_ROOT={}/rest_api\n'.format(microq_service)
            + 'JOB_API_USERNAME=admin\n'
            + 'JOB_API_PASSWORD=sqrrl\n'))
        config = qsmrprojects.load_config(CONFIG_FILE)
        url_project = config['JOB_API_ROOT'] + '/v4/' + PROJECT_NAME
        qsmrprojects.delete_project(url_project, config)
        assert qsmrprojects.main(self.ARGS) == 0

    def test_bad_api_root(self, microq_service):
        """Test bad api root url"""
        write_config((
            'JOB_API_ROOT=http://example.com/\n'
            'JOB_API_USERNAME=testuser\n'
            'JOB_API_PASSWORD=testpw\n'))
        assert qsmrprojects.main(self.ARGS) == 1


@pytest.mark.system
class BaseTestAddProjects:
    """test that project can be cretated"""
    ARGS = [
        PROJECT_NAME,
        ODIN_PROJECT,
        PROCESSING_IMAGE_URL,
        CONFIG_FILE]

    @pytest.fixture(autouse=True)
    def withproject(self):
        write_config(
            'JOB_API_ROOT={}/rest_api\n'.format(microq_service)
            + 'JOB_API_USERNAME=admin\n'
            + 'JOB_API_PASSWORD=sqrrl\n'
        )

    def test_validate_deadline(self):
        """test that deadline must be in the future"""
        past_date = str(date.today() + timedelta(days=-10))
        assert qsmrprojects.validate_deadline(past_date) is False
        future_date = str(date.today() + timedelta(days=10))
        assert qsmrprojects.validate_deadline(future_date) is True

    def test_create_project(self):
        """test that a project can be created"""
        config = qsmrprojects.load_config(CONFIG_FILE)
        url_project = config['JOB_API_ROOT'] + '/v4/' + PROJECT_NAME
        qsmrprojects.delete_project(url_project, config)
        assert qsmrprojects.validate_project_not_exist(url_project) is True
        qsmrprojects.main(self.ARGS)
        assert qsmrprojects.validate_project_not_exist(url_project) is False
        qsmrprojects.delete_project(url_project, config)
