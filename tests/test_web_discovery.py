import unittest
from unittest.mock import Mock, patch

import requests

from src.web_discovery import get_page_text, discover_vat_from_page


class TestWebDiscovery(unittest.TestCase):

    @patch("src.web_discovery.requests.get")
    def test_extracts_visible_text_and_metadata(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.url = "https://example.com/legal"
        response.encoding = "utf-8"
        response.headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": "100",
        }
        response.iter_content.return_value = [
            b"<html><body><p>VAT GB123456789</p>"
            b"<script>hidden text</script></body></html>"
        ]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        mock_get.return_value = response

        text, metadata = get_page_text("https://example.com")

        self.assertIn("VAT GB123456789", text)
        self.assertNotIn("hidden text", text)
        self.assertEqual(metadata["source_url"], "https://example.com")
        self.assertEqual(
            metadata["final_url"],
            "https://example.com/legal",
        )
        self.assertEqual(metadata["http_status"], 200)

    @patch("src.web_discovery.requests.get")
    def test_rejects_non_html_content(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.headers = {"Content-Type": "application/pdf"}
        response.raise_for_status.return_value = None
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        mock_get.return_value = response

        with self.assertRaisesRegex(ValueError, "Unsupported content type"):
            get_page_text("https://example.com/document")

    @patch("src.web_discovery.requests.get")
    def test_http_errors_propagate(self, mock_get):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("404")
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        mock_get.return_value = response

        with self.assertRaises(requests.HTTPError):
            get_page_text("https://example.com/missing")

    def test_rejects_invalid_scheme(self):
        with self.assertRaises(ValueError):
            get_page_text("file:///C:/Windows/win.ini")

    @patch("src.web_discovery.validate_public_url")
    @patch("src.web_discovery.requests.get")
    def test_follows_redirect_manually(self, mock_get, mock_validate):
        first_response = Mock()
        first_response.status_code = 302
        first_response.headers = {
            "Location": "https://example.com/final"
        }

        final_response = Mock()
        final_response.status_code = 200
        final_response.url = "https://example.com/final"
        final_response.encoding = "utf-8"
        final_response.headers = {"Content-Type": "text/html"}
        final_response.iter_content.return_value = [
            b"<html><body>VAT GB123456789</body></html>"
        ]

        mock_get.side_effect = [first_response, final_response]
        mock_validate.side_effect = lambda url: url

        text, metadata = get_page_text("https://example.com/start")

        self.assertIn("VAT GB123456789", text)
        self.assertEqual(
            metadata["final_url"],
            "https://example.com/final",
        )
        self.assertEqual(mock_get.call_count, 2)

        for call in mock_get.call_args_list:
            self.assertFalse(call.kwargs["allow_redirects"])

    @patch("src.web_discovery.validate_public_url")
    @patch("src.web_discovery.requests.get")
    def test_rejects_redirect_to_private_url(self, mock_get, mock_validate):
        response = Mock()
        response.status_code = 302
        response.headers = {"Location": "http://127.0.0.1/admin"}

        def validate(url):
            if "127.0.0.1" in url:
                raise ValueError("Private or non-public IP addresses are not allowed")
            return url

        mock_validate.side_effect = validate
        mock_get.return_value = response

        with self.assertRaisesRegex(ValueError, "Private or non-public"):
            get_page_text("https://example.com/start")

        self.assertEqual(mock_get.call_count, 1)
        response.close.assert_called_once()

    @patch("src.web_discovery.validate_public_url")
    @patch("src.web_discovery.requests.get")
    def test_stops_after_maximum_redirects(self, mock_get, mock_validate):
        response = Mock()
        response.status_code = 302
        response.headers = {"Location": "/next"}

        mock_get.return_value = response
        mock_validate.side_effect = lambda url: url

        with self.assertRaisesRegex(ValueError, "Maximum number of redirects"):
            get_page_text("https://example.com/start")

        self.assertEqual(mock_get.call_count, 6)


    @patch("src.web_discovery.get_page_text")
    def test_rejects_page_that_does_not_mention_company(self, mock_get_page):
        mock_get_page.return_value = (
            "Unrelated page with VAT GB123456789",
            {
                "source_url": "https://example.com",
                "final_url": "https://example.com",
                "http_status": 200,
                "content_type": "text/html",
            },
        )

        results = discover_vat_from_page(
            "https://example.com",
            company_name="4RENT ESTATES LTD",
        )

        self.assertEqual(results, [])

    @patch("src.web_discovery.get_page_text")
    def test_extracts_candidates_when_company_is_mentioned(self, mock_get_page):
        mock_get_page.return_value = (
            "4RENT ESTATES LTD VAT number GB123456789",
            {
                "source_url": "https://example.com",
                "final_url": "https://example.com",
                "http_status": 200,
                "content_type": "text/html",
            },
        )

        results = discover_vat_from_page(
            "https://example.com",
            company_name="4RENT ESTATES LTD",
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["vat_number"], "GB123456789")


    @patch("src.web_discovery.get_page_text")
    def test_company_number_match_is_recorded(self, mock_get_page):
        mock_get_page.return_value = (
            "4RENT ESTATES LTD Company number 14983527 VAT GB123456789",
            {
                "source_url": "https://example.com",
                "final_url": "https://example.com",
                "http_status": 200,
                "content_type": "text/html",
            },
        )

        results = discover_vat_from_page(
            "https://example.com",
            company_name="4RENT ESTATES LTD",
            company_number="14983527",
        )

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["company_number_match"])


if __name__ == "__main__":
    unittest.main()
