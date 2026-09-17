# VAT Identifier Discovery

## 1. Problem Understanding

The objective is to determine whether a UK company VAT dataset can be built from publicly available web data and to demonstrate the approach on a proof-of-concept sample.

The input dataset contains UK companies from Companies House. The target is to discover VAT registration numbers for companies where the VAT number is not directly available in the input data.

The main challenge is that VAT discovery and VAT verification are two different problems. HMRC can verify a VAT number when the number is already known, but the verification service does not provide a general company-name-to-VAT lookup mechanism.

The proposed pipeline therefore separates the problem into three stages:

1. Discovery — find potential VAT numbers from publicly available sources.
2. Verification — check whether the discovered VAT number is valid using an official verification source.
3. Entity matching — determine whether the verified VAT number belongs to the target Companies House company.

This separation is important because a valid VAT number can still belong to a different company. In such a case, accepting the number would create a false positive and could corrupt downstream company matching.

A second important limitation is that failure to discover a VAT number does not prove that a company is not VAT registered. Therefore, companies for which no sufficiently reliable VAT candidate was discovered are classified as `NOT_FOUND` rather than `NOT_VAT_REGISTERED`.

The proof of concept focuses on demonstrating the reliability of the pipeline and, in particular, its ability to reject valid VAT numbers that belong to the wrong entity.


## 2. Data Source

### Companies House

The primary company dataset used in this proof of concept is the Companies House Basic Company Data bulk dataset.

Companies House provides structured information about UK-registered companies, including:

- Company Name
- Company Number
- Company Status
- Country of Origin
- Incorporation Date
- Company Category
- Registered Address
- Postcode
- SIC Code

The Company Number is used as the primary identifier for entity-level matching throughout the pipeline.

The dataset is used as an identity backbone rather than as a VAT source. The main purpose of Companies House data is to define the target entity and provide attributes that can later be used to validate whether a discovered VAT number belongs to that entity.

### POC Sample

The original bulk file contains a substantially larger number of companies. For development and experimentation, a small sample of 89 companies was extracted from the beginning of the bulk dataset.

The sample contains:

- 89 companies
- 89 active companies
- Company Name available for all records
- Company Number available for all records
- SIC Code available for all records

Several registered-address fields contain missing values.

The sample is not presented as a nationally representative sample of UK companies. It is a development and proof-of-concept sample extracted from the beginning of the bulk file.

This distinction is important because the POC is intended to validate the pipeline and identify failure modes, rather than estimate nationwide VAT coverage.

### Why Companies House?

Companies House provides a stable company-level identity through the Company Number.

Company names alone are not sufficient for reliable entity matching because:

- different companies can have similar names;
- company names can change;
- historical companies can have the same or similar names;
- a VAT number discovered from a third-party source may refer to another legal entity.

Therefore, the Company Number is treated as the primary identity key, while company name, registered address, postcode and SIC information are used as supporting attributes.


## 3. Research and Experiments

The initial research focused on understanding the distinction between VAT discovery and VAT verification and identifying publicly accessible sources that could provide VAT candidates.

Several approaches were investigated.

### 3.1 Companies House

Companies House was evaluated as the primary company identity source.

It provides company identifiers and registered company information, but it is not used as a direct VAT discovery mechanism in this proof of concept.

Therefore, Companies House was retained as the identity backbone of the pipeline rather than as the main VAT discovery source.

### 3.2 HMRC VAT Verification

HMRC was evaluated as the authoritative verification layer.

The key finding was that verification is fundamentally different from discovery: the verifier can validate a VAT number when a candidate is already known, but it does not provide a general reverse lookup from company name to VAT number.

Therefore, HMRC is used after discovery rather than as the primary discovery mechanism.

### 3.3 Search Engine Discovery

Search engine queries were generated using combinations of:

- company name + VAT
- company name + VAT number
- company name + VAT registration
- company number + VAT
- company number + VAT number
- company name + postcode + VAT

The goal was to identify public pages containing possible VAT numbers.

Direct scraping of search engine result pages was also tested. This approach was not considered reliable for the final pipeline because the returned pages included consent, login, redirect and unrelated result pages rather than a stable machine-readable search result interface.

This experiment was retained as a documented research/dead-end result rather than being used as the final discovery mechanism.

### 3.4 Third-Party Sources

Third-party VAT directories were also investigated.

These sources can be useful for discovery because they may expose VAT numbers that are not visible on the company's official website.

However, they are not treated as authoritative.

A third-party VAT candidate is therefore only a candidate. It must pass official verification and entity matching before being accepted.

### 3.5 Official Company Websites

Official company websites were considered a high-value discovery source because VAT numbers may appear in legal notices, invoices, terms and conditions, footer information or other company documentation.

However, absence of a VAT number from an official website is not interpreted as proof that the company is not VAT registered.

### Research Conclusion

The experiments led to a cascade-based discovery strategy:

1. Search company-owned sources first.
2. Search public documents and other structured public sources.
3. Use third-party sources as candidate generators.
4. Verify discovered candidates using an authoritative VAT verification service.
5. Perform entity matching before accepting the result.


## 4. Discovery Method

The discovery pipeline generates search queries for each target company and looks for publicly available sources that may contain a VAT identifier.

The discovery process does not automatically accept every number matching the UK VAT format. Every discovered number is treated as a candidate until it passes verification and entity matching.

### 4.1 Query Generation

For each company, multiple query patterns are generated.

The current proof of concept uses:

- `"Company Name" VAT`
- `"Company Name" "VAT number"`
- `"Company Name" "VAT registration"`
- `"Company Number" VAT`
- `"Company Number" "VAT number"`
- `"Company Name" "Postcode" VAT`

Using both the company name and the Companies House Company Number helps reduce ambiguity between similarly named entities.

The postcode is used as an additional search signal when it is available.

### 4.2 Web Page Processing

When a candidate source page is available, the page is downloaded and converted into plain text.

HTML elements that do not contain useful page content, such as scripts and styles, are removed before extraction.

The resulting text is passed to the VAT extraction module.

The proof of concept keeps the discovery and extraction modules separate so that different discovery sources can be tested without changing the VAT parsing logic.

### 4.3 VAT Candidate Extraction

Potential VAT numbers are extracted from the text of discovered pages using a regular expression.

The extractor accepts common UK VAT formatting variants such as:

```text
GB123456789
GB 123 456 789
123456789
The extractor also stores surrounding text as context. This context can later be used to determine whether the VAT number appears in a relevant part of the page and whether it is associated with the target company.

The extraction step only produces candidates. It does not determine whether the number is valid or whether it belongs to the target company.
## 5. Verification and Entity Matching

### 5.1 VAT Verification

A discovered VAT number is not accepted directly into the final dataset.

The candidate must first be checked against an authoritative VAT verification source.

The verification step answers:

> Is this VAT number valid?

The verification result may include the registered business name and address associated with the VAT number.

A valid response alone is not sufficient to accept the candidate because the verified VAT number may belong to a different legal entity.

### 5.2 Entity Matching

After verification, the returned company information is compared with the target Companies House entity.

The matching process uses:

- Company Name
- Registered Address
- Postcode

The Companies House Company Number remains the primary identifier of the target entity.

Company names are normalized before comparison by standardizing punctuation, whitespace and common legal suffixes such as:

```text
LTD
LIMITED
LLP
PLC
Address and postcode information are used as supporting evidence.

The proof-of-concept matching rule requires:
Name match
AND
(Address match OR Postcode match)
A VAT number is therefore accepted only when:

1.the VAT number is successfully verified; and
2.the verified entity matches the target company.

This prevents a valid VAT number belonging to another company from being incorrectly assigned to the target company.

5.3 False Positive Example

One of the investigated companies was:
Company: !ABRIDGE TAX LTD
Company Number: 16092999
A VAT candidate was discovered from a third-party source:
GB992082694
The candidate was verified as a valid VAT number, but the verification result corresponded to:
ABRIDGE LTD
418 STAINES ROAD
BEDFONT
MIDDLESEX
TW14 8BT
The verified entity did not match the target Companies House entity.

Therefore:
VAT verification: PASS
Entity matching: FAIL
Final status: FALSE_POSITIVE
This example demonstrates why VAT verification and entity matching must be separate stages.

The VAT number itself can be valid while its attribution to the target company is incorrect.

6. Proof of Concept Results

The proof of concept contains seven investigated companies.

The result categories are:

FALSE_POSITIVE — a VAT candidate was found and verified, but the verified entity did not match the target company.
NOT_FOUND — no sufficiently reliable VAT candidate was discovered in the searched sources.
CONFIRMED — a VAT candidate was verified and successfully matched to the target company.
INVALID — a discovered VAT candidate failed official verification.

The current POC results are:
The current POC results are:

| Company Number | Company Name | VAT Candidate | HMRC Verified | Entity Match | Final Status |
|---|---|---|---|---|---|
| 16092999 | !ABRIDGE TAX LTD | GB992082694 | TRUE | FALSE | FALSE_POSITIVE |
| 14983527 | "4RENT ESTATES" LTD | - | - | - | NOT_FOUND |
| 15761044 | "A TASTE OF TUSCANY" LTD | - | - | - | NOT_FOUND |
| 04494986 | "A" CERAMICS LIMITED | - | - | - | NOT_FOUND |
| 17330181 | "BACKS" LTD | - | - | - | NOT_FOUND |
| 02871100 | BEDE INVESTMENT PROPERTIES LIMITED | - | - | - | NOT_FOUND |
| 04427981 | "BELLE-VUE" ENTERPRISES LIMITED | - | - | - | NOT_FOUND |

### POC Summary

The observed results are:

```text
Total companies investigated: 7
VAT candidates discovered: 1
VAT candidates verified: 1
Confirmed entity matches: 0
False positives: 1
Not found: 6
The single discovered candidate was a false positive.

Therefore, the observed false-positive rate among discovered candidates is: 1 / 1 = 100%
However, this should not be interpreted as an estimate of the production false-positive rate. The sample contains only one discovered candidate, so the observation is too small to provide a statistically reliable performance estimate.

The main purpose of the POC is to demonstrate that the pipeline can identify and reject an important failure mode: a valid VAT number belonging to the wrong entity.

Interpretation of NOT_FOUND

NOT_FOUND does not mean that the company is not VAT registered.

It means that no sufficiently reliable VAT candidate was discovered using the sources and queries investigated during the POC.

This distinction is important because the public web does not provide complete ground truth for VAT registration status.

7. Limitations

The proof of concept has several important limitations.

7.1 Sample Size

Only seven companies were taken through the complete discovery and verification analysis.

The broader sample of 89 companies was used for development and data profiling, but it was not fully processed through the complete VAT discovery pipeline.

Therefore, the POC results cannot be extrapolated directly to all UK companies.

7.2 Sample Representativeness

The 89-company development sample was extracted from the beginning of the Companies House bulk dataset.

It is therefore not treated as a statistically representative UK company sample.

A production evaluation should use stratified sampling across factors such as:

company size;
SIC code;
company age;
geography;
company status;
presence or absence of a public website.
7.3 No Complete Ground Truth

There is no complete reference dataset available that provides the correct VAT status and VAT number for every company in the input population.

As a result, a missing discovered VAT cannot automatically be classified as an actual absence of VAT registration.

7.4 Web Availability

Public websites may:

block automated requests;
require JavaScript;
change their structure;
disappear;
contain outdated information;
contain incorrect third-party data.

Therefore, discovery should be treated as a data collection process with uncertainty rather than a deterministic lookup.

7.5 Search Engine Scraping

Direct scraping of search engine result pages was not used in the final pipeline because the observed responses were not sufficiently stable or machine-readable.

For production, a supported search API or another legally and technically appropriate discovery mechanism would be preferable.

7.6 Entity Matching

Name and address matching can still produce ambiguous cases.

A production implementation should use additional signals where available, such as:

Companies House Company Number;
official domain;
historical company names;
registered address history;
source type;
document date;
company officers;
other public identifiers.

Ambiguous cases should be sent to manual review instead of being automatically accepted.

8. Scaling to 40,000 Companies

Scaling the POC to approximately 40,000 companies requires a different architecture from a small manual experiment.

The main principle is to minimize expensive operations while maintaining a conservative acceptance policy.

8.1 Proposed Production Pipeline
Companies House
      |
      v
Company identity + metadata
      |
      v
High-confidence discovery sources
      |
      v
Public documents / websites
      |
      v
Third-party sources
      |
      v
VAT candidate extraction
      |
      v
Candidate deduplication
      |
      v
Official VAT verification
      |
      v
Entity matching
      |
      +------> CONFIRMED
      |
      +------> FALSE_POSITIVE
      |
      +------> INVALID
      |
      +------> REVIEW
      |
      +------> NOT_FOUND
      8.2 Discovery Cascade

The discovery process should use sources in descending order of expected reliability and value.

A possible cascade is:

Official company website
Public company documents
Public procurement and tender documents
Reputable business directories and public records
Search APIs
Commercial data providers
Manual review for ambiguous cases

The system should stop querying additional sources once a sufficiently strong candidate has been verified and matched.

This reduces unnecessary crawling and verification costs.

8.3 Candidate Deduplication

The same VAT number may appear in multiple sources and in different formats.

For example:

GB123456789
GB 123 456 789
123456789

should be normalized to:

GB123456789

Candidates should be deduplicated before verification.

The system should also retain source-level information so that the provenance of each candidate remains available.

8.4 Verification Strategy

Verification should be performed only on discovered candidates.

For example, if 40,000 companies produce 2,000 VAT candidates, the verification workload is approximately:

40,000 companies
        |
        v
2,000 candidates
        |
        v
2,000 verification requests

The system should not attempt to enumerate VAT numbers for every company.

8.5 Manual Review

Manual review should be reserved for ambiguous cases.

Examples include:

name partially matches;
address changed recently;
company was recently incorporated;
company has multiple trading names;
VAT is valid but the registered entity differs slightly;
multiple candidate VAT numbers are discovered.

This keeps human effort focused on the cases where automated matching has insufficient confidence.

9. Cost Model

The exact production cost depends on the selected search provider, crawling infrastructure, proxy requirements, commercial data providers and verification API arrangements.

Rather than assuming a single fixed price, the cost model should be expressed as:

Total Cost =
Discovery
+ Crawling / Infrastructure
+ Proxy / Bandwidth
+ Commercial Data
+ VAT Verification
+ Manual Review

The most important scaling variable is the number of VAT candidates generated by discovery.

For 40,000 companies:
| Scenario | Candidate Rate | Candidates | Approx. Verification Workload |
| -------- | -------------: | ---------: | ----------------------------: |
| Low      |             2% |        800 |                           800 |
| Medium   |             5% |      2,000 |                         2,000 |
| High     |            10% |      4,000 |                         4,000 |
These are planning scenarios rather than measured production rates.

The main cost metrics I would monitor are:

Cost per company
Cost per VAT candidate
Cost per verified VAT
Cost per confirmed entity match
Cost per manually reviewed case

This distinction is useful because a discovery source may generate many candidates while producing very few correct entity matches.

A source should therefore be evaluated not only by the number of VAT numbers it produces, but also by the downstream verification and entity-match rate.

10. Monitoring and Quality Control

A production system should continuously monitor both data quality and pipeline health.

Important metrics include:

discovery rate;
candidate rate;
verification success rate;
confirmed entity-match rate;
false-positive rate;
invalid candidate rate;
NOT_FOUND rate;
manual-review rate;
source-level success rate;
average number of candidates per company.

Metrics should also be segmented by source.

For example:

Source A
Candidates: 1,000
Verified: 800
Confirmed: 700

Source B
Candidates: 500
Verified: 450
Confirmed: 100

This allows poor-performing sources to be identified even when their raw candidate volume is high.

Detecting a Wrong Dataset at Scale

Without a complete ground-truth dataset, quality control should rely on multiple signals.

These include:

Random manual audits.
HMRC verification of discovered candidates.
Comparison between independent discovery sources.
Monitoring sudden changes in candidate rates.
Monitoring source-specific failure rates.
Revalidation of previously confirmed VAT numbers.
Detection of unusual VAT duplication patterns.
Review of companies whose registered information changed.

For example, if a source suddenly changes from a normal confirmation rate to almost zero, this could indicate:

a parser failure;
a website structure change;
an API problem;
a blocked crawler;
stale source data.

Monitoring should therefore cover both the data and the collection infrastructure.

11. Keeping the Dataset Current

VAT information can become outdated because companies can change their legal entity, address, registration status or other identifying information.

A production dataset should therefore not be treated as a one-time extraction.

A possible strategy is:

periodically re-check existing VAT records;
prioritize recently changed Companies House entities;
re-run discovery for companies previously marked NOT_FOUND;
re-check records associated with changed addresses or names;
maintain discovery timestamps and verification timestamps.

Each VAT record should retain provenance information such as:

Company Number
VAT Number
Source URL
Source Type
Discovery Date
Verification Date
Verification Result
Entity Match Result
Last Checked

This makes the dataset auditable and allows stale records to be identified.

12. Source Quality and Commercial Suitability

Not every publicly accessible source is suitable for a commercial data product.

A source should be evaluated on:

legal and licensing restrictions;
terms of use;
robots.txt and crawling restrictions;
API availability;
rate limits;
data freshness;
source reliability;
reproducibility;
stability of page structure;
attribution requirements.

A source may be useful for research but unsuitable for production if its terms prohibit automated collection or commercial reuse.

For production, official APIs, licensed datasets and sources with clear commercial usage rights should therefore be preferred where available.

13. UK vs Germany

The UK and Germany illustrate an important distinction between VAT discovery and VAT verification.

United Kingdom

The UK uses a nine-digit VAT registration number, commonly represented with the GB prefix.

The HMRC VAT verification service can verify a VAT number when the number is already known.

The main challenge for this project is therefore discovery: finding a candidate VAT number that can subsequently be verified.

Germany

Germany uses the Umsatzsteuer-Identifikationsnummer (USt-IdNr.).

The German Federal Central Tax Office (BZSt) provides VAT identification number validation services.

The German qualified validation process can compare information associated with the VAT identification number with company information such as name, legal form, location, postcode and street.

This means that the verification stage can provide more entity-level comparison information than a simple VAT-number validity check.

Main Comparison
                 UK                         Germany
----------------------------------------------------------------
VAT identifier   GB VAT number              USt-IdNr.
Discovery        Main challenge             Main challenge
Verification     HMRC                       BZSt
Entity matching  Separate pipeline step     Can use qualified
                                             validation information

The comparison shows that the core challenge remains similar: discovering the identifier is harder than validating a candidate that is already known.

The exact discovery strategy, verification service and legal constraints would need to be adapted for each country.

14. Final Approach

The proof of concept suggests that a reliable VAT dataset should not be built by treating every discovered VAT number as ground truth.

Instead, the recommended architecture is:

Discover
   |
   v
Extract candidate
   |
   v
Normalize
   |
   v
Verify officially
   |
   v
Match entity
   |
   v
Accept or reject

The central design principle is conservative attribution.

A VAT number should enter the final dataset only when:

it has been discovered from an acceptable source;
it has been verified through an authoritative verification mechanism;
the verified entity matches the intended Companies House company.

A failed discovery should remain distinguishable from confirmed absence of VAT registration.

This approach prioritizes data integrity and minimizes the risk of silently introducing incorrect VAT-to-company relationships.

15. Project Structure
vat-identifier-discovery/
│
├── data/
│   ├── sample_89_companies.csv
│   ├── search_queries.csv
│   └── discovery_results.csv
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── data_profile.py
│   ├── vat_extractor.py
│   ├── web_discovery.py
│   ├── company_selector.py
│   ├── search_queries.py
│   ├── results_logger.py
│   ├── web_search.py
│   ├── discovery_runner.py
│   ├── vat_verifier.py
│   ├── poc_summary.py
│   └── create_poc_results.py
│
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md
Main Components

data_loader.py
Loads the Companies House sample dataset.

data_profile.py
Profiles the input data and checks missing values and company statuses.

company_selector.py
Selects companies for the proof of concept.

search_queries.py
Generates search queries for VAT discovery.

web_search.py
Contains the experimental search-engine discovery implementation.

web_discovery.py
Downloads web pages and extracts their text.

vat_extractor.py
Detects and normalizes VAT number candidates.

results_logger.py
Stores discovery and verification results.

discovery_runner.py
Runs the generated search queries.

vat_verifier.py
Normalizes company information and performs entity-level comparison against verification results.

poc_summary.py
Calculates summary statistics from the POC results.

create_poc_results.py
Creates the documented POC result dataset used for evaluation.

16. Key Takeaways

The main findings from the proof of concept are:

VAT discovery and VAT verification must be treated as separate problems.
Companies House is useful as an entity identity source but not as the primary VAT discovery source.
Company Number is a stronger identity key than company name alone.
Search queries should combine company name, Company Number and postcode where available.
Regular expressions can identify VAT candidates but cannot establish validity or ownership.
Third-party sources can be useful for discovery but should not be treated as authoritative.
A VAT number can be valid while belonging to the wrong company.
NOT_FOUND must not be interpreted as proof that a company is not VAT registered.
Entity matching is essential for preventing false-positive VAT assignments.
Scaling requires a source cascade, candidate deduplication, selective verification and monitoring.
A production system should maintain provenance and periodically revalidate existing records.