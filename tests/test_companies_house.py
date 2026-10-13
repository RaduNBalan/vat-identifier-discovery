
import unittest
from unittest.mock import Mock, patch

import requests

from src.companies_house import get_company_details


class TestCompaniesHouse(unittest.TestCase):

    @patch("src.companies_house.requests.get")
    def test_extracts_company_details(self, mock_get):
        response = Mock()
        response.url = (
            "https://find-and-update.company-information.service.gov.uk/"
            "company/14983527"
        )
        response.text = """
        <html>
            <h1 class="heading-xlarge">"4RENT ESTATES" LTD</h1>
            <strong id="company-number">Company number 14983527</strong>
            <dd id="company-status" class="text data">Active</dd>
        </html>
        """
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = get_company_details("14983527")

        self.assertEqual(result["company_number"], "14983527")
        self.assertEqual(result["company_name"], '"4RENT ESTATES" LTD')
        self.assertEqual(result["company_status"], "Active")
        self.assertEqual(result["source_url"], response.url)

    def test_rejects_invalid_company_number(self):
        with self.assertRaises(ValueError):
            get_company_details("123")

    @patch("src.companies_house.requests.get")
    def test_raises_for_http_error(self, mock_get):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = response

        with self.assertRaises(requests.HTTPError):
            get_company_details("14983527")

    @patch("src.companies_house.requests.get")
    def test_rejects_missing_company_details(self, mock_get):
        response = Mock()
        response.url = (
            "https://find-and-update.company-information.service.gov.uk/"
            "company/14983527"
        )
        response.text = "<html><body>No company details</body></html>"
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        with self.assertRaises(ValueError):
            get_company_details("14983527")


if __name__ == "__main__":
    unittest.main()
