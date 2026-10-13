import unittest

from src.vat_extractor import (
    extract_vat_numbers,
    normalize_vat_number,
    has_valid_uk_vat_checksum,
)


class TestVatExtractor(unittest.TestCase):
    def test_normalizes_vat_number(self):
        self.assertEqual(normalize_vat_number("GB 123 456 782"), "GB123456782")

    def test_rejects_wrong_length(self):
        self.assertIsNone(normalize_vat_number("GB12345678"))

    def test_checksum_valid(self):
        self.assertTrue(has_valid_uk_vat_checksum("GB123456782"))

    def test_checksum_invalid(self):
        self.assertFalse(has_valid_uk_vat_checksum("GB123456789"))

    def test_extracts_candidate(self):
        results = extract_vat_numbers("VAT number: GB 123 456 789")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["vat_number"], "GB123456789")
        self.assertFalse(results[0]["checksum_valid"])

    def test_deduplicates_candidates(self):
        results = extract_vat_numbers(
            "VAT: GB123456789; again GB 123 456 789"
        )
        self.assertEqual(len(results), 1)
    def test_normalizes_xi_vat_number(self):
        self.assertEqual(
            normalize_vat_number("XI 123 456 782"),
            "XI123456782",
        )

    def test_extracts_xi_candidate(self):
        results = extract_vat_numbers("VAT number: XI123456782")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["vat_number"], "XI123456782")

    def test_does_not_match_vat_inside_alphanumeric_text(self):
        results = extract_vat_numbers("Reference: ABCGB123456789XYZ")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()