import unittest
from unittest.mock import Mock, patch

from src.hmrc_client import (
    HMRCAPIError,
    HMRCConfigurationError,
    verify_vat_number,
)


class TestHMRCClient(unittest.TestCase):

    @patch.dict("os.environ", {}, clear=True)
    def test_requires_credentials(self):
        with self.assertRaises(HMRCConfigurationError):
            verify_vat_number("123456789")

    @patch.dict(
        "os.environ",
        {
            "HMRC_CLIENT_ID": "test-client",
            "HMRC_CLIENT_SECRET": "test-secret",
            "HMRC_BASE_URL": "https://test-api.service.hmrc.gov.uk",
        },
    )
    @patch("src.hmrc_client.requests.get")
    @patch("src.hmrc_client.requests.post")
    def test_registered_vat(self, mock_post, mock_get):
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test-token"
        }
        mock_post.return_value = token_response

        vat_response = Mock()
        vat_response.status_code = 200
        vat_response.json.return_value = {
            "target": {
                "name": "EXAMPLE LTD",
                "vatNumber": "123456789",
                "address": {},
            }
        }
        mock_get.return_value = vat_response

        result = verify_vat_number("GB123456789")

        self.assertTrue(result["verified"])
        self.assertEqual(result["status"], "REGISTERED")
        self.assertEqual(result["vat_number"], "GB123456789")
        mock_post.assert_called_once()
        mock_get.assert_called_once()

        headers = mock_get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer test-token")
        self.assertEqual(
            headers["Accept"],
            "application/vnd.hmrc.2.0+json",
        )

    @patch.dict(
        "os.environ",
        {
            "HMRC_CLIENT_ID": "test-client",
            "HMRC_CLIENT_SECRET": "test-secret",
        },
    )
    @patch("src.hmrc_client.requests.get")
    @patch("src.hmrc_client.requests.post")
    def test_vat_not_found(self, mock_post, mock_get):
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test-token"
        }
        mock_post.return_value = token_response

        vat_response = Mock()
        vat_response.status_code = 404
        mock_get.return_value = vat_response

        result = verify_vat_number("123456789")

        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "NOT_FOUND")
        self.assertIsNone(result["details"])

    @patch.dict(
        "os.environ",
        {
            "HMRC_CLIENT_ID": "test-client",
            "HMRC_CLIENT_SECRET": "test-secret",
        },
    )
    @patch("src.hmrc_client.requests.get")
    @patch("src.hmrc_client.requests.post")
    def test_http_error_is_not_treated_as_not_found(
        self, mock_post, mock_get
    ):
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test-token"
        }
        mock_post.return_value = token_response

        vat_response = Mock()
        vat_response.status_code = 500
        mock_get.return_value = vat_response

        with self.assertRaises(HMRCAPIError):
            verify_vat_number("123456789")

    @patch.dict(
        "os.environ",
        {
            "HMRC_CLIENT_ID": "test-client",
            "HMRC_CLIENT_SECRET": "test-secret",
        },
    )
    def test_rejects_invalid_vat_format(self):
        with self.assertRaises(ValueError):
            verify_vat_number("ABC123")

    @patch.dict(
        "os.environ",
        {
            "HMRC_CLIENT_ID": "test-client",
            "HMRC_CLIENT_SECRET": "test-secret",
        },
    )
    @patch("src.hmrc_client.requests.get")
    @patch("src.hmrc_client.requests.post")
    def test_oauth_failure_raises_error(self, mock_post, mock_get):
        token_response = Mock()
        token_response.status_code = 401
        mock_post.return_value = token_response

        with self.assertRaises(HMRCAPIError):
            verify_vat_number("123456789")

        mock_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
