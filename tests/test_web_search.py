import unittest
from unittest.mock import Mock, patch

from src.web_search import decode_bing_url, is_http_url, search_web


class TestWebSearch(unittest.TestCase):

    def test_accepts_direct_http_url(self):
        url = "https://example.com/vat"
        self.assertEqual(decode_bing_url(url), url)

    def test_rejects_bing_redirect_without_target(self):
        self.assertEqual(
            decode_bing_url("https://www.bing.com/ck/a?no_target=1"),
            "",
        )

    def test_rejects_invalid_scheme(self):
        self.assertFalse(is_http_url("javascript:alert(1)"))
        self.assertFalse(is_http_url("file:///etc/passwd"))

    def test_rejects_url_with_credentials(self):
        self.assertFalse(
            is_http_url("https://user:password@example.com/page")
        )

    @patch("src.web_search.requests.post")
    @patch("src.web_search.os.getenv", return_value="test-key")
    def test_search_web_returns_unique_valid_urls(self, mock_env, mock_post):
        response = Mock()
        response.json.return_value = {
            "results": [
                {"url": "https://example.com/vat"},
                {"url": "https://example.com/vat"},
                {"url": "javascript:alert(1)"},
                {"url": "https://example.org/registration"},
            ]
        }
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        results = search_web("example company VAT", max_results=5)

        self.assertEqual(
            results,
            [
                "https://example.com/vat",
                "https://example.org/registration",
            ],
        )
        mock_post.assert_called_once()
        self.assertEqual(
            mock_post.call_args.kwargs["json"]["query"],
            "example company VAT",
        )

    @patch("src.web_search.requests.post")
    @patch("src.web_search.os.getenv", return_value="test-key")
    def test_search_web_returns_empty_list_when_no_results(
        self, mock_env, mock_post
    ):
        response = Mock()
        response.json.return_value = {"results": []}
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        self.assertEqual(search_web("unknown company VAT"), [])
        mock_post.assert_called_once()

    def test_rejects_empty_query(self):
        self.assertEqual(search_web("   "), [])

    def test_rejects_invalid_max_results(self):
        with self.assertRaises(ValueError):
            search_web("company VAT", max_results=0)


if __name__ == "__main__":
    unittest.main()
