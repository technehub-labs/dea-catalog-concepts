# CR-CON-05: Vocabulary Growth + Cross-Catalog Target-Resolution Gate

| Field | Value |
|-------|-------|
| **CR** | CR-CON-05 |
| **Title** | Vocabulary Growth + Cross-Catalog Target-Resolution Gate |
| **Status** | Proposed (this PR) |
| **Layer** | L1 (Concepts Catalog) |
| **Depends on** | CR-CON-04 |
| **Owner** | Emmanuel A. Otchere |
| **Author** | Emmanuel A. Otchere |
| **Date** | 2026-10-27 |

## 1. Purpose

Two follow-ons from CR-CON-04, landed together:

1. **Vocabulary growth**: 12 new concept records seeded, each wired
   with a `defines` edge to the live capability record(s) in
   `dea-catalog-business-capabilities` whose `business_object` the
   concept defines.
2. **Target-resolution gate (ES-006)**: a new gate
   (`scripts/check_target_resolution.py`) that dereferences every
   cross-catalog edge against a committed snapshot of the target
   catalog's record ids (`reconciliation/target-index.yaml`). An edge
   pointing at a record that does not exist in the target catalog is a
   NON-CONFORMANT finding.

## 2. The seeded concepts (12)

Mapped from the capabilities catalog's `business_object` fields
(verified live at snapshot commit `22e99529b8be`):

`dea:concept-offering`, `dea:concept-partner`, `dea:concept-supplier`,
`dea:concept-asset`, `dea:concept-risk`, `dea:concept-regulation`,
`dea:concept-information`, `dea:concept-insight`,
`dea:concept-workforce`, `dea:concept-facility`,
`dea:concept-legal-matter`, `dea:concept-change`.

Deferred (composite / compound business objects needing a definition
decision): Market/Customer, Asset/Information, Enterprise Performance,
Organization Structure, Technology, Technology Service, Operations,
Plan, Workforce Plan, Continuity, Idea, Enterprise, Decision,
Acquisition Cycle, Financial Resource (already covered by two
capabilities and needs a governance read on single vs. multiple
`defines` edges).

## 3. The target index (snapshot design)

`reconciliation/target-index.yaml` is a committed snapshot of the 33
live record ids in `dea-catalog-business-capabilities`, pinned at
commit `22e99529b8be` (2026-10-27). CI runs offline; the snapshot
keeps the gate hermetic while pinning the target state. Refresh with
`--rebuild <target-repo-checkout>` in the same PR that wires edges to
newly admitted target records.

## 4. The rule (ES-006)

For every record edge whose relationship type has
`target_identity_scopes` in the registry (currently `defines`):

- the edge's `identity_scope` must name the indexed catalog;
- the edge's `target` must resolve in the index.

Findings: `ES-006` (blocking under `--strict`). The gate supports
`--strict`, `--json`, and `--rebuild`. It is registered as the
per-type gate for `Concept` in the entity-system registry (ES-005
now verifies its existence).

## 5. Repository changes

| Path | Status | Notes |
|---|---|---|
| `entities/concepts/{offering,partner,supplier,asset,risk,regulation,information,insight,workforce,facility,legal-matter,change}.yaml` | NEW (12) | Seeded concepts, each with verified `defines` edge |
| `reconciliation/target-index.yaml` | NEW | Pinned snapshot (33 records @ `22e99529b8be`) |
| `scripts/check_target_resolution.py` | NEW | ES-006 gate (+ `--rebuild`) |
| `tests/test_check_target_resolution.py` | NEW | 9 tests |
| `.github/workflows/validate-target-resolution.yml` | NEW | CI: gate under `--strict` + tests |
| `reconciliation/entity-system-registry.yaml` | MOD | `per_type_gates` registers the Concept gate |
| `change-requests/CR-CON-05-...md` | NEW | This file (the carrier CR) |
| `change-requests/README.md` | MOD | New row |
| `CHANGELOG.md` | MOD | [Unreleased] entry |

## 6. Acceptance criteria

- AC-01 12 new concepts seeded; every `defines` target exists in the
  target index (gate CONFORMANT under `--strict`).
- AC-02 The ES-006 gate fires on unresolvable targets and wrong
  scopes (tested); catalog-internal edges are ignored (tested).
- AC-03 The `--rebuild` path regenerates the snapshot idempotently
  from a target checkout (verified against the live clone).
- AC-04 The entity-system gate (ES-001..ES-005) remains CONFORMANT,
  with ES-005 now verifying the registered per-type gate exists.
- AC-05 All tests pass: 59 existing + 9 new = 68.
- AC-06 D-004 clean across all new/modified files; 118a/b/c
  authorship gates CONFORMANT.

## 7. Out-of-scope follow-ons

- The deferred compound business objects (see section 2) pending a
  definition read.
- A scheduled CI job that detects target-catalog drift (snapshot
  stale vs. live target tree) and opens a refresh PR.
- Extending the index design to `dea-catalog-business-objects` once
  that catalog admits records.

## 8. Cross-references

- **CR-CON-04**: wired the first cross-catalog edge; identified this
  gate as the follow-on.
- **dea-catalog-business-capabilities @ 22e99529b8be**: the pinned
  target snapshot source (33 capability records).
- **CR-BP-122 SS5 / ES-005**: per-type gate delegation; this gate is
  the registered Concept per-type gate.
