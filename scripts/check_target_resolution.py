#!/usr/bin/env python3
"""check_target_resolution.py: cross-catalog target-resolution gate (CR-CON-05).

ES-006 (target resolution): every cross-catalog relationship edge in
this catalog's entity records must dereference against the committed
target index (reconciliation/target-index.yaml), a pinned snapshot of
the live record ids in the target catalog. An edge pointing at a
record that does not exist in the target catalog is a NON-CONFORMANT
finding.

The snapshot pins the target catalog at a commit. Refresh it with:

    python3 scripts/check_target_resolution.py --rebuild \\
        /path/to/dea-catalog-business-capabilities

(in the same PR that wires new edges to newly admitted target
records).

Run: python3 scripts/check_target_resolution.py [--strict] [--json]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "reconciliation" / "entity-system-registry.yaml"
TARGET_INDEX_PATH = REPO_ROOT / "reconciliation" / "target-index.yaml"


def _load_yaml(path: Path) -> dict:
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def _load_registry(path: Path | None = None) -> dict:
    if path is None:
        path = REGISTRY_PATH
    return _load_yaml(path)


def _load_target_index(path: Path | None = None) -> dict:
    if path is None:
        path = TARGET_INDEX_PATH
    return _load_yaml(path)


# --------------------------------------------------------------------------- #
# Record walker (mirrors check_entity_system._walk_records scope)
# --------------------------------------------------------------------------- #

def _walk_records(repo_root: Path, registry: dict) -> list:
    records = []
    file_globs = registry["envelope"]["file_globs"]
    skip_basenames = {"entity-system-registry.yaml", "conformance_report.yaml",
                      "migration-id-map.yaml", "target-index.yaml",
                      "normalization.yaml"}
    for path_glob in file_globs:
        base_name = path_glob.split("*", 1)[0].rstrip("/")
        base = repo_root / base_name if base_name else repo_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in (".yaml", ".yml"):
                continue
            if path.name in skip_basenames:
                continue
            if not fnmatch.fnmatch(str(path.relative_to(repo_root)), path_glob):
                continue
            record = _load_yaml(path)
            if isinstance(record, dict) and record.get("id"):
                records.append((path, record))
    return records


# --------------------------------------------------------------------------- #
# The rule
# --------------------------------------------------------------------------- #

def _cross_catalog_edges(record: dict, registry: dict) -> list:
    """Yield (index, relationship) for edges constrained to target catalogs."""
    constraints = registry["relationships"].get("type_constraints", {})
    edges = []
    relationships = record.get("relationships", [])
    if not isinstance(relationships, list):
        return edges
    for i, rel in enumerate(relationships):
        if not isinstance(rel, dict):
            continue
        rel_type = rel.get("relationship_type", "")
        if "target_identity_scopes" in constraints.get(rel_type, {}):
            edges.append((i, rel))
    return edges


def _check_es_006(records: list, target_index: dict, registry: dict) -> list:
    """ES-006: every cross-catalog edge dereferences against the index."""
    findings = []
    catalog = target_index.get("snapshot", {}).get("catalog", "")
    known_ids = set(target_index.get("records", []) or [])
    for path, record in records:
        record_id = record.get("id", str(path))
        for i, rel in _cross_catalog_edges(record, registry):
            scope = rel.get("identity_scope", "")
            target = rel.get("target", "")
            if catalog and scope != catalog:
                findings.append({
                    "rule": "ES-006", "record_id": record_id,
                    "diagnostic": (f"relationships[{i}]: identity_scope {scope!r} "
                                   f"has no target index (index covers {catalog!r})"),
                })
                continue
            if target not in known_ids:
                findings.append({
                    "rule": "ES-006", "record_id": record_id,
                    "diagnostic": (f"relationships[{i}]: target {target!r} does not "
                                   f"resolve in the target index ({len(known_ids)} records)"),
                })
    return findings


def evaluate(repo_root: Path = REPO_ROOT) -> list:
    registry = _load_registry()
    target_index = _load_target_index()
    records = _walk_records(repo_root, registry)
    return _check_es_006(records, target_index, registry)


# --------------------------------------------------------------------------- #
# Rebuild (snapshot refresh)
# --------------------------------------------------------------------------- #

def _snapshot_ids_from_repo(target_repo: Path) -> tuple[set, str, str]:
    """Extract capability record ids + HEAD commit/date from a checkout."""
    ids = set()
    for path in target_repo.rglob("*.yaml"):
        if any(part in {".git", "node_modules", "__pycache__"} for part in path.parts):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"^id:\s*(capabilities:[A-Za-z0-9-]+)\s*$", content, re.M)
        if match:
            ids.add(match.group(1))
    commit = subprocess.run(["git", "-C", str(target_repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    date = subprocess.run(["git", "-C", str(target_repo), "log", "-1", "--format=%cs"],
                          capture_output=True, text=True).stdout.strip()
    return ids, commit, date


def check_drift(target_repo: Path) -> tuple[list, dict]:
    """ES-007 (drift): compare the pinned snapshot against the live target catalog.

    Findings fire when:
    - a record the snapshot pins has been removed upstream (stale pin;
      a wired target may now dangle), or
    - a wired target is missing from the live catalog (the edge points
    at a removed/renamed record).
    New upstream records are reported as informational (not findings):
    they only matter once an edge is wired to them.
    """
    target_repo = Path(target_repo).resolve()
    live_ids, live_commit, live_date = _snapshot_ids_from_repo(target_repo)
    index = _load_target_index()
    pinned_ids = set(index.get("records", []) or [])
    pinned_commit = index.get("snapshot", {}).get("commit", "")

    registry = _load_registry()
    records = _walk_records(REPO_ROOT, registry)
    wired_targets = set()
    for _, record in records:
        for _, rel in _cross_catalog_edges(record, registry):
            if rel.get("target"):
                wired_targets.add(rel["target"])

    findings = []
    removed = sorted(pinned_ids - live_ids)
    for rid in removed:
        detail = " (WIRED: an edge in this catalog points at it)" if rid in wired_targets else ""
        findings.append({
            "rule": "ES-007", "record_id": rid,
            "diagnostic": (f"pinned target record no longer exists upstream "
                           f"(live HEAD {live_commit[:12]}; pinned {pinned_commit[:12]}){detail}"),
        })
    for rid in sorted(wired_targets - live_ids):
        if rid not in removed:
            findings.append({
                "rule": "ES-007", "record_id": rid,
                "diagnostic": (f"wired target does not exist in the live target catalog "
                               f"(live HEAD {live_commit[:12]})"),
            })

    report = {
        "pinned_commit": pinned_commit,
        "live_commit": live_commit,
        "live_date": live_date,
        "pinned_count": len(pinned_ids),
        "live_count": len(live_ids),
        "added_upstream": sorted(live_ids - pinned_ids),
        "removed_upstream": removed,
        "wired_targets": len(wired_targets),
        "drift": bool(removed or (wired_targets - live_ids)),
    }
    return findings, report


def _rebuild(target_repo: Path) -> int:
    """Refresh reconciliation/target-index.yaml from a target catalog checkout."""
    target_repo = Path(target_repo).resolve()
    ids, commit, date = _snapshot_ids_from_repo(target_repo)
    if not ids:
        print(f"no capability record ids found under {target_repo}", file=sys.stderr)
        return 2
    doc = {
        "snapshot": {
            "catalog": "dea-catalog-business-capabilities",
            "repo": "technehub-labs/dea-catalog-business-capabilities",
            "commit": commit,
            "date": date,
            "record_count": len(ids),
        },
        "records": sorted(ids),
    }
    out = TARGET_INDEX_PATH
    header = (
        "# Target index (CR-CON-05): committed snapshot of the live record ids\n"
        "# in the dea-catalog-business-capabilities catalog, used by the\n"
        "# cross-catalog target-resolution gate. Refresh with:\n"
        "#   python3 scripts/check_target_resolution.py --rebuild /path/to/dea-catalog-business-capabilities\n"
        "# (the snapshot pins the target catalog at a commit; refresh it in the\n"
        "# same PR that wires new edges to newly admitted target records)\n"
    )
    with open(out, "w") as f:
        f.write(header)
        f.write(yaml.safe_dump(doc, sort_keys=False, default_flow_style=False))
    print(f"target index rebuilt: {len(ids)} records @ {commit[:12]} ({date})")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 on any ES-006 finding.")
    parser.add_argument("--json", action="store_true",
                        help="Emit findings as JSON.")
    parser.add_argument("--rebuild", metavar="TARGET_REPO",
                        help="Refresh the target index from a target catalog checkout.")
    parser.add_argument("--check-drift", metavar="TARGET_REPO",
                        help="Compare the pinned snapshot against a live target catalog checkout; "
                             "exit 1 if pinned records were removed upstream or a wired target is missing live.")
    args = parser.parse_args(argv)

    if args.rebuild:
        return _rebuild(args.rebuild)

    if args.check_drift:
        findings, report = check_drift(Path(args.check_drift))
        print(f"Target Drift Check: pinned {report['pinned_commit'][:12]} "
              f"({report['pinned_count']} records) vs live {report['live_commit'][:12]} "
              f"({report['live_count']} records)")
        if report["added_upstream"]:
            print(f"  informational: {len(report['added_upstream'])} new record(s) upstream: "
                  f"{', '.join(report['added_upstream'])}")
        for f in findings:
            print(f"ES-007 {f['record_id']}: {f['diagnostic']}")
        verdict = "NON-CONFORMANT" if findings else "CONFORMANT"
        print(f"Target Drift Check (CR-CON-06; ES-007): {verdict}")
        return 1 if findings else 0

    findings = evaluate()
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        if findings:
            for f in findings:
                print(f"ES-006 {f['record_id']}: {f['diagnostic']}")
        verdict = "NON-CONFORMANT" if findings else "CONFORMANT"
        print(f"Target Resolution Gate (CR-CON-05; ES-006): {verdict}")
    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
