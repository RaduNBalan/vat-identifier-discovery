import csv
import os


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


def save_result(result, output_path="data/discovery_results.csv"):
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        writer.writerow(result)


if __name__ == "__main__":
    result = {
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
        "Notes": (
            "VAT candidate was discovered on a third-party source "
            "and verified as valid by HMRC, but the HMRC registered "
            "business does not match the target Companies House entity."
        ),
    }

    save_result(result)

    print("Rezultatul a fost salvat.")