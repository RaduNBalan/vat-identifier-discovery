import re
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from .vat_extractor import extract_vat_numbers
except ImportError:
    from vat_extractor import extract_vat_numbers

USER_AGENT = (
    "VATIdentifierDiscovery/1.0 "
    "(research prototype; contact: project-maintainer)"
)

REQUEST_TIMEOUT = 15
MAX_PAGE_BYTES = 2_000_000
MAX_REDIRECTS = 5

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}

ALLOWED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
}
def validate_public_url(url):
    """Reject URLs that resolve to non-public IP addresses."""
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are allowed")

    if not parsed.hostname:
        raise ValueError("URL must contain a hostname")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed")

    hostname = parsed.hostname

    try:
        addresses = {ipaddress.ip_address(hostname)}
    except ValueError:
        try:
            addresses = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(
                    hostname,
                    parsed.port or (443 if parsed.scheme == "https" else 80),
                    type=socket.SOCK_STREAM,
                )
            }
        except (OSError, ValueError) as error:
            raise ValueError("Could not resolve public hostname") from error

    if not addresses:
        raise ValueError("Hostname did not resolve to an IP address")

    for address in addresses:
        if not address.is_global:
            raise ValueError("Private or non-public IP addresses are not allowed")

    return url


def get_page_text(url):
    """
    Download a public HTML page, validate each redirect,
    and return visible text with retrieval metadata.
    """
    current_url = validate_public_url(url)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }

    response = None

    try:
        for redirect_count in range(MAX_REDIRECTS + 1):
            response = requests.get(
                current_url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                stream=True,
                allow_redirects=False,
            )

            if response.status_code in REDIRECT_STATUS_CODES:
                location = response.headers.get("Location")

                if not location:
                    raise ValueError(
                        "Redirect response does not contain a Location header"
                    )

                if redirect_count >= MAX_REDIRECTS:
                    raise ValueError("Maximum number of redirects exceeded")

                next_url = urljoin(current_url, location)
                validate_public_url(next_url)

                response.close()
                response = None
                current_url = next_url
                continue

            response.raise_for_status()

            content_type = (
                response.headers.get("Content-Type", "")
                .split(";")[0]
                .strip()
                .lower()
            )

            if content_type not in ALLOWED_CONTENT_TYPES:
                raise ValueError(
                    f"Unsupported content type: "
                    f"{content_type or 'unknown'}"
                )

            content_length = response.headers.get("Content-Length")

            if content_length:
                try:
                    declared_size = int(content_length)
                except ValueError:
                    declared_size = None

                if declared_size is not None and declared_size > MAX_PAGE_BYTES:
                    raise ValueError("Page exceeds the 2 MB size limit")

            chunks = []
            total_bytes = 0

            for chunk in response.iter_content(chunk_size=16_384):
                if not chunk:
                    continue

                total_bytes += len(chunk)

                if total_bytes > MAX_PAGE_BYTES:
                    raise ValueError("Page exceeds the 2 MB size limit")

                chunks.append(chunk)

            encoding = response.encoding or "utf-8"
            html = b"".join(chunks).decode(encoding, errors="replace")
            final_url = response.url
            status_code = response.status_code

            break
        else:
            raise ValueError("Maximum number of redirects exceeded")

    finally:
        if response is not None:
            response.close()

    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        ["script", "style", "noscript", "svg", "template"]
    ):
        element.decompose()

    text = soup.get_text(separator=" ", strip=True)

    metadata = {
        "source_url": url,
        "final_url": final_url,
        "http_status": status_code,
        "content_type": content_type,
    }

    return text, metadata

def normalize_company_name(value):
    """Normalize a company name for a preliminary relevance check."""
    value = (value or "").upper()
    value = re.sub(r"\bLIMITED\b|\bLTD\b", "", value)
    return re.sub(r"[^A-Z0-9]", "", value)


def page_mentions_company(text, company_name):
    """Check whether visible page text mentions the expected company."""
    normalized_name = normalize_company_name(company_name)
    normalized_text = normalize_company_name(text)

    if len(normalized_name) < 4:
        return False

    return normalized_name in normalized_text

def page_mentions_company_number(text, company_number):
    """Check for an exact Companies House number in page text."""
    if not company_number:
        return False

    normalized_text = re.sub(r"[^A-Z0-9]", "", (text or "").upper())
    normalized_number = re.sub(
        r"[^A-Z0-9]", "", company_number.upper()
    )

    if not normalized_number:
        return False

    return normalized_number in normalized_text



def discover_vat_from_page(url, company_name=None, company_number=None):
    """
    Extract VAT candidates and attach source provenance.
    Company name and number checks are preliminary relevance signals.
    They do not verify VAT registration or company ownership.
    """
    text, metadata = get_page_text(url)

    name_match = (
        page_mentions_company(text, company_name)
        if company_name
        else False
    )

    number_match = (
        page_mentions_company_number(text, company_number)
        if company_number
        else False
    )

    if company_name and not name_match:
        return []

    candidates = extract_vat_numbers(text)
    results = []

    for candidate in candidates:
        results.append({
            **candidate,
            **metadata,
            "company_name_match": name_match,
            "company_number_match": number_match,
        })

    return results