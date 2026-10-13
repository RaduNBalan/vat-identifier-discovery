
import os
import base64
from urllib.parse import urlparse, parse_qs

import requests
from dotenv import load_dotenv

load_dotenv()

SEARCH_URL = "https://api.tavily.com/search"
REQUEST_TIMEOUT = 20
MAX_RESULTS = 10


def is_http_url(url):
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
        )
    except (TypeError, ValueError):
        return False


def decode_bing_url(url):
    if not is_http_url(url):
        return ""

    parsed = urlparse(url)
    if parsed.hostname not in ("bing.com", "www.bing.com"):
        return url

    encoded = parse_qs(parsed.query).get("u", [""])[0]
    if encoded.startswith("a1"):
        encoded = encoded[2:]

    try:
        encoded += "=" * (-len(encoded) % 4)
        decoded = base64.urlsafe_b64decode(encoded).decode("utf-8")
        return decoded if is_http_url(decoded) else ""
    except (ValueError, UnicodeDecodeError):
        return ""


def load_queries(file_path):
    import csv

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def search_web_results(query, max_results=MAX_RESULTS):
    if not isinstance(query, str) or not query.strip():
        return []

    if not isinstance(max_results, int) or max_results < 1:
        raise ValueError("max_results must be at least 1")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is missing from the environment")

    response = requests.post(
        SEARCH_URL,
        json={
            "api_key": api_key,
            "query": query.strip(),
            "search_depth": "basic",
            "max_results": min(max_results, MAX_RESULTS),
            "include_answer": False,
        },
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    results = []
    seen = set()

    for item in response.json().get("results", []):
        url = item.get("url", "")
        if not is_http_url(url) or url in seen:
            continue

        seen.add(url)
        results.append({
            "url": url,
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "score": item.get("score"),
        })

        if len(results) >= max_results:
            break

    return results


def search_web(query, max_results=MAX_RESULTS):
    """Return result URLs for compatibility with existing callers."""
    return [
        item["url"]
        for item in search_web_results(query, max_results=max_results)
    ]
