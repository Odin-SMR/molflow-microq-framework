import pytest
from selenium import webdriver


@pytest.mark.system
class TestBrowser:

    @pytest.fixture
    def chrome(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = (
            './node_modules/chromium/lib/chromium/chrome-linux/chrome'
        )
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(
            './node_modules/chromedriver/bin/chromedriver',
            options=chrome_options
        )
        driver.implicitly_wait(4)
        yield driver

    def test_main_page_is_up(self, microq_service, chrome):
        """Test that main page is up"""
        chrome.get(microq_service)
        assert "Service" in chrome.title
