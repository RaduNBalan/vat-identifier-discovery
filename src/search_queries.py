import csv


def load_companies(file_path):
    companies = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            companies.append(row)

    return companies


def generate_vat_queries(company):
    name = company["CompanyName"].strip()
    company_number = company["CompanyNumber"].strip()
    postcode = company["RegAddress.PostCode"].strip()

    queries = [
        ("company_name_vat", f'"{name}" VAT'),
        ("company_name_vat_number", f'"{name}" "VAT number"'),
        ("company_name_registration", f'"{name}" "VAT registration"'),
        ("company_number_vat", f'"{company_number}" VAT'),
        ("company_number_vat_number", f'"{company_number}" "VAT number"'),
    ]

    if postcode:
        queries.append(
            ("name_postcode_vat", f'"{name}" "{postcode}" VAT')
        )

    return queries


def save_queries(companies, output_path):
    fieldnames = [
        "CompanyNumber",
        "CompanyName",
        "QueryType",
        "Query",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for company in companies:
            queries = generate_vat_queries(company)

            for query_type, query in queries:
                writer.writerow({
                    "CompanyNumber": company["CompanyNumber"],
                    "CompanyName": company["CompanyName"],
                    "QueryType": query_type,
                    "Query": query,
                })


if __name__ == "__main__":
    companies = load_companies("data/sample_89_companies.csv")

    selected_numbers = {
        "15761044",
        "04494986",
        "14983527",
        "17330181",
        "02871100",
        "04427981",
    }

    selected_companies = [
        company
        for company in companies
        if company["CompanyNumber"] in selected_numbers
    ]

    save_queries(
        selected_companies,
        "data/search_queries.csv"
    )

    print(
        f"Au fost generate query-uri pentru "
        f"{len(selected_companies)} companii."
    )

    print("Fișier creat: data/search_queries.csv")