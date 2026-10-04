"""Build a restricted 32-row pilot from verified stored source files; never render/fetch pages.

Run after recovering the exact technical20 API bytes and downloading the pinned
train shard listed in source_manifest.json. Source mapping/labels stay under data/raw.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import secrets

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phishing.annotation import BlindSample, extract_safe_view_content, export_blind_view
from phishing.preprocessing.urls import normalize_url


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build(technical_path, extra_path):
    import pyarrow.parquet as pq
    import tldextract
    import pyarrow
    import platform

    summary = read_json(ROOT / "data/source_audit/phreshphish/pilot_summary.json")
    technical_bytes = technical_path.read_bytes()
    if sha(technical_bytes) != summary["pilot_sha256"]:
        raise ValueError("Technical20 bytes do not match the archived pilot checksum.")
    technical = [item["row"] for item in json.loads(technical_bytes)["rows"]]
    if len(technical) != 20 or sum(r["label"] == "phish" for r in technical) != 8:
        raise ValueError("Expected the original 8 phishing + 12 benign technical rows.")
    source = read_json(ROOT / "configs/source_manifest.json")
    shard = next(f for f in source["files"] if f["file_name"] == extra_path.name)
    if sha(extra_path.read_bytes()) != shard["source_metadata_lfs_sha256"]:
        raise ValueError("Extra train shard checksum mismatch.")
    dictionary = read_json(ROOT / "configs/dictionary_v1.json")
    # Offline bundled PSL; private suffixes group shared hosting conservatively.
    extractor = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=True)
    candidates = pq.read_table(extra_path, columns=["url", "html", "label", "sha256", "date", "lang"]).to_pylist()
    used = {sha((r["url"] + "\0" + r["html"]).encode()) for r in technical}
    extra = []
    for offset, row in enumerate(candidates):
        identity = sha((row["url"] + "\0" + row["html"]).encode())
        if row["label"] == "phish" and identity not in used and 0 < len(row["html"]) <= 2_000_000:
            used.add(identity)
            extra.append((offset, row))
            if len(extra) == 12:
                break
    if len(extra) != 12:
        raise ValueError("Verified train shard does not supply 12 unique extra phishing rows.")
    raw_directory = ROOT / "data/raw/pilot"
    order_path = raw_directory / "blind_order.json"
    if order_path.exists():
        order = read_json(order_path)
    else:
        order = list(range(32))
        secrets.SystemRandom().shuffle(order)
        order_path.write_text(json.dumps(order), encoding="utf-8", newline="\n")
    if sorted(order) != list(range(32)):
        raise ValueError("Invalid restricted blinding permutation.")
    source_rows = technical + [row for _, row in extra]
    samples, mapping = [], []
    for index, source_index in enumerate(order):
        row = source_rows[source_index]
        sid = f"PILOT-{index + 1:03d}"
        # Full pilot overlap is explicit; main 30% sampling is a separate manifest.
        raw_url = row["url"].strip()
        candidate_url = "https:" + raw_url if raw_url.startswith("//") else raw_url
        if "://" not in candidate_url:
            candidate_url = "https://" + candidate_url
        normalized = normalize_url(candidate_url)
        text, structure = extract_safe_view_content(row["html"], normalized, max_html_characters=2_000_000)
        blind = BlindSample(sid, normalized, text, structure, random_subset=True, codebook_version=dictionary["version"])
        samples.append(blind)
        domain = extractor(row["url"]).top_domain_under_public_suffix
        if not domain:
            raise ValueError("Cannot establish a conservative pilot domain group.")
        mapping.append({"sample_id": sid, "source_label": row["label"],
                        "source_sha256": row["sha256"], "url_sha256": sha(row["url"].encode()),
                        "html_sha256": sha(row["html"].encode()), "group_id": domain,
                        "source_split": "train", "source_revision": None if source_index < 20 else source["revision"],
                        "source_path": "technical20_api.json" if source_index < 20 else shard["relative_path"],
                        "source_row_offset": source_index if source_index < 20 else extra[source_index - 20][0]})
    raw_directory.mkdir(parents=True, exist_ok=True)
    mapping_path = raw_directory / "source_mapping.json"
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    output = ROOT / "data/annotations/blind_view_pilot_real.json"
    export_blind_view(samples, output, dataset_id="REAL-PILOT-32-V1", dataset_type="real_pilot_pending_review",
                      purpose="Real pilot: human annotation only after B/D acceptance; not official test.")
    manifest = {"dataset_id": "REAL-PILOT-32-V1", "is_synthetic": False, "sample_count": 32,
                "source_class_counts": {"phish": 20, "benign": 12}, "ready_for_annotation": False,
                "codebook_version": dictionary["version"], "codebook_status": dictionary["status"],
                "dictionary_version": dictionary["version"], "dictionary_status": dictionary["status"],
                "codebook_sha256": sha((ROOT / "docs/CODEBOOK_V1.md").read_bytes()),
                "dictionary_sha256": sha((ROOT / "configs/dictionary_v1.json").read_bytes()),
                "blind_view_path": str(output.relative_to(ROOT)), "blind_view_sha256": sha(output.read_bytes()),
                "restricted_source_mapping_path": str(mapping_path.relative_to(ROOT)),
                "restricted_source_mapping_sha256": sha(mapping_path.read_bytes()),
                "restricted_blind_order_sha256": sha(order_path.read_bytes()),
                "technical20": {"rows_api_revision_pinned": False, "sha256_matches_original_archive": True,
                                "batch_sha256": sha(technical_bytes), "pinned_shard_mapping_status": "unresolved"},
                "extra12": {"revision": source["revision"], "path": shard["relative_path"],
                            "locally_verified_shard_sha256": sha(extra_path.read_bytes()),
                            "selection_rule": "first 12 source-phish unique URL+HTML, 1..2000000 HTML chars, shard row order"},
                "agreement_scope": "full_pilot_overlap_not_main_30_percent", "official_test_used": False,
                "missing_scheme_rule": "prepend https:// (or https: for protocol-relative), retain raw URL only in source",
                "grouping": {"library": "tldextract", "version": tldextract.__version__,
                             "network_PSL_fetch": False, "include_private_suffixes": True,
                             "PSL_snapshot_sha256": sha((Path(tldextract.__file__).parent / ".tld_set_snapshot").read_bytes())},
                "runtime": {"python": platform.python_version(), "pyarrow": pyarrow.__version__},
                "acceptance": {"B": "pending", "D": "pending"}}
    (ROOT / "configs/pilot_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    # This registry is restricted: contains source labels and domain membership.
    registry = {"training_blocked": True, "registry_status": "content_and_domain_exclusion_available_mapping_pending",
                "training_block_reason": "Technical20 pinned-shard mapping and B/D review still pending.",
                "total_excluded_samples": 32, "exclusions": [{"exclusion_id": "REAL-PILOT-32-V1",
                 "action": "permanently_exclude_samples_and_groups_from_train_val_test", "samples": mapping}]}
    (raw_directory / "exclusion_registry_real.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    public_registry_path = ROOT / "data/exclusion_registry.json"
    public_registry = read_json(public_registry_path)
    public_registry["exclusions"] = [entry for entry in public_registry["exclusions"] if entry["exclusion_id"] not in {"EXCL-PILOT-EXTRA-12", "EXCL-REAL-PILOT-32"}]
    def public_hashes(record):
        return {key: record[key] for key in ("url_sha256", "html_sha256")} | {"group_sha256": sha(record["group_id"].encode())}
    for old in public_registry["exclusions"][0]["samples"]:
        for key in ("sample_id", "url_sha256", "html_sha256", "group_sha256"):
            old.pop(key, None)
    public_registry["exclusions"][0]["raw_batch_checksum_recovered"] = True
    hashes = [public_hashes(r) for r in mapping]
    hashes.sort(key=lambda r: r["url_sha256"])
    public_registry["exclusions"].append({"exclusion_id": "EXCL-REAL-PILOT-32", "n_samples": 32,
        "mapping_status": "unresolved_source_mapping", "rows_api_revision_pinned": False,
        "samples": hashes, "reason": "Union of all 32 pilot rows, no per-ID/class/source-batch mapping published."})
    public_registry.update(total_excluded_samples=32, total_excluded_entries=2, training_blocked=True)
    public_registry["counting_note"] = "32 unique rows; legacy 20 are a subset of the real32 entry, not 52 rows."
    public_registry_path.write_text(json.dumps(public_registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Built 32 real-source rows (20 phish/12 benign); restricted view/mapping/registry; B/D review pending.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--technical-json", type=Path, required=True)
    parser.add_argument("--extra-parquet", type=Path, required=True)
    args = parser.parse_args()
    build(args.technical_json, args.extra_parquet)
