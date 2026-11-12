from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import load_workbook


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "dist" / "assets" / "data"
CHUNK_SIZE = 5000
ENTITY_SHARD_SIZE = 250
ENTITY_LIST_LIMIT = 500

RELEASE_PATHS = [
    (2019, 2018, "August 2019 data-update/Table-S4-career-2018.xlsx"),
    (2020, 2019, "August 2020 data-update/Table-S6-career-2019.xlsx"),
    (2021, 2020, "August 2021 data-update/Table_1_Authors_career_2020_wopp_extracted_202108.xlsx"),
    (2022, 2021, "November 2022 data-update/Table_1_Authors_career_2021_pubs_since_1788_wopp_extracted_202209b.xlsx"),
    (2023, 2022, "October 2023 data-update/Table_1_Authors_career_2022_pubs_since_1788_wopp_extracted_202310.xlsx"),
    (2024, 2023, "August 2024 data-update/Table_1_Authors_career_2023_pubs_since_1788_wopp_extracted_202408.xlsx"),
    (2025, 2024, "August 2025 data-update/Table_1_Authors_career_2024_pubs_since_1788_wopp_extracted_202508.xlsx"),
    (2026, 2025, "August 2026 data-update/Table_1_Authors_career_2025_pubs_since_1788_wopp_extracted_202608.xlsx"),
]


def clean(value):
    if value is None or isinstance(value, float) and math.isnan(value):
        return None
    return value


def number(value, digits=None):
    value = clean(value)
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return round(value, digits) if digits is not None and isinstance(value, float) else value


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def person_name_key(value: str) -> str:
    """Normalize a person name and recognize 'Surname, Given' ordering."""
    value = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip()
    if value.count(",") == 1:
        surname, given = (part.strip() for part in value.split(",", 1))
        if surname and given:
            return normalize(f"{given} {surname}")
    return normalize(value)


def person_display(value: str) -> str:
    """Use a consistent Given Surname display when the source uses one comma."""
    value = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip()
    if value.count(",") == 1:
        surname, given = (part.strip() for part in value.split(",", 1))
        if surname and given:
            return f"{given} {surname}"
    return value


def person_forms(value: str) -> dict:
    """Create search/linking forms while retaining evidence about written initials."""
    display = person_display(value)
    normalized = normalize(display)
    tokens = normalized.split()
    raw_tokens = re.findall(r"[A-Za-z0-9]+", display)
    if len(tokens) < 2:
        return {"exact": normalized, "compact": normalized.replace(" ", ""), "initials": None}
    surname = tokens[-1]
    given_tokens = tokens[:-1]
    raw_given = raw_tokens[:-1]
    initials = ""
    for token, raw_token in zip(given_tokens, raw_given):
        if len(raw_token) <= 4 and raw_token.isalpha() and raw_token.upper() == raw_token:
            initials += normalize(raw_token)
        else:
            initials += token[0]
    return {
        "exact": normalized,
        "compact": normalized.replace(" ", ""),
        "initials": f"{surname}|{initials}" if initials else None,
    }


def person_alias_keys(value: str) -> list[tuple[str, str]]:
    forms = person_forms(value)
    keys = [("exact", f"e:{forms['exact']}"), ("compact", f"c:{forms['compact']}")]
    if forms["initials"]:
        keys.append(("initials", f"i:{forms['initials']}"))
    return keys


def name_quality(value: str) -> tuple[int, int, int, int]:
    """Prefer a full written name over an initials-only source variant."""
    tokens = re.findall(r"[A-Za-z]+", person_display(value))
    full_tokens = sum(len(token) > 2 and not (len(token) <= 4 and token.upper() == token) for token in tokens)
    proper_tokens = sum(token[:1].isupper() and (len(token) == 1 or token[1:].islower()) for token in tokens)
    return full_tokens, proper_tokens, sum(map(len, tokens)), len(tokens)


def institution_key(value: str) -> str:
    key = normalize(value)
    return re.sub(r"^the\s+", "", key)


def institution_display(value: str) -> str:
    value = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip(" ,.;")
    return re.sub(r"^the\s+", "", value, flags=re.IGNORECASE)


def is_generic_institution(value: str) -> bool:
    """Detect a source label that lacks a named parent institution."""
    return institution_key(value) in {"college of engineering"}


def engineering_college_display(parent: str) -> str:
    """Create a separate engineering-college label from a linked parent affiliation."""
    parent = institution_display(parent)
    key = institution_key(parent)
    if "college of engineering" in key or "school of engineering" in key or "faculty of engineering" in key:
        return parent
    preferred = {
        "cornell university": "Cornell University College of Engineering",
        "university of washington": "UW College of Engineering",
    }
    return preferred.get(key, f"{parent} College of Engineering")


def find_metric(headers, pattern):
    return next((header for header in headers if re.fullmatch(pattern, header)), None)


def write_gzip_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as stream:
        json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))


class Dictionary:
    def __init__(self, key_function=None, display_function=None):
        self.values = []
        self.index = {}
        self.key_function = key_function or (lambda value: value)
        self.display_function = display_function or (lambda value: value)
        self.raw_values = set()

    def add(self, value):
        value = str(value or "Not listed")
        self.raw_values.add(value)
        key = self.key_function(value)
        if key not in self.index:
            self.index[key] = len(self.values)
            self.values.append(self.display_function(value))
        return self.index[key]


def similarity(cluster, record):
    score = 0
    if cluster["field"] == record["field"]:
        score += 4
    if cluster["subfield"] == record["subfield"]:
        score += 2
    if cluster["country"] == record["country"]:
        score += 2
    if cluster["institution"] == record["institution"]:
        score += 3
    first_a, first_b = cluster["first"], record["first"]
    if first_a is not None and first_b is not None:
        difference = abs(first_a - first_b)
        score += 3 if difference <= 1 else 1 if difference <= 3 else -3 if difference > 8 else 0
    return score


def choose_cluster(candidates, record, release_year):
    eligible = []
    for cluster, match_kind in candidates.values():
        if release_year in cluster["years"]:
            continue
        score = similarity(cluster, record)
        if match_kind == "initials":
            first_close = cluster["first"] is not None and record["first"] is not None and abs(cluster["first"] - record["first"]) <= 2
            first_exact = cluster["first"] is not None and cluster["first"] == record["first"]
            adjacent_release = any(abs(year - release_year) == 1 for year in cluster["years"])
            country_or_continuity = cluster["country"] == record["country"] or (
                first_exact and adjacent_release and cluster["subfield"] == record["subfield"]
            )
            evidence_ok = (
                cluster["institution"] == record["institution"]
                and country_or_continuity
                and first_close
                and (cluster["field"] == record["field"] or cluster["subfield"] == record["subfield"])
            )
            if not evidence_ok or score < 11:
                continue
        elif match_kind == "compact" and score < 8:
            continue
        elif match_kind == "exact" and score < 6:
            continue
        eligible.append((score, {"exact": 3, "compact": 2, "initials": 1}[match_kind], cluster))
    eligible.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if not eligible:
        return None, bool(candidates)
    if len(eligible) > 1 and eligible[0][1] == eligible[1][1] and eligible[0][0] - eligible[1][0] <= 1:
        return None, True
    return eligible[0][2], False


def new_profile_id(record, sequence):
    signature = "|".join(
        [record["name_key"], str(record["first"] or ""), str(record["field"]), str(record["institution"]), str(sequence)]
    )
    return hashlib.sha1(signature.encode("utf-8")).hexdigest()[:16]


def top_items(counter, dictionary, limit=12):
    return [{"name": dictionary.values[item], "count": count} for item, count in counter.most_common(limit)]


def compact_entity_record(record):
    """Keep only the columns used in institution and country scientist tables."""
    return [
        record[0], record[1], record[2], record[3], record[4], record[5],
        record[6], record[7], record[10], record[11], record[14], record[15],
    ]


def write_entity_rankings(output, release_year, ranking_records):
    grouped = {"institutions": defaultdict(list), "countries": defaultdict(list)}
    for record in ranking_records:
        compact = None
        for kind, item_id in (("institutions", record[2]), ("countries", record[3])):
            if len(grouped[kind][item_id]) < ENTITY_LIST_LIMIT:
                compact = compact or compact_entity_record(record)
                grouped[kind][item_id].append(compact)
    for kind, items in grouped.items():
        shards = defaultdict(dict)
        for item_id, records in items.items():
            shards[item_id // ENTITY_SHARD_SIZE][str(item_id)] = records
        for shard_id, payload in shards.items():
            write_gzip_json(output / "entity-rankings" / kind / str(release_year) / f"{shard_id}.json.gz", payload)


def main():
    parser = argparse.ArgumentParser(description="Build the complete static data layer for the Top 2% Scientist Trends website.")
    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Directory containing the annual source-workbook folders described in data/README.md.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    institutions = Dictionary(institution_key, institution_display)
    unresolved_institution_id = institutions.add("College of Engineering — unresolved")
    countries, fields, subfields = Dictionary(), Dictionary(), Dictionary()
    profiles = {}
    clusters_by_alias = defaultdict(list)
    entity_history = {
        "institutions": defaultdict(list),
        "countries": defaultdict(list),
        "fields": defaultdict(list),
        "subfields": defaultdict(list),
    }
    entity_history["institutions"][unresolved_institution_id] = []
    releases = []
    featured = []
    ambiguous_links = 0
    generic_affiliations_recovered = 0
    generic_affiliations_unresolved = 0

    for release_year, metric_year, relative_path in RELEASE_PATHS:
        path = source_root / relative_path
        if not path.exists():
            raise FileNotFoundError(path)
        print(f"Reading {release_year}: {path.name}", flush=True)
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet_name = "Data" if "Data" in workbook.sheetnames else "Career"
        sheet = workbook[sheet_name]
        rows = sheet.iter_rows(values_only=True)
        headers = [str(value) if value is not None else "" for value in next(rows)]
        index = {header: position for position, header in enumerate(headers)}
        citation_key = find_metric(headers, r"nc\d{4}")
        h_key = find_metric(headers, r"h\d{2}")
        hm_key = find_metric(headers, r"hm\d{2}")
        papers_key = find_metric(headers, r"np60\d{2}")
        counts = {"institutions": Counter(), "countries": Counter(), "fields": Counter(), "subfields": Counter()}
        ranking_records = []
        subfield_records = defaultdict(list)
        record_count = 0

        def get(row, key):
            return clean(row[index[key]]) if key and key in index else None

        for row in rows:
            name = get(row, "authfull")
            if not name:
                continue
            raw_institution = get(row, "inst_name") or "Institution not listed"
            generic_institution = is_generic_institution(raw_institution)
            institution_id = unresolved_institution_id if generic_institution else institutions.add(raw_institution)
            country_id = countries.add(str(get(row, "cntry") or "n/a").upper())
            field_id = fields.add(get(row, "sm-field") or get(row, "name22") or "Field not listed")
            subfield_id = subfields.add(get(row, "sm-subfield-1") or get(row, "name1") or "Subfield not listed")
            first_year = number(get(row, "firstyr"))
            identity = {
                "name": str(name),
                "name_key": person_name_key(name),
                "institution": institution_id,
                "country": country_id,
                "field": field_id,
                "subfield": subfield_id,
                "first": first_year,
            }
            candidates = {}
            for match_kind, alias_key in person_alias_keys(name):
                for candidate in clusters_by_alias[alias_key]:
                    existing = candidates.get(candidate["id"])
                    if existing is None or {"exact": 3, "compact": 2, "initials": 1}[match_kind] > {"exact": 3, "compact": 2, "initials": 1}[existing[1]]:
                        candidates[candidate["id"]] = (candidate, match_kind)
            cluster, uncertain = choose_cluster(candidates, identity, release_year)
            affiliation_inferred = False
            if cluster is not None and generic_institution and cluster["institution"] != unresolved_institution_id:
                parent_institution = institutions.values[cluster["institution"]]
                institution_id = institutions.add(engineering_college_display(parent_institution))
                identity["institution"] = institution_id
                affiliation_inferred = True
            if generic_institution:
                if affiliation_inferred:
                    generic_affiliations_recovered += 1
                else:
                    generic_affiliations_unresolved += 1
            if cluster is None:
                if uncertain:
                    ambiguous_links += 1
                profile_id = new_profile_id(identity, len(profiles))
                cluster = {
                    "id": profile_id,
                    "name": person_display(name),
                    "aliases": set(),
                    "first": first_year,
                    "institution": institution_id,
                    "country": country_id,
                    "field": field_id,
                    "subfield": subfield_id,
                    "years": set(),
                    "history": [],
                }
                profiles[profile_id] = cluster
            display_name = person_display(name)
            cluster["aliases"].add(display_name)
            for _, alias_key in person_alias_keys(name):
                if cluster not in clusters_by_alias[alias_key]:
                    clusters_by_alias[alias_key].append(cluster)
            profile_id = cluster["id"]
            cluster["years"].add(release_year)
            if name_quality(display_name) > name_quality(cluster["name"]):
                cluster["name"] = display_name
            cluster.update(institution=institution_id, country=country_id, field=field_id, subfield=subfield_id)
            history_row = [
                release_year, metric_year, institution_id, country_id, field_id, subfield_id,
                number(get(row, "rank")), number(get(row, "rank (ns)")),
                number(get(row, "rank sm-subfield-1")), number(get(row, "rank sm-subfield-1 (ns)")),
                number(get(row, citation_key)), number(get(row, h_key)), number(get(row, hm_key), 3),
                number(get(row, papers_key)), number(get(row, "c"), 6), number(get(row, "c (ns)"), 6),
                number(get(row, "self%"), 6), first_year, number(get(row, "lastyr")), affiliation_inferred,
            ]
            cluster["history"].append(history_row)
            ranking_record = [profile_id, str(name), *history_row[2:]]
            ranking_records.append(ranking_record)
            subfield_records[subfield_id].append(ranking_record)
            if release_year == RELEASE_PATHS[-1][0] and record_count < 100:
                featured.append([profile_id, person_display(name), institution_id, country_id, field_id, subfield_id])
            if institution_id != unresolved_institution_id:
                counts["institutions"][institution_id] += 1
            counts["countries"][country_id] += 1
            counts["fields"][field_id] += 1
            counts["subfields"][subfield_id] += 1
            record_count += 1
            if record_count % 50000 == 0:
                print(f"  {record_count:,} rows", flush=True)
        workbook.close()

        ranking_records.sort(key=lambda item: (item[6] is None, item[6] if item[6] is not None else 10**12))
        write_entity_rankings(output, release_year, ranking_records)
        ranking_search = defaultdict(list)
        for position, ranking_record in enumerate(ranking_records):
            chunk_number, row_in_chunk = divmod(position, CHUNK_SIZE)
            name_key = person_name_key(ranking_record[1])
            initials = {token[0] for token in name_key.split() if token}
            for initial in initials or {"_"}:
                ranking_search[initial if initial.isalnum() else "_"].append(
                    [name_key, ranking_record[1], chunk_number, row_in_chunk]
                )
        for chunk_number, start in enumerate(range(0, len(ranking_records), CHUNK_SIZE)):
            write_gzip_json(
                output / "rankings" / str(release_year) / f"{chunk_number:03d}.json.gz",
                ranking_records[start:start + CHUNK_SIZE],
            )
        for subfield_id, records in subfield_records.items():
            records.sort(key=lambda item: (item[8] is None, item[8] if item[8] is not None else 10**12))
            write_gzip_json(output / "subfield-rankings" / str(release_year) / f"{subfield_id}.json.gz", records)
        chunk_count = math.ceil(len(ranking_records) / CHUNK_SIZE)

        dictionaries = {"institutions": institutions, "countries": countries, "fields": fields, "subfields": subfields}
        for kind, counter in counts.items():
            ranked = counter.most_common()
            write_gzip_json(
                output / "overview" / str(release_year) / f"{kind}.json.gz",
                [[item_id, count] for item_id, count in ranked],
            )
            for rank, (item_id, count) in enumerate(ranked, start=1):
                entity_history[kind][item_id].append([release_year, count, rank, round(count / record_count, 8)])
        releases.append(
            {
                "releaseYear": release_year,
                "metricYear": metric_year,
                "totalRecords": record_count,
                "chunkCount": chunk_count,
                "topInstitutions": top_items(counts["institutions"], institutions),
                "topCountries": top_items(counts["countries"], countries),
                "topFields": top_items(counts["fields"], fields),
                "topSubfields": top_items(counts["subfields"], subfields),
            }
        )
        for initial, entries in ranking_search.items():
            write_gzip_json(output / "ranking-search" / str(release_year) / f"{initial}.json.gz", entries)
        print(f"  complete: {record_count:,} rows, {chunk_count} ranking chunks", flush=True)

    write_gzip_json(
        output / "dictionaries.json.gz",
        {"institutions": institutions.values, "countries": countries.values, "fields": fields.values, "subfields": subfields.values},
    )
    write_gzip_json(
        output / "entities.json.gz",
        {kind: [[item_id, history] for item_id, history in values.items()] for kind, values in entity_history.items()},
    )
    write_gzip_json(output / "featured.json.gz", featured)

    search_groups = defaultdict(list)
    profile_groups = defaultdict(list)
    for profile_id, profile in profiles.items():
        entry = [
            profile_id, profile["name"], profile["institution"], profile["country"], profile["field"], profile["subfield"], len(profile["history"])
        ]
        aliases = sorted(profile["aliases"], key=name_quality, reverse=True)
        canonical_name = person_name_key(profile["name"])
        entry.append(canonical_name)
        entry.append(aliases)
        initials = {token[0] for alias in aliases for token in person_name_key(alias).split() if token}
        for initial in initials or {"_"}:
            search_groups[initial if initial.isalnum() else "_"].append(entry)
        profile_groups[profile_id[:2]].append(profile_id)
    for initial, entries in search_groups.items():
        entries.sort(key=lambda item: item[7])
        write_gzip_json(output / "scientist-search" / f"{initial}.json.gz", entries)
    for prefix, ids in profile_groups.items():
        payload = {
            profile_id: {
                "n": profiles[profile_id]["name"],
                "a": sorted(profiles[profile_id]["aliases"], key=name_quality, reverse=True),
                "h": profiles[profile_id]["history"],
            }
            for profile_id in ids
        }
        write_gzip_json(output / "profiles" / f"{prefix}.json.gz", payload)

    manifest = {
        "schemaVersion": 3,
        "datasetType": "career-long",
        "releaseYears": [item[0] for item in RELEASE_PATHS],
        "releases": releases,
        "recordCount": sum(item["totalRecords"] for item in releases),
        "profileCount": len(profiles),
        "ambiguousLinksSeparated": ambiguous_links,
        "institutionAliasesMerged": len(institutions.raw_values) - len(institutions.values),
        "genericAffiliationPolicy": "Generic College of Engineering labels are assigned a distinct engineering-college name derived from a linked prior named affiliation when possible; unresolved records are excluded from institution rankings.",
        "genericAffiliationsRecovered": generic_affiliations_recovered,
        "genericAffiliationsUnresolved": generic_affiliations_unresolved,
        "chunkSize": CHUNK_SIZE,
        "entityShardSize": ENTITY_SHARD_SIZE,
        "entityListLimit": ENTITY_LIST_LIMIT,
        "note": "Complete annual career datasets. Name order, joined names, and evidence-backed initials variants are linked; uncertain identities remain separate.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Built {len(profiles):,} profiles from {manifest['recordCount']:,} annual rows in {output}", flush=True)


if __name__ == "__main__":
    main()
