import csv
from collections import Counter


def load_results(file_path):
    results = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            results.append(row)

    return results


if __name__ == "__main__":
    results = load_results("data/discovery_results.csv")

    total = len(results)

    statuses = Counter(
        result["FinalStatus"]
        for result in results
    )

    candidates = [
        result
        for result in results
        if result["VATCandidate"].strip()
    ]

    verified = [
        result
        for result in results
        if result["HMRCVerified"].upper() == "TRUE"
    ]

    print("REZULTATE POC")
    print("=============")

    print(f"Total companii: {total}")
    print(f"VAT candidates: {len(candidates)}")
    print(f"HMRC verified: {len(verified)}")

    print("\nStatusuri:")

    for status, count in statuses.items():
        print(f"- {status}: {count}")