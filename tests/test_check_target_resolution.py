"""Tests for the cross-catalog target-resolution gate (CR-CON-05; ES-006)."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_target_resolution.py"
REGISTRY = ROOT / "reconciliation" / "entity-system-registry.yaml"
TARGET_INDEX = ROOT / "reconciliation" / "target-index.yaml"


def _load_module():
    spec = importlib.util.spec_from_file_location("ctr", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=ROOT)


def _write_record(root: Path, rel: dict, rid: str = "dea:concept-test"):
    ents = root / "entities" / "concepts"
    ents.mkdir(parents=True, exist_ok=True)
    (ents / "t.yaml").write_text(
        f"id: {rid}\n"
        "type: Concept\n"
        "name: Test\n"
        "definition: x.\n"
        "lifecycle:\n"
        "  status: active\n"
        "relationships:\n"
        f"  - relationship_type: defines\n    target: {rel['target']}\n    identity_scope: {rel['scope']}\n"
        "provenance:\n"
        "  change_history:\n"
        "    - cr: CR-CON-05\n"
        "      date: '2026-10-27'\n"
        "      change: test.\n")


# --------------------------------------------------------------------------- #
# Live tree
# --------------------------------------------------------------------------- #

def test_live_tree_conformant_strict():
    r = _run("--strict")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CONFORMANT" in r.stdout


def test_live_index_snapshot_pinned():
    mod = _load_module()
    idx = mod._load_target_index()
    snap = idx["snapshot"]
    assert snap["catalog"] == "dea-catalog-business-capabilities"
    assert len(snap["commit"]) == 40
    assert snap["record_count"] == len(idx["records"])


def test_live_records_count():
    mod = _load_module()
    reg = mod._load_registry()
    recs = mod._walk_records(ROOT, reg)
    assert len(recs) >= 14


# --------------------------------------------------------------------------- #
# Rule behaviour (tmp trees)
# --------------------------------------------------------------------------- #

def test_unresolvable_target_fires(tmp_path: Path):
    mod = _load_module()
    _write_record(tmp_path, {"target": "capabilities:capability-nope-zzz999",
                             "scope": "dea-catalog-business-capabilities"})
    findings = mod.evaluate(tmp_path)
    assert [f["rule"] for f in findings] == ["ES-006"]
    assert "does not resolve" in findings[0]["diagnostic"]


def test_resolvable_target_passes(tmp_path: Path):
    mod = _load_module()
    _write_record(tmp_path, {"target": "capabilities:capability-customer-management-f3n8wb",
                             "scope": "dea-catalog-business-capabilities"})
    assert mod.evaluate(tmp_path) == []


def test_wrong_scope_fires_no_index(tmp_path: Path):
    mod = _load_module()
    _write_record(tmp_path, {"target": "capabilities:capability-customer-management-f3n8wb",
                             "scope": "dea-catalog-concepts"})
    findings = mod.evaluate(tmp_path)
    assert [f["rule"] for f in findings] == ["ES-006"]
    assert "no target index" in findings[0]["diagnostic"]


def test_catalog_internal_edges_ignored(tmp_path: Path):
    mod = _load_module()
    ents = tmp_path / "entities" / "concepts"
    ents.mkdir(parents=True)
    (ents / "t.yaml").write_text(
        "id: dea:concept-test\n"
        "type: Concept\n"
        "name: Test\n"
        "definition: x.\n"
        "lifecycle:\n  status: active\n"
        "relationships:\n"
        "  - relationship_type: related-to\n"
        "    target: dea:concept-order\n"
        "    identity_scope: dea-catalog-concepts\n"
        "provenance:\n"
        "  change_history:\n"
        "    - cr: CR-CON-05\n"
        "      date: '2026-10-27'\n"
        "      change: test.\n")
    assert mod.evaluate(tmp_path) == []


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def test_cli_strict_exits_one_on_finding(monkeypatch, tmp_path: Path):
    """--strict exits 1 and prints NON-CONFORMANT when ES-006 fires."""
    import io
    import contextlib
    mod = _load_module()
    _write_record(tmp_path, {"target": "capabilities:capability-nope-zzz999",
                             "scope": "dea-catalog-business-capabilities"})
    findings = mod.evaluate(tmp_path)
    assert findings, "expected ES-006 finding"
    monkeypatch.setattr(mod, "evaluate", lambda root=None: findings)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = mod.main(["--strict"])
    assert rc == 1
    assert "NON-CONFORMANT" in out.getvalue()


def test_cli_json_shape():
    r = _run("--json")
    import json
    data = json.loads(r.stdout)
    assert isinstance(data, list)
