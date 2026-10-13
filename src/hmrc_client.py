
"""Client for the HMRC Check a UK VAT number API."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://test-api.service.hmrc.gov.uk"
REQUEST_TIMEOUT = 20


class HMRCConfigurationError(RuntimeError):
    """Missing HMRC configuration."""


class HMRCAPIError(RuntimeError):
    """HMRC API request failed."""


def _get_access_token(client_id, client_secret, base_url):
    url = f"{base_url}/oauth/token"

    try:
        response = requests.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "read:vat",
            },
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as error:
        raise HMRCAPIError("HMRC OAuth token request failed.") from error

    if response.status_code != 200:
        raise HMRCAPIError(
            f"HMRC OAuth returned HTTP {response.status_code}."
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise HMRCAPIError("HMRC OAuth returned invalid JSON.") from error

    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise HMRCAPIError("HMRC OAuth response has no access token.")

    return token


def verify_vat_number(vat_number):
    client_id = os.getenv("HMRC_CLIENT_ID", "").strip()
    client_secret = os.getenv("HMRC_CLIENT_SECRET", "").strip()
    base_url = os.getenv("HMRC_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")

    if not client_id or not client_secret:
        raise HMRCConfigurationError(
            "HMRC_CLIENT_ID and HMRC_CLIENT_SECRET must be configured."
        )

    if not isinstance(vat_number, str) or not vat_number.strip():
        raise ValueError("vat_number must be a non-empty string.")

    normalized_vat = vat_number.strip().upper().replace(" ", "")
    if normalized_vat.startswith("GB"):
        normalized_vat = normalized_vat[2:]

    if len(normalized_vat) not in (9, 12) or not normalized_vat.isdigit():
        raise ValueError("A UK VAT number must contain 9 or 12 digits.")

    token = _get_access_token(client_id, client_secret, base_url)
    url = (
        f"{base_url}/organisations/vat/check-vat-number/"
        f"lookup/{normalized_vat}"
    )

    try:
        response = requests.get(
            url,
            headers={
                "Accept": "application/vnd.hmrc.2.0+json",
                "Authorization": f"Bearer {token}",
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as error:
        raise HMRCAPIError("HMRC VAT lookup request failed.") from error

    if response.status_code == 404:
        return {
            "verified": False,
            "vat_number": f"GB{normalized_vat}",
            "status": "NOT_FOUND",
            "details": None,
        }

    if response.status_code != 200:
        raise HMRCAPIError(
            f"HMRC VAT lookup returned HTTP {response.status_code}."
        )

    try:
        details = response.json()
    except ValueError as error:
        raise HMRCAPIError("HMRC VAT lookup returned invalid JSON.") from error

    return {
        "verified": True,
        "vat_number": f"GB{normalized_vat}",
        "status": "REGISTERED",
        "details": details,
    }