import csv


def load_queries(file_path):
    queries = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            queries.append(row)

    return queries


if __name__ == "__main__":
    queries = load_queries("data/search_queries.csv")

    print(f"Au fost încărcate {len(queries)} query-uri.")

    for query in queries:
        print()
        print(f"Companie: {query['CompanyName']}")
        print(f"Company Number: {query['CompanyNumber']}")
        print(f"Tip query: {query['QueryType']}")
        print(f"Căutare: {query['Query']}")