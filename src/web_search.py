import csv
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


def load_queries(file_path):
    queries = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            queries.append(row)

    return queries


def decode_bing_url(url):
    """
    Extrage URL-ul real din redirect-ul Bing.
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    if "u" not in query_params:
        return url

    encoded_url = query_params["u"][0]

    try:
        decoded = base64.b64decode(encoded_url + "===")
        decoded_url = decoded.decode("utf-8")

        if decoded_url.startswith("http"):
            return decoded_url

    except Exception:
        pass

    return url


def search_web(query):
    url = "https://www.bing.com/search"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    params = {
        "q": query
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for result in soup.select("li.b_algo h2 a"):
        href = result.get("href")

        if not href:
            continue

        real_url = decode_bing_url(href)

        if real_url.startswith("http"):
            results.append(real_url)

    return list(dict.fromkeys(results))


if __name__ == "__main__":
    queries = load_queries("data/search_queries.csv")

    first_query = queries[0]["Query"]

    print(f"Query test: {first_query}")
    print("\nRezultate:")

    try:
        results = search_web(first_query)

        if results:
            for result in results[:10]:
                print(f"- {result}")
        else:
            print("- Nu au fost găsite rezultate.")

    except requests.RequestException as error:
        print(f"Eroare la căutare: {error}")