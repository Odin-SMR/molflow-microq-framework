import pytest
from selenium import webdriver


@pytest.mark.system
class TestBrowser:

    @pytest.fixture
    def chrome(self):
        driver = webdriver.Chrome()
        yield driver
        driver.quit()

    def test_main_page_is_up(self, microq_service, chrome):
        """Test that main page is up"""
        chrome.get(microq_service)
        assert "Service" in chrome.title
