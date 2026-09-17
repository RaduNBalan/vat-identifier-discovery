import pandas as pd


def load_companies(file_path):
    """
    Load the Companies House dataset from a CSV file.
    """
    df = pd.read_csv(file_path)

    print(f"Loaded {len(df)} companies")
    print(f"Number of columns: {len(df.columns)}")

    return df


if __name__ == "__main__":
    companies = load_companies("data/sample_89_companies.csv")

    print("\nFirst 5 companies:")
    print(companies[["CompanyName", "CompanyNumber", "CompanyStatus"]].head())