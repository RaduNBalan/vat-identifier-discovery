import csv
from pathlib import Path


REQUIRED_COLUMNS = {
    "CompanyName",
    "CompanyNumber",
    "CompanyStatus",
}


def load_companies(file_path):
    """Load Companies House records from a CSV file."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Company dataset not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        if not reader.fieldnames:
            raise ValueError(
                "The CSV file is empty or has no header."
            )

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)

        if missing:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(sorted(missing))
            )

        companies = list(reader)
        column_count = len(reader.fieldnames)

    print(f"Loaded {len(companies)} companies")
    print(f"Number of columns: {column_count}")

    return companies


if __name__ == "__main__":
    companies = load_companies(
        "data/sample_89_companies.csv"
    )

    print("\nFirst 5 companies:")

    for company in companies[:5]:
        print(
            f"{company['CompanyName']} | "
            f"{company['CompanyNumber']} | "
            f"{company['CompanyStatus']}"
        )