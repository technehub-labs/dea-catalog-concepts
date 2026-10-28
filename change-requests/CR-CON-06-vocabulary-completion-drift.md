# CR-CON-06: Vocabulary Completion + Target Drift Detection

| Field | Value |
|-------|-------|
| **CR** | CR-CON-06 |
| **Title** | Vocabulary Completion + Target Drift Detection |
| **Status** | Proposed (this PR) |
| **Layer** | L1 (Concepts Catalog) |
| **Depends on** | CR-CON-05 |
| **Owner** | Emmanuel A. Otchere |
| **Author** | Emmanuel A. Otchere |
| **Date** | 2026-10-27 |

## 1. Purpose

The two CR-CON-05 follow-ons, landed together:

1. **Vocabulary completion**: the 15 remaining business objects from
   the capabilities catalog are seeded (29 concepts total), closing
   the `business_object` coverage map.
2. **Target drift detection (ES-007)**: a scheduled CI job clones the
   target catalog at its current HEAD and compares the live record ids
   against the pinned snapshot, catching upstream removals/renames
   that would leave wired edges dangling.

## 2. Vocabulary completion (15 new concepts)

CR-CON-05 deferred the compound business objects pending a definition
read. Resolution applied here:

- Compound objects map to a single concept with a definition that
  names the compound sense (`market` for Marketing's
  Market/Customer; `information-asset` for Security's
  Asset/Information).
- Multi-capability objects get multiple `defines` edges
  (`financial-resource` defines both Financial Resource Management
  and Financial Stewardship).

Seeded: `market`, `information-asset`, `financial-resource`,
`enterprise-performance`, `organization-structure`, `technology`,
`technology-service`, `operations`, `plan`, `enterprise`, `decision`,
`continuity`, `idea`, `acquisition-cycle`, `workforce-plan`.

All 29 capability records' `business_object` fields are now covered
by a concept with a resolvable `defines` edge (verified: the 33-record
target index, gate CONFORMANT).

## 3. Drift detection (ES-007)

`scripts/check_target_resolution.py` gains `--check-drift
<TARGET_REPO>`: extract live record ids from a target checkout,
compare against the pinned snapshot, and fire ES-007 when:

- a pinned record was removed upstream (stale pin), or
- a wired target is missing from the live catalog.

New upstream records are informational only (they matter once wired).
A removed record that an edge in this catalog points at is flagged
`WIRED` in the diagnostic.

New workflow `validate-target-drift.yml` runs the check weekly
(Mondays 06:00 UTC) and on demand (`workflow_dispatch`); it clones
the target catalog in CI and fails the job on drift.

## 4. Repository changes

| Path | Status | Notes |
|---|---|---|
| `entities/concepts/{market,information-asset,financial-resource,enterprise-performance,organization-structure,technology,technology-service,operations,plan,enterprise,decision,continuity,idea,acquisition-cycle,workforce-plan}.yaml` | NEW (15) | Vocabulary completion |
| `scripts/check_target_resolution.py` | MOD | `check_drift()` + `--check-drift` CLI + shared snapshot extractor |
| `.github/workflows/validate-target-drift.yml` | NEW | Weekly scheduled drift job |
| `tests/test_check_target_resolution.py` | MOD | 4 new drift tests (13 total in file) |
| `change-requests/CR-CON-06-...md` | NEW | This file (the carrier CR) |
| `change-requests/README.md` | MOD | New row |
| `CHANGELOG.md` | MOD | [Unreleased] entry |

## 5. Acceptance criteria

- AC-01 All 29 concepts' `defines` targets resolve in the pinned
  index (gate CONFORMANT under `--strict`).
- AC-02 The drift check fires on removed pinned records and flags
  wired targets (tested); added-upstream records are informational
  (tested).
- AC-03 The `--check-drift` CLI exits 1 on drift, 0 when clean
  (verified against a live clone: CONFORMANT).
- AC-04 All tests pass: 68 existing + 4 new = 72.
- AC-05 D-004 clean across all new/modified files; 118a/b/c
  authorship gates CONFORMANT; entity-system and allocation gates
  unchanged and CONFORMANT.

## 6. Out-of-scope follow-ons

- Wiring `dea:concept-order` (still awaiting an Order/Fulfilment
  capability upstream).
- BO-catalog edges once `dea-catalog-business-objects` admits
  records (the index design generalises: one index per target
  catalog).
- A drift job that opens a refresh PR automatically (the weekly job
  fails loudly; refresh is manual via `--rebuild`).

## 7. Cross-references

- **CR-CON-05**: introduced the pinned-snapshot design and listed
  both follow-ons.
- **dea-catalog-business-capabilities @ 22e99529b8be**: the pinned
  target snapshot (33 records); unchanged by this CR.
