
import argparse
import csv
from pathlib import Path


def load_companies(file_path):
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def generate_vat_queries(company):
    name = company.get("CompanyName", "").strip().replace('"', "")
    company_number = company.get("CompanyNumber", "").strip()
    postcode = company.get("RegAddress.PostCode", "").strip()
    address = company.get("RegAddress.AddressLine1", "").strip()
    town = company.get("RegAddress.PostTown", "").strip()
    country = company.get("RegAddress.Country", "").strip()

    queries = []

    if name:
        queries.extend([
            ("company_name_vat", f'"{name}" VAT'),
            ("company_name_vat_number", f'"{name}" "VAT number"'),
            ("company_name_vat_registration", f'"{name}" "VAT registration"'),
        ])

    if company_number:
        queries.extend([
            ("company_number_vat", f'"{company_number}" VAT'),
            ("company_number_vat_number", f'"{company_number}" "VAT number"'),
        ])

    if name and postcode:
        queries.append(
            ("name_postcode_vat", f'"{name}" "{postcode}" VAT')
        )

    if name and address and town:
        queries.append(
            ("name_address_town_vat", f'"{name}" "{address}" "{town}" VAT')
        )

    if name and postcode and country:
        queries.append(
            ("name_postcode_country_vat",
             f'"{name}" "{postcode}" "{country}" VAT')
        )

    return queries


def save_queries(companies, output_path):
    fieldnames = [
        "CompanyNumber",
        "CompanyName",
        "CompanyAddress",
        "CompanyPostcode",
        "QueryType",
        "Query",
    ]

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for company in companies:
            for query_type, query in generate_vat_queries(company):
                writer.writerow({
                    "CompanyNumber": company.get("CompanyNumber", "").strip(),
                    "CompanyName": company.get("CompanyName", "").strip(),
                    "CompanyAddress": company.get(
                        "RegAddress.AddressLine1", ""
                    ).strip(),
                    "CompanyPostcode": company.get(
                        "RegAddress.PostCode", ""
                    ).strip(),
                    "QueryType": query_type,
                    "Query": query,
                })


def main():
    parser = argparse.ArgumentParser(
        description="Generate VAT discovery search queries from a company CSV."
    )
    parser.add_argument(
        "--input",
        default="data/sample_89_companies.csv",
        help="Input company CSV file.",
    )
    parser.add_argument(
        "--output",
        default="data/search_queries.csv",
        help="Output query CSV file.",
    )
    args = parser.parse_args()

    companies = load_companies(args.input)
    save_queries(companies, args.output)

    query_count = sum(len(generate_vat_queries(company)) for company in companies)
    print(f"Companii procesate: {len(companies)}")
    print(f"Query-uri generate: {query_count}")
    print(f"Fisier creat: {args.output}")


if __name__ == "__main__":
    main()
