"""Retrieve company identity details from the public Companies House website."""

import re

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://find-and-update.company-information.service.gov.uk"
REQUEST_TIMEOUT = 15


def get_company_details(company_number):
    """
    Retrieve a company's name, registration number, and legal status.

    Returns a dictionary with the company details, or raises an exception
    if the company cannot be retrieved or the expected data is missing.
    """
    if not isinstance(company_number, str):
        company_number = str(company_number)

    company_number = company_number.strip().upper()

    if not re.fullmatch(r"[A-Z0-9]{8}", company_number):
        raise ValueError("Company number must contain exactly 8 letters or digits.")

    url = f"{BASE_URL}/company/{company_number}"

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "VAT-Identifier-Discovery/1.0"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    name_element = soup.select_one("h1.heading-xlarge")
    status_element = soup.select_one("#company-status")
    number_element = soup.select_one("#company-number")

    if not name_element or not status_element or not number_element:
        raise ValueError(
            f"Could not extract company details for {company_number}."
        )

    page_number = number_element.get_text(" ", strip=True)

    if company_number not in page_number.replace(" ", "").upper():
        raise ValueError(
            f"Company number mismatch for {company_number}."
        )

    return {
        "company_number": company_number,
        "company_name": name_element.get_text(" ", strip=True),
        "company_status": status_element.get_text(" ", strip=True),
        "source_url": response.url,
    }