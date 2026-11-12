from __future__ import annotations

import gzip
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "dist" / "assets" / "data"


def quality(value: str):
    tokens = re.findall(r"[A-Za-z]+", value)
    full = sum(len(token) > 2 and not (len(token) <= 4 and token.upper() == token) for token in tokens)
    proper = sum(token[:1].isupper() and (len(token) == 1 or token[1:].islower()) for token in tokens)
    return full, proper, sum(map(len, tokens)), len(tokens)


def load(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def write(path: Path, value):
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as stream:
        json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))


def main():
    canonical = {}
    for path in sorted((ROOT / "profiles").glob("*.json.gz")):
        shard = load(path)
        for profile_id, profile in shard.items():
            profile["a"] = sorted(profile.get("a", [profile["n"]]), key=quality, reverse=True)
            profile["n"] = profile["a"][0]
            canonical[profile_id] = profile["n"]
        write(path, shard)
    for path in sorted((ROOT / "scientist-search").glob("*.json.gz")):
        entries = load(path)
        for entry in entries:
            entry[1] = canonical[entry[0]]
            entry[8] = sorted(entry[8], key=quality, reverse=True)
        write(path, entries)
    featured_path = ROOT / "featured.json.gz"
    featured = load(featured_path)
    for entry in featured:
        entry[1] = canonical[entry[0]]
    write(featured_path, featured)
    print(f"Canonicalized {len(canonical):,} generated profile names.")


if __name__ == "__main__":
    main()
