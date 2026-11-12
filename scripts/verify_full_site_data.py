from __future__ import annotations

import gzip
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "dist" / "assets" / "data"


def load_json(path: Path):
    if path.suffix == ".gz":
        stream = gzip.open(path, "rt", encoding="utf-8")
    else:
        stream = path.open("rt", encoding="utf-8")
    with stream:
        return json.load(stream)


def main():
    manifest = load_json(DATA_ROOT / "manifest.json")
    assert manifest["schemaVersion"] == 3
    assert manifest["releaseYears"] == list(range(2019, 2027))
    assert manifest["institutionAliasesMerged"] > 0
    assert manifest["genericAffiliationsRecovered"] > 0
    assert manifest["entityShardSize"] == 250
    assert manifest["entityListLimit"] == 500

    total_records = 0
    profile_ids = set()
    profile_rows = 0
    for path in sorted((DATA_ROOT / "profiles").glob("*.json.gz")):
        shard = load_json(path)
        profile_ids.update(shard)
        profile_rows += len(shard)
    assert profile_rows == manifest["profileCount"] == len(profile_ids)

    dictionaries = load_json(DATA_ROOT / "dictionaries.json.gz")
    unresolved_id = dictionaries["institutions"].index("College of Engineering — unresolved")
    assert "College of Engineering" not in dictionaries["institutions"]

    for release in manifest["releases"]:
        year = release["releaseYear"]
        records = []
        paths = sorted((DATA_ROOT / "rankings" / str(year)).glob("*.json.gz"))
        assert len(paths) == release["chunkCount"]
        for path in paths:
            chunk = load_json(path)
            assert len(chunk) <= manifest["chunkSize"]
            records.extend(chunk)
        assert len(records) == release["totalRecords"]
        ranks = [row[6] for row in records]
        assert ranks == sorted(ranks)
        assert all(row[0] in profile_ids for row in records)
        assert all(len(row) >= 20 for row in records)
        overview_institutions = load_json(DATA_ROOT / "overview" / str(year) / "institutions.json.gz")
        overview_countries = load_json(DATA_ROOT / "overview" / str(year) / "countries.json.gz")
        overview_fields = load_json(DATA_ROOT / "overview" / str(year) / "fields.json.gz")
        unresolved_count = sum(row[2] == unresolved_id for row in records)
        assert sum(row[1] for row in overview_institutions) == len(records) - unresolved_count
        assert sum(row[1] for row in overview_countries) == len(records)
        assert sum(row[1] for row in overview_fields) == len(records)
        assert all(row[0] != unresolved_id for row in overview_institutions)
        assert all(item["name"] != "College of Engineering — unresolved" for item in release["topInstitutions"])
        for kind, entity_index in (("institutions", 2), ("countries", 3)):
            expected_counts = Counter(row[entity_index] for row in records)
            indexed_counts = {}
            for path in sorted((DATA_ROOT / "entity-rankings" / kind / str(year)).glob("*.json.gz")):
                shard_id = int(path.name.split(".")[0])
                payload = load_json(path)
                for item_id_text, rows in payload.items():
                    item_id = int(item_id_text)
                    assert item_id // manifest["entityShardSize"] == shard_id
                    assert 0 < len(rows) <= manifest["entityListLimit"]
                    assert all(len(row) == 12 and row[entity_index] == item_id for row in rows)
                    assert [row[6] for row in rows] == sorted(row[6] for row in rows)
                    indexed_counts[item_id] = len(rows)
            assert indexed_counts == {
                item_id: min(count, manifest["entityListLimit"])
                for item_id, count in expected_counts.items()
            }
        subfield_total = 0
        for path in sorted((DATA_ROOT / "subfield-rankings" / str(year)).glob("*.json.gz")):
            rows = load_json(path)
            subfield_id = int(path.name.split(".")[0])
            assert all(row[5] == subfield_id for row in rows)
            ranks = [row[8] if row[8] is not None else 10**12 for row in rows]
            assert ranks == sorted(ranks)
            subfield_total += len(rows)
        assert subfield_total == len(records)
        total_records += len(records)

    assert total_records == manifest["recordCount"]

    search_ids = set()
    for path in sorted((DATA_ROOT / "scientist-search").glob("*.json.gz")):
        rows = load_json(path)
        assert all(len(row) >= 8 and row[7] for row in rows)
        search_ids.update(row[0] for row in rows)
    assert search_ids == profile_ids

    requested = []
    for path in sorted((DATA_ROOT / "profiles").glob("*.json.gz")):
        for profile in load_json(path).values():
            aliases = {name.lower() for name in profile.get("a", [])}
            joined = " ".join(aliases)
            if "ling tim wong" in joined or "l. t. wong" in joined:
                requested.append(profile)
    matching = [profile for profile in requested if any("ling tim wong" in name.lower() for name in profile["a"]) and any("l. t. wong" in name.lower() for name in profile["a"])]
    assert len(matching) == 1
    assert len(matching[0]["h"]) >= 7

    entities = load_json(DATA_ROOT / "entities.json.gz")
    assert len(entities["institutions"]) == len(dictionaries["institutions"])
    assert len(entities["countries"]) == len(dictionaries["countries"])
    assert all(not name.lower().startswith("the ") for name in dictionaries["institutions"])

    print(
        f"Verified {manifest['recordCount']:,} annual records, "
        f"{manifest['profileCount']:,} profiles, {manifest['institutionAliasesMerged']:,} merged "
        f"institution aliases, and {len(manifest['releases'])} releases."
    )


if __name__ == "__main__":
    main()
