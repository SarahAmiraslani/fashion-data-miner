import unittest
from unittest.mock import patch
from scrapping_utility import get_user_agent, prep_driver, get_metadata


class TestScrappingUtility(unittest.TestCase):
    @patch("scrapping_utility.UserAgent")
    def test_get_user_agent(self, mock_UserAgent):
        # Set up the mock
        mock_UserAgent.return_value.random.return_value = "Test User Agent"

        # Call the function
        result = get_user_agent()

        # Check the result
        self.assertEqual(result, "Test User Agent")

    @patch("scrapping_utility.webdriver.ChromeOptions")
    def test_prep_driver(self, mock_ChromeOptions):
        # Set up the mock
        mock_options = mock_ChromeOptions.return_value

        # Call the function
        result = prep_driver("Test User Agent")

        # Check the result
        self.assertEqual(result, mock_options)
        mock_options.add_argument.assert_called()

    @patch("scrapping_utility.requests.get")
    @patch("scrapping_utility.get_base_url")
    @patch("scrapping_utility.extruct.extract")
    def test_get_metadata(self, mock_extract, mock_get_base_url, mock_get):
        # Set up the mocks
        mock_get.return_value.text = "Test HTML"
        mock_get.return_value.url = "Test URL"
        mock_get_base_url.return_value = "Test Base URL"
        mock_extract.return_value = {"metadata": "Test Metadata"}

        # Call the function
        result = get_metadata("Test URL")

        # Check the result
        self.assertEqual(result, {"metadata": "Test Metadata"})


if __name__ == "__main__":
    unittest.main()
