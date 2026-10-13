
import argparse
import csv
import time
from pathlib import Path

import requests

try:
    from .web_search import load_queries, search_web_results
    from .web_discovery import (
        discover_vat_from_page,
        normalize_company_name,
        page_mentions_company,
        page_mentions_company_number,
    )
    from .vat_extractor import extract_vat_numbers
    from .results_logger import save_result
    from .companies_house import get_company_details
    from .hmrc_client import (
        verify_vat_number,
        HMRCAPIError,
        HMRCConfigurationError,
    )
    from .vat_verifier import compare_entities
except ImportError:
    from web_search import load_queries, search_web_results
    from web_discovery import (
        discover_vat_from_page,
        normalize_company_name,
        page_mentions_company,
        page_mentions_company_number,
    )
    from vat_extractor import extract_vat_numbers
    from results_logger import save_result
    from companies_house import get_company_details
    from hmrc_client import (
        verify_vat_number,
        HMRCAPIError,
        HMRCConfigurationError,
    )
    from vat_verifier import compare_entities


DEFAULT_QUERY_FILE = "data/search_queries.csv"
DEFAULT_OUTPUT_FILE = "data/discovery_results_live.csv"
MAX_PAGES_PER_QUERY = 5
DELAY_BETWEEN_QUERIES = 1.0

OUTPUT_FIELDS = [
    "CompanyNumber",
    "CompanyName",
    "Query",
    "SourceURL",
    "FinalURL",
    "SourceType",
    "VATCandidate",
    "ChecksumValid",
    "HMRCVerified",
    "HMRCName",
    "HMRCAddress",
    "EntityMatch",
    "FinalStatus",
    "Notes",
]


def ensure_output_file(output_file):
    """Create the output CSV with headers if it does not exist."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not output_path.exists() or output_path.stat().st_size == 0:
        with output_path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as file:
            writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()


def candidates_from_search_snippet(
    search_result, company_name, company_number
):
    """
    Extract preliminary candidates from a search result snippet.

    A name or company-number match is required. A search snippet alone
    cannot establish that a VAT number belongs to the target company.
    """
    title = search_result.get("title", "")
    content = search_result.get("content", "")
    snippet = f"{title} {content}".strip()

    name_match = page_mentions_company(snippet, company_name)
    number_match = page_mentions_company_number(snippet, company_number)

    if not (name_match or number_match):
        return []

    url = search_result.get("url", "")
    candidates = []

    for candidate in extract_vat_numbers(snippet):
        candidates.append({
            **candidate,
            "source_url": url,
            "final_url": url,
            "company_name_match": name_match,
            "company_number_match": number_match,
            "source_type": "search_snippet",
        })

    return candidates


def verify_and_save_candidate(
    candidate,
    company_number,
    registered_name,
    query,
    company_address,
    company_postcode,
    output_file,
):
    """Apply checksum, HMRC verification and entity-attribution checks."""
    vat_number = candidate.get("vat_number", "")
    source_url = candidate.get("source_url", "")
    final_url = candidate.get("final_url") or source_url

    if not vat_number:
        return False, 0, 0

    checksum_valid = bool(candidate.get("checksum_valid", False))
    hmrc_verified = "NOT_CHECKED"
    hmrc_name = ""
    hmrc_address = ""
    entity_match = "NOT_CHECKED"
    final_status = "REVIEW"
    notes = []

    if candidate.get("source_type") == "search_snippet":
        notes.append(
            "Candidate discovered from a search-result snippet; "
            "the original page could not be accessed."
        )

    hmrc_checks = 0
    errors = 0

    if not checksum_valid:
        final_status = "INVALID"
        notes.append("VAT checksum failed.")
    else:
        try:
            hmrc_result = verify_vat_number(vat_number)
            hmrc_checks += 1

            if hmrc_result.get("status") == "NOT_FOUND":
                hmrc_verified = "NOT_FOUND"
                notes.append(
                    "HMRC did not find this VAT candidate. "
                    "This does not prove that the company is not "
                    "VAT registered."
                )
            elif hmrc_result.get("status") == "REGISTERED":
                hmrc_verified = "VERIFIED"
                details = hmrc_result.get("details") or {}
                target = details.get("target") or {}

                hmrc_name = target.get("name", "")
                address = target.get("address") or {}

                address_parts = [
                    address.get("line1", ""),
                    address.get("line2", ""),
                    address.get("line3", ""),
                    address.get("line4", ""),
                ]

                hmrc_address = ", ".join(
                    part for part in address_parts if part
                )
                hmrc_postcode = address.get("postcode", "")

                match = compare_entities(
                    company_name=registered_name,
                    company_address=company_address,
                    company_postcode=company_postcode,
                    hmrc_name=hmrc_name,
                    hmrc_address=(
                        f"{hmrc_address} {hmrc_postcode}"
                    ).strip(),
                )

                if match.get("EntityMatch", False):
                    entity_match = "MATCH"
                    final_status = "CONFIRMED"
                    notes.append(
                        "HMRC verified the VAT number and the "
                        "entity-attribution criteria passed."
                    )
                else:
                    entity_match = "NO_MATCH"
                    notes.append(
                        "HMRC returned a registered VAT number, "
                        "but the company identity did not pass "
                        "the attribution criteria."
                    )
            else:
                errors += 1
                notes.append(
                    "HMRC returned an unrecognised status; "
                    "the candidate requires manual review."
                )

        except (HMRCAPIError, HMRCConfigurationError) as error:
            errors += 1
            notes.append(f"HMRC verification error: {error}")
        except (KeyError, TypeError, ValueError) as error:
            errors += 1
            notes.append(f"Could not evaluate HMRC identity: {error}")

    result = {
        "CompanyNumber": company_number,
        "CompanyName": registered_name,
        "Query": query,
        "SourceURL": source_url,
        "FinalURL": final_url,
        "SourceType": candidate.get("source_type", "public_web"),
        "VATCandidate": vat_number,
        "ChecksumValid": str(checksum_valid).upper(),
        "HMRCVerified": hmrc_verified,
        "HMRCName": hmrc_name,
        "HMRCAddress": hmrc_address,
        "EntityMatch": entity_match,
        "FinalStatus": final_status,
        "Notes": " ".join(notes),
    }

    save_result(result, output_file)

    print(
        f"  VAT: {vat_number} | "
        f"Checksum: {checksum_valid} | "
        f"HMRC: {hmrc_verified} | "
        f"Entity: {entity_match} | "
        f"Status: {final_status}"
    )

    return True, hmrc_checks, errors


def run_discovery(
    query_file=DEFAULT_QUERY_FILE,
    output_file=DEFAULT_OUTPUT_FILE,
    max_pages=MAX_PAGES_PER_QUERY,
    delay=DELAY_BETWEEN_QUERIES,
):
    ensure_output_file(output_file)
    queries = load_queries(query_file)

    if not queries:
        print(f"Nu exista query-uri in {query_file}.")
        return

    seen_records = set()
    query_count = 0
    pages_checked = 0
    candidates_found = 0
    hmrc_checks = 0
    errors = 0

    print(f"Query-uri incarcate: {len(queries)}")

    for query_row in queries:
        company_number = query_row.get("CompanyNumber", "").strip()
        company_name = query_row.get("CompanyName", "").strip()
        query = query_row.get("Query", "").strip()
        company_address = query_row.get("CompanyAddress", "").strip()
        company_postcode = query_row.get("CompanyPostcode", "").strip()

        if not company_number or not company_name or not query:
            print("Query ignorat: lipsesc date obligatorii.")
            errors += 1
            continue

        query_count += 1
        print(f"\n[{query_count}/{len(queries)}] {company_name}")
        print(f"Query: {query}")

        try:
            company_details = get_company_details(company_number)
            registered_name = company_details["company_name"]
            company_status = company_details["company_status"]

            print(f"  Companies House name: {registered_name}")
            print(f"  Companies House status: {company_status}")

        except (requests.RequestException, ValueError, KeyError) as error:
            print(f"  Companies House verification failed: {error}")
            errors += 1
            time.sleep(delay)
            continue

        if normalize_company_name(company_name) != normalize_company_name(
            registered_name
        ):
            print("  Company name mismatch; VAT search skipped.")
            errors += 1
            time.sleep(delay)
            continue

        print("  Company name match: OK")

        try:
            search_results = search_web_results(query)
        except (requests.RequestException, ValueError) as error:
            print(f"  Eroare la cautare: {error}")
            errors += 1
            time.sleep(delay)
            continue

        if not search_results:
            print("  Nu au fost returnate rezultate.")
            time.sleep(delay)
            continue

        for search_result in search_results[:max_pages]:
            url = search_result.get("url", "")
            if not url:
                continue

            pages_checked += 1
            candidates = []
            page_error = None

            try:
                candidates = discover_vat_from_page(
                    url,
                    company_name=registered_name,
                    company_number=company_number,
                )
            except (requests.RequestException, ValueError) as error:
                page_error = error
                print(f"  Pagina inaccesibila: {url} ({error})")
            except Exception as error:
                page_error = error
                print(f"  Eroare la pagina {url}: {error}")

            if page_error is not None:
                snippet_candidates = candidates_from_search_snippet(
                    search_result,
                    registered_name,
                    company_number,
                )

                if snippet_candidates:
                    print(
                        "  Se foloseste fragmentul Tavily ca sursa "
                        "preliminara."
                    )
                    candidates.extend(snippet_candidates)
                else:
                    errors += 1
                    continue

            for candidate in candidates:
                vat_number = candidate.get("vat_number", "")
                final_url = candidate.get("final_url") or url

                if not vat_number:
                    continue

                # Require the page or snippet to identify the target entity.
                if not (
                    candidate.get("company_name_match", False)
                    or candidate.get("company_number_match", False)
                ):
                    continue

                key = (company_number, vat_number, final_url)
                if key in seen_records:
                    continue

                seen_records.add(key)
                candidates_found += 1

                _, checks, candidate_errors = verify_and_save_candidate(
                    candidate=candidate,
                    company_number=company_number,
                    registered_name=registered_name,
                    query=query,
                    company_address=company_address,
                    company_postcode=company_postcode,
                    output_file=output_file,
                )

                hmrc_checks += checks
                errors += candidate_errors

        time.sleep(delay)

    print("\n--- Rezumat descoperire ---")
    print(f"Query-uri procesate: {query_count}")
    print(f"Pagini/rezultate procesate: {pages_checked}")
    print(f"Candidate salvate: {candidates_found}")
    print(f"Verificari HMRC executate: {hmrc_checks}")
    print(f"Erori/elemente omise: {errors}")
    print(f"Fisier rezultate: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descopera si verifica candidati VAT din surse web."
    )
    parser.add_argument("--queries", default=DEFAULT_QUERY_FILE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE)
    parser.add_argument(
        "--max-pages", type=int, default=MAX_PAGES_PER_QUERY
    )
    parser.add_argument(
        "--delay", type=float, default=DELAY_BETWEEN_QUERIES
    )

    args = parser.parse_args()

    if args.max_pages < 1:
        parser.error("--max-pages trebuie sa fie cel putin 1.")

    if args.delay < 0:
        parser.error("--delay nu poate fi negativ.")

    run_discovery(
        query_file=args.queries,
        output_file=args.output,
        max_pages=args.max_pages,
        delay=args.delay,
    )
