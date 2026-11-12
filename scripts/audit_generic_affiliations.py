import gzip
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dist" / "assets" / "data"


def load(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


manifest = load(DATA / "manifest.json")
dictionaries = load(DATA / "dictionaries.json.gz")
institutions = dictionaries["institutions"]
unresolved_id = institutions.index("College of Engineering — unresolved")

recovered_by_institution = Counter()
unresolved_by_year = Counter()
for release in manifest["releases"]:
    year = release["releaseYear"]
    for chunk_index in range(release["chunkCount"]):
        rows = load(DATA / "rankings" / str(year) / f"{chunk_index:03d}.json.gz")
        for row in rows:
            institution_id = row[2]
            if institution_id == unresolved_id:
                unresolved_by_year[year] += 1
            if len(row) > 19 and row[19]:
                recovered_by_institution[institutions[institution_id]] += 1

print(f"Recovered annual ranking rows: {sum(recovered_by_institution.values()):,}")
print(f"Recovered while processing source rows: {manifest['genericAffiliationsRecovered']:,}")
print(f"Unresolved annual ranking rows: {sum(unresolved_by_year.values()):,}")
print(f"Unresolved while processing source rows: {manifest['genericAffiliationsUnresolved']:,}")
assert sum(recovered_by_institution.values()) == manifest["genericAffiliationsRecovered"]
assert sum(unresolved_by_year.values()) == manifest["genericAffiliationsUnresolved"]
print("Unresolved by year:", dict(unresolved_by_year))
print("Most frequent recovered named affiliations:")
for name, count in recovered_by_institution.most_common(20):
    print(f"  {count:>4}  {name}")
print("Requested examples present:")
for term in ("Cornell University College of Engineering", "UW College of Engineering"):
    matches = [(name, count) for name, count in recovered_by_institution.items() if term.casefold() in name.casefold()]
    print(f"  {term}: {matches or 'no exact recovered label'}")
