# Source data

The original annual workbooks are deliberately excluded from Git because they are large source artifacts. The website’s Downloads page links each edition to its authoritative record in the Elsevier Data Repository (dataset DOI `10.17632/btchxktzyw`). The build script currently discovers local originals in the project’s parent data folders used for this study.

For a fresh checkout, either:

1. keep the original annual folders beside this repository and pass their common root with `--source-root`, or
2. place the required career workbooks in `data/source/` and update the release paths in `scripts/build_full_site_data.py`.

The website data under `dist/assets/data/` is generated from the complete career datasets. Files are split and gzip-compressed so the static HTML site remains suitable for GitHub Pages and other static hosts.
