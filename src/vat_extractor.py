
import re


VAT_PATTERN = re.compile(
    r"(?<![A-Z0-9])"
    r"(?:(GB|XI)\s*)?"
    r"((?:\d[\s.-]*){9})"
    r"(?![A-Z0-9])",
    re.IGNORECASE,
)


def normalize_vat_number(value):
    """Normalize a nine-digit UK or Northern Ireland VAT candidate."""
    if not value:
        return None

    value = value.upper().strip()

    prefix = "GB"

    if value.startswith("GB") or value.startswith("XI"):
        prefix = value[:2]
        value = value[2:].strip()

    digits = re.sub(r"\D", "", value)

    if len(digits) != 9:
        return None

    return f"{prefix}{digits}"


def has_valid_uk_vat_checksum(vat_number):
    """
    Check the standard nine-digit UK VAT checksum.
    This does not confirm registration or company ownership.
    """
    normalized = normalize_vat_number(vat_number)

    if normalized is None:
        return False

    digits = [int(char) for char in normalized[2:]]

    weighted_sum = sum(
        digit * weight
        for digit, weight in zip(digits[:7], range(8, 1, -1))
    )

    expected = (97 - (weighted_sum % 97)) % 97
    actual = int(normalized[-2:])
    alternative = (expected - 55) % 97

    return actual == expected or actual == alternative


def extract_vat_numbers(text):
    """
    Extract UK VAT candidates and their surrounding context.
    Checksum validity is reported separately.
    """
    if not text:
        return []

    results = []
    seen = set()

    for match in VAT_PATTERN.finditer(text):
        prefix = (match.group(1) or "GB").upper()
        digits = re.sub(r"\D", "", match.group(2))
        candidate = normalize_vat_number(prefix + digits)

        if candidate is None or candidate in seen:
            continue

        seen.add(candidate)

        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)

        results.append({
            "vat_number": candidate,
            "checksum_valid": has_valid_uk_vat_checksum(candidate),
            "context": text[start:end],
        })

    return results


if __name__ == "__main__":
    examples = [
        "VAT number: GB 123 456 789",
        "Registration: 123456789",
        "Northern Ireland VAT: XI123456782",
    ]

    for example in examples:
        print(f"\nInput: {example}")
        for result in extract_vat_numbers(example):
            print(result)
