import requests
from bs4 import BeautifulSoup

from vat_extractor import extract_vat_numbers


def get_page_text(url):
    """
    Descarcă o pagină web și extrage textul vizibil.
    """

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Eliminăm elementele care nu conțin text util
    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True
    )

    return text


def discover_vat_from_page(url):
    """
    Caută posibile VAT-uri într-o pagină web.
    """

    text = get_page_text(url)

    vat_numbers = extract_vat_numbers(text)

    return vat_numbers


if __name__ == "__main__":

    url = input("Introdu URL-ul paginii: ")

    try:
        results = discover_vat_from_page(url)

        print("\nVAT-uri găsite:")

        if results:
            for result in results:
                print(f"- VAT: {result['vat_number']}")
                print(f"  Context: {result['context']}")
        else:
            print("- Nu a fost găsit niciun VAT.")

    except requests.RequestException as error:
        print(f"Eroare la accesarea paginii: {error}")