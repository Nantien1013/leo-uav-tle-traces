"""Download the CelesTrak Starlink TLE set once and archive it with a timestamp and SHA-256."""
from __future__ import annotations

import argparse
import hashlib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"


def archive_tle(out_dir: str) -> str:
    data = urllib.request.urlopen(URL, timeout=60).read()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    out = Path(out_dir) / f"starlink-{stamp}.tle"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    out.with_suffix(".tle.sha256").write_text(f"{digest}  {out.name}\n{URL}\n")
    return str(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/tle")
    path = archive_tle(ap.parse_args().out)
    with open(path) as f:
        n = sum(1 for l in f if l.startswith("1 "))
    print(f"saved {path}  satellites={n}")
