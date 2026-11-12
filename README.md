# Top 2% Scientist Trends

A light, static HTML website for exploring the published career-long Top 2% Scientist datasets from 2019 through 2026.

Public website: <https://lba191.github.io/Yearly-Top2-scientist-website/>

The generated site contains 1,541,862 annual records and 365,864 conservatively linked scientist profiles. It supports flexible scientist-name search, institution, country, and subfield explorers with complete year-selectable entity rankings and independently scrolling scientist lists, self-citation views, and annual source-workbook downloads. Institution, country, and subfield scientist tables show up to 500 ranked records for the selected release. The November 2022 revision is used as the canonical 2021-metric edition.

## Repository layout

- `dist/` — the complete static website and generated, compressed data shards.
- `scripts/build_full_site_data.py` — rebuilds all static data from the eight source workbooks.
- `scripts/inspect_source_schemas.py` — reports workbook sheets and headers.
- `scripts/verify_full_site_data.py` — checks totals, shards, ranking order, profile references, and search indexes.
- `scripts/test_search_matching.mjs` — checks reordered, joined, partial, and initials-based name queries.
- `data/source/` — optional local staging folder for source workbooks; spreadsheet files are ignored by Git.

The original workbooks are not copied into this repository. See [`data/README.md`](data/README.md) for the expected release paths.

## Preview locally

The pages load compressed data with `fetch`, so open them through a local web server instead of `file://`.

```powershell
python -m http.server 8000 --directory dist
```

Then open <http://localhost:8000/>.

## Rebuild the data

Python 3.11+ and `openpyxl` are required.

```powershell
python scripts/build_full_site_data.py --source-root "path/to/Year TOP2 Scientist List"
python scripts/verify_full_site_data.py
```

Generic `College of Engineering` affiliations are assigned a separate engineering-college label derived from the scientist’s previous named affiliation only when the identity is confidently linked. For example, a linked Cornell or University of Washington record is shown as `Cornell University College of Engineering` or `UW College of Engineering`, separately from its parent university. Unresolved records remain available in scientist results but are excluded from institution counts and rankings. The Overview page reads complete ranked institution, country, and field lists from compressed year-specific files and renders them progressively inside independent scrolling panels.

## Publish with GitHub Pages

1. Push the repository to GitHub.
2. In **Settings → Pages**, choose **GitHub Actions** as the source.
3. The included workflow publishes `dist/` after each push to the main branch.

No application build or server is required. GitHub Pages serves the HTML, CSS, JavaScript, and compressed JSON shards directly.

## Data interpretation

Institution names are retained as published. Spelling changes, abbreviations, faculty-level affiliations, and generic labels can appear as distinct institutions, so institution counts describe listed records rather than institutional performance. Missing years are shown as gaps. Citation indicators are descriptive and should not be treated as a complete measure of scientific quality.
