
import csv
import os


FIELDNAMES = [
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


def save_result(result, output_path="data/discovery_results_live.csv"):
    directory = os.path.dirname(output_path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    file_exists = os.path.exists(output_path)
    write_header = not file_exists or os.path.getsize(output_path) == 0

    with open(output_path, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        writer.writerow({
            field: result.get(field, "")
            for field in FIELDNAMES
        })


if __name__ == "__main__":
    print(
        "Logger pregătit. Rezultatele noi vor fi salvate în "
        "data/discovery_results_live.csv."
    )
