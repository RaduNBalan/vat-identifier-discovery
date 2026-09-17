import csv


RESULTS = [
    {
        "CompanyNumber": "16092999",
        "CompanyName": "!ABRIDGE TAX LTD",
        "SourceURL": "https://vat-lookup.co.uk/verify/vat_check.php/VATNumber/GB992082694",
        "SourceType": "third_party",
        "VATCandidate": "GB992082694",
        "HMRCVerified": "TRUE",
        "HMRCName": "ABRIDGE LTD",
        "HMRCAddress": "418 STAINES ROAD; BEDFONT; MIDDLESEX; TW14 8BT; GB",
        "EntityMatch": "FALSE",
        "FinalStatus": "FALSE_POSITIVE",
        "Notes": "VAT candidate was discovered on a third-party source and verified as valid by HMRC, but the HMRC registered business does not match the target Companies House entity.",
    },
    {
        "CompanyNumber": "14983527",
        "CompanyName": '"4RENT ESTATES" LTD',
        "SourceURL": "",
        "SourceType": "",
        "VATCandidate": "",
        "HMRCVerified": "FALSE",
        "HMRCName": "",
        "HMRCAddress": "",
        "EntityMatch": "",
        "FinalStatus": "NOT_FOUND",
        "Notes": "No VAT candidate discovered in the searched public web sources.",
    },
    {
        "CompanyNumber": "15761044",
        "CompanyName": '"A TASTE OF TUSCANY" LTD',
        "SourceURL": "",
        "SourceType": "",
        "VATCandidate": "",
        "HMRCVerified": "FALSE",
        "HMRCName": "",
        "HMRCAddress": "",
        "EntityMatch": "",
        "FinalStatus": "NOT_FOUND",
        "Notes": "No VAT candidate explicitly attributable to company 15761044 was discovered in the searched public sources.",
    },
    {
        "CompanyNumber": "04494986",
        "CompanyName": '"A" CERAMICS LIMITED',
        "SourceURL": "",
        "SourceType": "",
        "VATCandidate": "",
        "HMRCVerified": "FALSE",
        "HMRCName": "",
        "HMRCAddress": "",
        "EntityMatch": "",
        "FinalStatus": "NOT_FOUND",
        "Notes": "No VAT candidate explicitly attributable to company 04494986 was discovered in the searched public sources.",
    },
    {
        "CompanyNumber": "17330181",
        "CompanyName": '"BACKS" LTD',
        "SourceURL": "",
        "SourceType": "",
        "VATCandidate": "",
        "HMRCVerified": "FALSE",
        "HMRCName": "",
        "HMRCAddress": "",
        "EntityMatch": "",
        "FinalStatus": "NOT_FOUND",
        "Notes": "No VAT candidate explicitly attributable to company 17330181 was discovered in the searched public sources.",
    },
    {
        "CompanyNumber": "02871100",
        "CompanyName": "BEDE INVESTMENT PROPERTIES LIMITED",
        "SourceURL": "",
        "SourceType": "",
        "VATCandidate": "",
        "HMRCVerified": "FALSE",
        "HMRCName": "",
        "HMRCAddress": "",
        "EntityMatch": "",
        "FinalStatus": "NOT_FOUND",
        "Notes": "No VAT candidate explicitly attributable to company 02871100 was discovered in the searched public sources.",
    },
    {
        "CompanyNumber": "04427981",
        "CompanyName": '"BELLE-VUE" ENTERPRISES LIMITED',
        "SourceURL": "",
        "SourceType": "",
        "VATCandidate": "",
        "HMRCVerified": "FALSE",
        "HMRCName": "",
        "HMRCAddress": "",
        "EntityMatch": "",
        "FinalStatus": "NOT_FOUND",
        "Notes": "No VAT candidate explicitly attributable to company 04427981 was discovered in the searched public sources.",
    },
]


FIELDNAMES = [
    "CompanyNumber",
    "CompanyName",
    "SourceURL",
    "SourceType",
    "VATCandidate",
    "HMRCVerified",
    "HMRCName",
    "HMRCAddress",
    "EntityMatch",
    "FinalStatus",
    "Notes",
]


if __name__ == "__main__":
    with open(
        "data/discovery_results.csv",
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES
        )

        writer.writeheader()
        writer.writerows(RESULTS)

    print(f"Au fost salvate {len(RESULTS)} rezultate.")
    print("Fișier: data/discovery_results.csv")