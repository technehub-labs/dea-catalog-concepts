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


# --------------------------------------------------------------------------- #
# Drift check (CR-CON-06; ES-007)
# --------------------------------------------------------------------------- #

def _write_target_repo(root: Path, ids: list):
    repo = root / "target"
    ents = repo / "entities" / "v1-alpha"
    ents.mkdir(parents=True)
    for i, rid in enumerate(ids):
        (ents / f"r{i}.yaml").write_text(f"id: {rid}\nname: x\n")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
    return repo


def test_drift_clean_when_live_matches_pin(tmp_path: Path):
    mod = _load_module()
    idx = mod._load_target_index()
    repo = _write_target_repo(tmp_path, idx["records"])
    findings, report = mod.check_drift(repo)
    assert findings == []
    assert report["drift"] is False
    assert report["pinned_count"] == report["live_count"]


def test_drift_fires_on_removed_pinned_record(tmp_path: Path):
    mod = _load_module()
    idx = mod._load_target_index()
    live = [r for r in idx["records"] if r != "capabilities:capability-customer-management-f3n8wb"]
    repo = _write_target_repo(tmp_path, live)
    findings, report = mod.check_drift(repo)
    es_007 = [f for f in findings if f["rule"] == "ES-007"]
    assert any("customer-management" in f["record_id"] for f in es_007)
    assert report["drift"] is True
    assert "capabilities:capability-customer-management-f3n8wb" in report["removed_upstream"]


def test_drift_removed_wired_target_flagged(tmp_path: Path):
    mod = _load_module()
    idx = mod._load_target_index()
    live = [r for r in idx["records"] if r != "capabilities:capability-customer-management-f3n8wb"]
    repo = _write_target_repo(tmp_path, live)
    findings, _ = mod.check_drift(repo)
    hit = [f for f in findings if f["record_id"] == "capabilities:capability-customer-management-f3n8wb"]
    assert hit and "WIRED" in hit[0]["diagnostic"]


def test_drift_added_upstream_informational_only(tmp_path: Path):
    mod = _load_module()
    idx = mod._load_target_index()
    live = list(idx["records"]) + ["capabilities:capability-brand-new-aaa111"]
    repo = _write_target_repo(tmp_path, live)
    findings, report = mod.check_drift(repo)
    assert findings == []
    assert report["drift"] is False
    assert "capabilities:capability-brand-new-aaa111" in report["added_upstream"]
