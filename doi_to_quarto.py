
#!/usr/bin/env python3

"""
Generate Quarto Markdown files from a CSV list of DOIs.
Can be used to populate sections such as the catalogue.
Add a index.csv (containing list of doi's) to the folder and run the script.

Metadata retrieval:
    1. DataCite JSON (primary)
    2. APA bibliography (fallback)

DataCite fields:
    title, authors, date, keywords, abstract,
    type, publisher, rights, DOI

Bibliography fields:
    title, authors, date, citation_source, DOI

Usage:
    pip install requests pyyaml

    python doi_to_quarto.py src/asdac/catalogue/index.csv --output-dir src/asdac/catalogue

"""

import argparse
import csv
import re
import sys
import time

from pathlib import Path

import requests
import yaml


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DOI_URL = "https://doi.org/"

DATACITE_ACCEPT = "application/vnd.datacite.datacite+json"

BIBLIOGRAPHY_ACCEPT = "text/x-bibliography; style=apa"

HEADERS = {
    "User-Agent": "DOI-to-Quarto/1.0 (metadata retrieval)"
}

REQUEST_TIMEOUT = 3


# ---------------------------------------------------------
# DOI metadata retrieval
# ---------------------------------------------------------

def fetch_doi_metadata(doi):
    """
    Fetch DOI metadata.

    First attempts DataCite JSON.
    Falls back to bibliography if crossref JSON is unavailable
    or does not contain usable title metadata.

    Returns a normalized metadata dictionary.
    """

    url = f"{DOI_URL}{doi}"

    # -----------------------------------------------------
    # Attempt 1: DataCite JSON
    # -----------------------------------------------------

    try:

        print("  Trying DataCite JSON...")

        headers = {
            **HEADERS,
            "Accept": DATACITE_ACCEPT
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        # Validate root-level DataCite JSON structure
        if not isinstance(data, dict) or not data.get("titles"):
            raise ValueError("No usable DataCite title metadata")

        metadata = extract_datacite_metadata(data)

        print("  Retrieved metadata using DataCite JSON")

        return metadata

    except (requests.RequestException, ValueError) as error:

        print(f"  DataCite JSON unavailable: {error}")

    # -----------------------------------------------------
    # Attempt 2: Bibliography fallback
    # -----------------------------------------------------

    print("  Trying APA bibliography fallback...")

    headers = {
        **HEADERS,
        "Accept": BIBLIOGRAPHY_ACCEPT
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    citation = response.text.strip()

    if not citation:
        raise ValueError(f"Empty bibliography response for {doi}")

    metadata = parse_bibliography(citation, doi)

    print("  Retrieved metadata using bibliography fallback")

    return metadata


# ---------------------------------------------------------
# DataCite JSON parser
# ---------------------------------------------------------

def extract_datacite_metadata(data):
    """
    Extract metadata from root-level DataCite JSON.

    Expected structure:
        {
            "doi": "...",
            "titles": [...],
            "creators": [...],
            "dates": [...],
            "subjects": [...],
            "descriptions": [...],
            "types": {...},
            "publisher": {...},
            "rightsList": [...]
        }
    """

    # Title
    titles = data.get("titles", [])

    title = (
        titles[0].get("title", "Untitled")
        if titles else "Untitled"
    )

    # Authors / creators
    authors = []

    for creator in data.get("creators", []):

        name = creator.get("name")

        if not name:

            given_name = creator.get("givenName", "")
            family_name = creator.get("familyName", "")

            name = f"{given_name} {family_name}".strip()

        if name:
            authors.append(name)

    # Publication date
    publication_date = None

    for date_entry in data.get("dates", []):

        if date_entry.get("dateType") == "Issued":

            publication_date = date_entry.get("date")
            break

    # Fallback to publication year
    if not publication_date:
        publication_date = data.get("publicationYear")

    if publication_date is not None:
        publication_date = str(publication_date)

    # Keywords / subjects
    keywords = []

    for subject in data.get("subjects", []):

        keyword = subject.get("subject")

        if keyword:
            keywords.append(keyword)

    # Abstract
    abstract = ""

    for description in data.get("descriptions", []):

        if description.get("descriptionType") == "Abstract":

            abstract = description.get("description", "")
            break

    # Resource type
    resource_type = data.get(
        "types", {}
    ).get("schemaOrg")

    # Publisher
    publisher_data = data.get("publisher") or {}

    if isinstance(publisher_data, dict):
        publisher = publisher_data.get("name")
    else:
        publisher = publisher_data

    # Rights / license identifiers
    rights = ""
    
    for i in data.get("rightsList", []):
        if isinstance(i,dict):
            if "rightsIdentifier" in i.keys():
                rights = i['rightsIdentifier']
                break
            elif "rightsUri" in i.keys():
                rights = i['rightsUri']
                break
        else:
            if i not in [None,'']:
                rights = i
    
    # DOI
    doi = data.get("doi", "")

    return {
        "title": title,
        "authors": authors,
        "date": publication_date,
        "keywords": keywords,
        "abstract": abstract,
        "doi": doi,
        "type": resource_type,
        "publisher": publisher,
        "rights": rights,
        "citation_source": None,
        "metadata_source": "datacite"
    }


# ---------------------------------------------------------
# Bibliography parser
# ---------------------------------------------------------


def parse_bibliography(citation, doi):
    """
    Parse APA-style bibliography citations.

    Supports:
      - Journal articles
      - Preprints
      - Books
      - Edited books
      - Citations without journal/source information

    Examples:
      Author (2024). Title. Journal, 10, 20-30. DOI
      Author (2024). Title. DOI
      Author (Eds.). (2019). Title. DOI
    """

    # Normalize whitespace
    citation = re.sub(r"\s+", " ", citation).strip()

    # Remove DOI URL from the citation before parsing
    citation_without_doi = re.sub(
        r"\s*https?://doi\.org/\S+.*$",
        "",
        citation,
        flags=re.IGNORECASE
    ).strip()

    # -----------------------------------------------------
    # Extract authors and year
    # -----------------------------------------------------

    # Supports:
    # Author (2024).
    # Author (Eds.). (2019).
    # Author (Ed.). (2019).

    author_year_pattern = re.compile(
        r"^(?P<authors>.+?)\s+"
        r"(?:\((?P<editor>Ed|Eds)\.\)\s+)?"
        r"\((?P<year>\d{4}[a-z]?)\)\.\s+"
        r"(?P<remaining>.+)$",
        re.IGNORECASE
    )

    match = author_year_pattern.match(citation_without_doi)

    if not match:
        raise ValueError(
            f"Could not extract authors and year for {doi}:\n"
            f"{citation}"
        )

    authors_text = match.group("authors").strip()

    year = match.group("year")

    remaining = match.group("remaining").strip()

    editor_type = match.group("editor")

    # -----------------------------------------------------
    # Extract title and optional source
    # -----------------------------------------------------

    # The title is the first sentence after the year.
    # The remaining text, if present, is journal/source info.

    title_match = re.match(
        r"^(?P<title>.+?)\.\s*(?P<source>.*)$",
        remaining
    )

    if not title_match:
        raise ValueError(
            f"Could not extract title for {doi}:\n"
            f"{citation}"
        )

    title = title_match.group("title").strip()

    source = title_match.group("source").strip()

    # -----------------------------------------------------
    # Parse authors
    # -----------------------------------------------------

    # Normalize APA final-author separator
    authors_text = re.sub(
        r",\s*&\s*",
        ", ",
        authors_text
    )

    authors_text = re.sub(
        r"\s+&\s+",
        ", ",
        authors_text
    )

    author_parts = [
        part.strip()
        for part in authors_text.split(",")
        if part.strip()
    ]

    authors = []

    if len(author_parts) >= 2 and len(author_parts) % 2 == 0:

        for i in range(0, len(author_parts), 2):

            surname = author_parts[i]
            initials = author_parts[i + 1]

            authors.append(
                f"{surname}, {initials}"
            )

    else:
        authors = [authors_text]

    # -----------------------------------------------------
    # Return normalized metadata
    # -----------------------------------------------------

    return {
        "title": title,
        "authors": authors,
        "date": year,
        "keywords": [],
        "abstract": "",
        "doi": doi,
        "type": None,
        "publisher": None,
        "rights": "",
        "citation_source": source or None,
        "editor": editor_type,
        "metadata_source": "bibliography"
    }



# ---------------------------------------------------------
# Filename generation
# ---------------------------------------------------------

def clean_filename(doi):
    """Generate a filesystem-safe filename from a DOI."""

    filename = re.sub(
        r"[^\w\-]+",
        "_",
        doi
    )

    filename = filename.strip("_")

    return filename + ".qmd"


# ---------------------------------------------------------
# Quarto Markdown generation
# ---------------------------------------------------------

def generate_qmd(metadata, output_dir):
    """
    Generate a Quarto Markdown file with YAML frontmatter
    and abstract as Markdown content.
    """

    doi = metadata["doi"]

    doi_url = f"{DOI_URL}{doi}"

    filename = clean_filename(doi)

    output_path = output_dir / filename

    # -----------------------------------------------------
    # YAML frontmatter
    # -----------------------------------------------------

    frontmatter = {
        "title": metadata["title"],
        "author": metadata["authors"],
        "date": metadata["date"],
        "keywords": metadata["keywords"],
        "doi": doi,
        "resource": doi_url,
        "type": metadata["type"],
        "publisher": metadata["publisher"],
        "rights": metadata["rights"],
        "citation_source": metadata["citation_source"]
    }

    # Remove empty fields
    frontmatter = {
        key: value
        for key, value in frontmatter.items()
        if value not in (None, "", [])
    }

    yaml_frontmatter = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False
    )

    # -----------------------------------------------------
    # Markdown content
    # -----------------------------------------------------

    abstract = (
        metadata["abstract"]
        or "No abstract available."
    )

    content = f"""---
{yaml_frontmatter}---

## Abstract

{abstract}

---

**Read more:** [{doi_url}]({doi_url})
"""

    output_path.write_text(
        content,
        encoding="utf-8"
    )

    return output_path


# ---------------------------------------------------------
# CSV input
# ---------------------------------------------------------

def read_dois(csv_file, doi_column):
    """Read DOI identifiers from CSV."""

    dois = []

    with open(
        csv_file,
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        if doi_column not in (reader.fieldnames or []):

            raise ValueError(
                f"CSV does not contain column '{doi_column}'. "
                f"Available columns: {reader.fieldnames}"
            )

        for row in reader:

            doi = (row.get(doi_column) or "").strip()

            # Remove DOI URL prefixes if present
            doi = re.sub(
                r"^https?://(dx\.)?doi\.org/",
                "",
                doi,
                flags=re.IGNORECASE
            )

            if doi:
                dois.append(doi)

    return dois


# ---------------------------------------------------------
# Main processing
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate Quarto Markdown files from DOI metadata "
            "using DataCite JSON with APA bibliography fallback."
        )
    )

    parser.add_argument(
        "csv_file",
        help="CSV file containing DOI identifiers."
    )

    parser.add_argument(
        "--doi-column",
        default="doi",
        help="Name of the DOI column (default: doi)."
    )

    parser.add_argument(
        "--output-dir",
        default="quarto_dois",
        help="Output directory (default: quarto_dois)."
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Quarto files (default: skip existing files)."
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds."
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    dois = read_dois(
        args.csv_file,
        args.doi_column
    )

    print(f"\nFound {len(dois)} DOI(s).\n")

    successful = 0
    failed = []

    for index, input_doi in enumerate(dois, start=1):

        print(f"[{index}/{len(dois)}] Processing {input_doi}")

        try:
            # Determine output filename
            output_path = output_dir / clean_filename(input_doi)

            # Skip existing files unless overwrite is enabled
            if output_path.exists() and not args.overwrite:
                print(f"  SKIPPED (already exists): {output_path}")
                continue

            # Fetch and normalize metadata
            metadata = fetch_doi_metadata(input_doi)

            if not metadata.get("doi"):
                metadata["doi"] = input_doi

            # Generate Quarto file
            output_path = generate_qmd(metadata, output_dir)

            print(f"  Created: {output_path}")
            print(f"  Metadata source: {metadata['metadata_source']}")

            successful += 1

        except Exception as error:
            print(f"  ERROR: {error}", file=sys.stderr)
            failed.append((input_doi, str(error)))

        if index < len(dois):
            time.sleep(args.delay)


    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\n" + "=" * 50)
    print("Processing complete")
    print("=" * 50)

    print(f"Total DOIs: {len(dois)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(failed)}")

    if failed:

        print("\nFailed DOIs:")

        for doi, error in failed:

            print(f"\n  DOI: {doi}")
            print(f"  Error: {error}")


if __name__ == "__main__":
    main()
