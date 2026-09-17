import re


def normalize_text(value):
    """
    Normalizează textul pentru comparații.
    """
    if not value:
        return ""

    value = value.upper()

    replacements = {
        "&": " AND ",
        ",": " ",
        ".": " ",
        "-": " ",
        "'": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = " ".join(value.split())

    return value


def normalize_company_name(value):
    """
    Normalizează numele unei companii.
    """
    value = normalize_text(value)

    suffixes = [
        " LIMITED",
        " LTD",
        " LLP",
        " PLC",
    ]

    for suffix in suffixes:
        if value.endswith(suffix):
            value = value[:-len(suffix)].strip()
            break

    return value


def normalize_postcode(value):
    """
    Normalizează un postcode UK.
    """
    if not value:
        return ""

    return re.sub(r"\s+", "", value.upper())


def normalize_vat(vat_number):
    """
    Normalizează un VAT number UK.
    """
    if not vat_number:
        return ""

    vat = vat_number.upper().replace(" ", "").strip()

    if vat.isdigit():
        vat = "GB" + vat

    return vat


def compare_entities(
    company_name,
    company_address,
    company_postcode,
    hmrc_name,
    hmrc_address,
):
    """
    Compară compania din Companies House cu entitatea returnată de HMRC.
    """

    company_name_normalized = normalize_company_name(company_name)
    hmrc_name_normalized = normalize_company_name(hmrc_name)

    company_address_normalized = normalize_text(company_address)
    hmrc_address_normalized = normalize_text(hmrc_address)

    company_postcode_normalized = normalize_postcode(company_postcode)

    name_match = (
        company_name_normalized == hmrc_name_normalized
    )

    address_match = False

    if company_address_normalized and hmrc_address_normalized:
        address_match = (
            company_address_normalized in hmrc_address_normalized
            or hmrc_address_normalized in company_address_normalized
        )

    postcode_match = False

    if company_postcode_normalized and hmrc_address_normalized:
        postcode_match = (
            company_postcode_normalized in
            normalize_postcode(hmrc_address_normalized)
        )

    return {
        "NameMatch": name_match,
        "AddressMatch": address_match,
        "PostcodeMatch": postcode_match,
        "EntityMatch": name_match and (
            address_match or postcode_match
        ),
    }


if __name__ == "__main__":

    company = {
        "CompanyName": "!ABRIDGE TAX LTD",
        "CompanyAddress": "82 GREAT NORTH ROAD",
        "CompanyPostcode": "AL9 5BL",
    }

    hmrc = {
        "VATNumber": "GB992082694",
        "Name": "ABRIDGE LTD",
        "Address": "418 STAINES ROAD BEDFONT MIDDLESEX TW14 8BT GB",
    }

    vat_number = normalize_vat(hmrc["VATNumber"])

    comparison = compare_entities(
        company["CompanyName"],
        company["CompanyAddress"],
        company["CompanyPostcode"],
        hmrc["Name"],
        hmrc["Address"],
    )

    print("VAT verificat:")
    print(f"- VAT: {vat_number}")

    print("\nComparație entitate:")
    print(f"- Name match: {comparison['NameMatch']}")
    print(f"- Address match: {comparison['AddressMatch']}")
    print(f"- Postcode match: {comparison['PostcodeMatch']}")
    print(f"- Entity match: {comparison['EntityMatch']}")

    if comparison["EntityMatch"]:
        print("\nRezultat: CONFIRMED")
    else:
        print("\nRezultat: FALSE_POSITIVE")