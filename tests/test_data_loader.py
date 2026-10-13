import csv
import tempfile
import unittest
from pathlib import Path

from src.data_loader import load_companies


class TestDataLoader(unittest.TestCase):

    def test_loads_valid_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "companies.csv"

            with path.open(
                "w",
                encoding="utf-8-sig",
                newline=""
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "CompanyName",
                        "CompanyNumber",
                        "CompanyStatus",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "CompanyName": "Example Ltd",
                    "CompanyNumber": "01234567",
                    "CompanyStatus": "Active",
                })

            companies = load_companies(path)

            self.assertEqual(len(companies), 1)
            self.assertEqual(
                companies[0]["CompanyNumber"],
                "01234567",
            )

    def test_missing_file_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.csv"

            with self.assertRaises(FileNotFoundError):
                load_companies(path)

    def test_missing_required_column_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "companies.csv"
            path.write_text(
                "CompanyName,CompanyNumber\nExample Ltd,01234567\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_companies(path)


if __name__ == "__main__":
    unittest.main()