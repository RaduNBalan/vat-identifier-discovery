import re


VAT_PATTERN = re.compile(
    r"\b(?:GB\s*)?\d{3}\s*\d{3}\s*\d{3}\b",
    re.IGNORECASE
)


def extract_vat_numbers(text):
    """
    Identifică posibile numere VAT UK într-un text
    și păstrează contextul în care au fost găsite.
    """

    results = []

    for match in VAT_PATTERN.finditer(text):
        number = re.sub(r"\s+", "", match.group(0)).upper()

        if not number.startswith("GB"):
            number = "GB" + number

        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)

        context = text[start:end]

        result = {
            "vat_number": number,
            "context": context
        }

        if result not in results:
            results.append(result)

    return results


if __name__ == "__main__":

    test_text = """
    Example Company Ltd
    Company Number: 12345678
    VAT Registration Number: GB 123 456 789
    """

    results = extract_vat_numbers(test_text)

    print("VAT-uri găsite:")

    for result in results:
        print(f"- VAT: {result['vat_number']}")
        print(f"  Context: {result['context']}")