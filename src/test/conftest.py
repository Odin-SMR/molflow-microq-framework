import pytest

from .testbase import ApiSession


@pytest.fixture(scope='function')
def api(microq_service):
    apisession = ApiSession(microq_service)
    yield apisession
    apisession.cleanup()
