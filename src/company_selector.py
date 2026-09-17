import csv


def load_companies(file_path):
    companies = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            companies.append(row)

    return companies


def show_company(company):
    print("\nCompanie selectată")
    print("------------------")
    print(f"Nume: {company['CompanyName']}")
    print(f"Număr Companies House: {company['CompanyNumber']}")
    print(f"Statut: {company['CompanyStatus']}")
    print(f"Țara: {company['CountryOfOrigin']}")
    print(f"Data înființării: {company['IncorporationDate']}")
    print(f"Categoria: {company['CompanyCategory']}")
    print(f"Adresă: {company['RegAddress.AddressLine1']}")
    print(f"Localitate: {company['RegAddress.PostTown']}")
    print(f"Județ/Regiune: {company['RegAddress.County']}")
    print(f"Țara adresei: {company['RegAddress.Country']}")
    print(f"Cod poștal: {company['RegAddress.PostCode']}")
    print(f"Activitate SIC: {company['SICCode.SicText_1']}")


if __name__ == "__main__":
    companies = load_companies("data/sample_89_companies.csv")

    print(f"Au fost încărcate {len(companies)} companii.")

    print("\nCompaniile 11-30:")
    print("=================")

    for company in companies[10:30]:
        show_company(company)