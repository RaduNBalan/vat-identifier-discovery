import csv


def load_companies(file_path):
    companies = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            companies.append(row)

    return companies


def profile_companies(companies):
    print(f"Număr total de companii: {len(companies)}")

    print("\nColoane disponibile:")

    if companies:
        for column in companies[0].keys():
            print(f"- {column}")

    print("\nStatutul companiilor:")

    statuses = {}

    for company in companies:
        status = company["CompanyStatus"]

        if status not in statuses:
            statuses[status] = 0

        statuses[status] += 1

    for status, count in statuses.items():
        print(f"- {status}: {count}")

    print("\nValori lipsă:")

    for column in companies[0].keys():
        missing = 0

        for company in companies:
            value = company[column]

            if value is None or value.strip() == "":
                missing += 1

        print(f"- {column}: {missing} valori lipsă")

if __name__ == "__main__":
    companies = load_companies("data/sample_89_companies.csv")

    profile_companies(companies)