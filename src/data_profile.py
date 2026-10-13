from collections import Counter

from data_loader import load_companies


DATA_PATH = "data/sample_89_companies.csv"

PROFILE_FIELDS = [
    "CompanyName",
    "CompanyNumber",
    "CompanyStatus",
    "CountryOfOrigin",
    "IncorporationDate",
    "CompanyCategory",
    "RegAddress.AddressLine1",
    "RegAddress.PostTown",
    "RegAddress.County",
    "RegAddress.Country",
    "RegAddress.PostCode",
    "SICCode.SicText_1",
]


def profile_companies(companies):
    """Return basic data-quality metrics for company records."""
    missing_by_field = {}

    for field in PROFILE_FIELDS:
        missing_by_field[field] = sum(
            not (company.get(field) or "").strip()
            for company in companies
        )

    statuses = Counter(
        (company.get("CompanyStatus") or "").strip()
        for company in companies
    )

    company_numbers = [
        (company.get("CompanyNumber") or "").strip()
        for company in companies
    ]

    duplicate_numbers = len(company_numbers) - len(set(company_numbers))

    return {
        "total": len(companies),
        "statuses": statuses,
        "missing_by_field": missing_by_field,
        "duplicate_company_numbers": duplicate_numbers,
    }


def main():
    companies = load_companies(DATA_PATH)
    profile = profile_companies(companies)

    print("\nDATA PROFILE")
    print("=" * 40)
    print(f"Total companies: {profile['total']}")
    print(f"Duplicate company numbers: {profile['duplicate_company_numbers']}")

    print("\nCompany status:")
    for status, count in profile["statuses"].most_common():
        print(f"- {status or '[missing]'}: {count}")

    print("\nMissing values by field:")
    for field, count in profile["missing_by_field"].items():
        print(f"- {field}: {count}")


if __name__ == "__main__":
    main()