
import unittest

from src.vat_verifier import (
    normalize_company_name,
    normalize_postcode,
    normalize_vat,
    compare_entities,
)


class TestVatVerifier(unittest.TestCase):

    def test_normalizes_company_suffix(self):
        self.assertEqual(
            normalize_company_name("Abridge Tax Limited"),
            "ABRIDGE TAX",
        )

    def test_normalizes_postcode(self):
        self.assertEqual(
            normalize_postcode("AL9 5BL"),
            "AL95BL",
        )

    def test_normalizes_vat_number(self):
        self.assertEqual(
            normalize_vat(" 992 082 694 "),
            "GB992082694",
        )

    def test_confirms_matching_name_and_postcode(self):
        result = compare_entities(
            "Example Company Ltd",
            "10 High Street",
            "SW1A 1AA",
            "EXAMPLE COMPANY LIMITED",
            "10 High Street, London, SW1A 1AA, GB",
        )

        self.assertTrue(result["NameMatch"])
        self.assertTrue(result["PostcodeMatch"])
        self.assertTrue(result["EntityMatch"])

    def test_rejects_different_company_name(self):
        result = compare_entities(
            "Abridge Tax Ltd",
            "82 Great North Road",
            "AL9 5BL",
            "Abridge Ltd",
            "418 Staines Road, TW14 8BT, GB",
        )

        self.assertFalse(result["NameMatch"])
        self.assertFalse(result["EntityMatch"])

    def test_rejects_matching_name_without_address_or_postcode(self):
        result = compare_entities(
            "Example Company Ltd",
            "10 High Street",
            "SW1A 1AA",
            "Example Company Limited",
            "99 Other Road, Manchester, M1 1AA, GB",
        )

        self.assertTrue(result["NameMatch"])
        self.assertFalse(result["AddressMatch"])
        self.assertFalse(result["PostcodeMatch"])
        self.assertFalse(result["EntityMatch"])


if __name__ == "__main__":
    unittest.main()
