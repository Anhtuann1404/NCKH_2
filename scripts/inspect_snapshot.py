"""Inspect a local HTML snapshot. No classification or network access."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from phishing.features import FEATURE_VERSION, extract
from phishing.preprocessing import PREPROCESSING_VERSION, prepare_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="HTTP(S) page URL; not fetched")
    parser.add_argument("--html", type=Path, help="Local UTF-8 HTML file; omitted for URL-only")
    arguments = parser.parse_args()
    html = arguments.html.read_text(encoding="utf-8") if arguments.html else None
    try:
        features = extract(prepare_snapshot(arguments.url, html))
    except (ValueError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps({
        "status": "feature_inspection_only",
        "preprocessing_version": PREPROCESSING_VERSION,
        "feature_version": FEATURE_VERSION,
        "features": asdict(features),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
