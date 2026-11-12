from __future__ import annotations

import gzip
import json
import shutil
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dist" / "assets" / "data"
SHARD_SIZE = 250
LIST_LIMIT = 500


def load(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as stream:
        json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))


def compact(record):
    return [
        record[0], record[1], record[2], record[3], record[4], record[5],
        record[6], record[7], record[10], record[11], record[14], record[15],
    ]


def main():
    manifest_path = DATA / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target = DATA / "entity-rankings"
    if target.exists():
        shutil.rmtree(target)

    for release in manifest["releases"]:
        year = release["releaseYear"]
        grouped = {"institutions": defaultdict(list), "countries": defaultdict(list)}
        for chunk in range(release["chunkCount"]):
            for record in load(DATA / "rankings" / str(year) / f"{chunk:03d}.json.gz"):
                item = None
                for kind, item_id in (("institutions", record[2]), ("countries", record[3])):
                    if len(grouped[kind][item_id]) < LIST_LIMIT:
                        item = item or compact(record)
                        grouped[kind][item_id].append(item)
        for kind, items in grouped.items():
            shards = defaultdict(dict)
            for item_id, records in items.items():
                shards[item_id // SHARD_SIZE][str(item_id)] = records
            for shard_id, payload in shards.items():
                write(target / kind / str(year) / f"{shard_id}.json.gz", payload)
        print(f"Built entity scientist lists for {year}")

    manifest["entityShardSize"] = SHARD_SIZE
    manifest["entityListLimit"] = LIST_LIMIT
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
