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

def _rebuild(target_repo: Path) -> int:
    """Refresh reconciliation/target-index.yaml from a target catalog checkout."""
    target_repo = Path(target_repo).resolve()
    ids = set()
    for path in target_repo.rglob("*.yaml"):
        if any(part in {".git", "node_modules", "__pycache__"} for part in path.parts):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"^id:\s*(capabilities:[A-Za-z0-9-]+)\s*$", content, re.M)
        if match:
            ids.add(match.group(1))
    if not ids:
        print(f"no capability record ids found under {target_repo}", file=sys.stderr)
        return 2
    commit = subprocess.run(["git", "-C", str(target_repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    date = subprocess.run(["git", "-C", str(target_repo), "log", "-1", "--format=%cs"],
                          capture_output=True, text=True).stdout.strip()
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
    args = parser.parse_args(argv)

    if args.rebuild:
        return _rebuild(args.rebuild)

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
