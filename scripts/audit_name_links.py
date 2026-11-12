from __future__ import annotations

import gzip
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "dist" / "assets" / "data"


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def main():
    linked = 0
    different_compact = 0
    alias_counts = Counter()
    examples = []
    named = []
    for path in sorted((ROOT / "profiles").glob("*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            shard = json.load(stream)
        for profile_id, profile in shard.items():
            aliases = profile.get("a", [])
            alias_counts[len(aliases)] += 1
            if len(aliases) > 1:
                linked += 1
                forms = {compact(name) for name in aliases}
                if len(forms) > 1:
                    different_compact += 1
                    if len(examples) < 30:
                        examples.append((profile_id, aliases, len(profile["h"])))
            search = " ".join(aliases).lower()
            compact_aliases = {compact(name) for name in aliases}
            is_requested_wong = "lingtimwong" in compact_aliases or "ltwong" in compact_aliases
            if is_requested_wong or "jian lei niu" in search or "jianlei niu" in search:
                named.append((profile_id, aliases, len(profile["h"]), profile["h"]))
    print(f"Profiles with multiple source names: {linked:,}")
    print(f"Profiles linked across different compact spellings: {different_compact:,}")
    print("Alias-count distribution:", alias_counts.most_common(10))
    print("Initials-link examples:")
    for item in examples:
        print(item)
    print("Requested-name matches:")
    for profile_id, aliases, years, history in named:
        print(profile_id, aliases, years)
        for row in history:
            print("  ", row)


if __name__ == "__main__":
    main()
