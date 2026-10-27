# CR-CON-03: First Concept Record Admission (Registry Enrichment + Pilot Seeding)

| Field | Value |
|-------|-------|
| **CR** | CR-CON-03 |
| **Title** | First Concept Record Admission (Registry Enrichment + Pilot Seeding) |
| **Status** | Proposed (this PR) |
| **Layer** | L1 (Concepts Catalog) |
| **Depends on** | CR-CON-01, CR-CON-02 |
| **Owner** | Emmanuel A. Otchere |
| **Author** | Emmanuel A. Otchere |
| **Date** | 2026-10-27 |

## 1. Purpose

CR-CON-02 left the entity-system gate vacuously CONFORMANT (0 entity
records; empty registry blocks). This CR moves the catalog from
governance-only to governed content by:

1. Enriching `reconciliation/entity-system-registry.yaml` from generic
   stubs to a working Concept profile.
2. Admitting the first two pilot concept records under `entities/`.
3. Shipping the T8-prep stub `reconciliation/migration-id-map.yaml`.
4. Housekeeping: fixing stale `CONTRIBUTING.md` references (repo name,
   CR link).

## 2. Registry enrichment

- `envelope.profiles` gains the `Concept` profile with required fields
  `id, type, name, definition, lifecycle, provenance` and
  `lifecycle_state_field: lifecycle.status`.
- `lifecycle.valid_states` becomes
  `[proposed, planned, scaffold, active, deprecated, retired]` with
  terminal state `retired` and a linear transition table
  (`deprecated` may reactivate to `active`).
- `relationships.canonical_types` becomes `[defines, broader-than,
  related-to]` with per-type source constraints (all `Concept`).
  `part-of` remains forbidden. `defines` is the canonical type for the
  model's CON -> CAP and CON -> BO governance edges (per the OpenDEAM
  v0.4.0 metamodel pointer).

## 3. Pilot records

Two seed concepts, admitted directly at `lifecycle.status: active`
(pilot admission; the state machine governs subsequent transitions):

- `dea:concept-customer` (`entities/concepts/customer.yaml`)
- `dea:concept-order` (`entities/concepts/order.yaml`)

Both carry the full envelope, a `related-to` edge scoped to this
catalog via `identity_scope`, and a `provenance.change_history` entry
naming this CR.

## 4. T8 prep

`reconciliation/migration-id-map.yaml` ships as an empty stub. The repo
is in the pre-migration namespace state (canonical and legacy
prefixes both `dea:`); when the umbrella T8 follow-on promotes the
org-wide canonical namespace, each record's id move lands here.

## 5. Repository changes

| Path | Status | Notes |
|---|---|---|
| `entities/concepts/customer.yaml` | NEW | Pilot concept record |
| `entities/concepts/order.yaml` | NEW | Pilot concept record |
| `reconciliation/entity-system-registry.yaml` | MOD | Concept profile, lifecycle machine, relationship types |
| `reconciliation/migration-id-map.yaml` | NEW | T8-prep stub (empty) |
| `tests/test_check_entity_system.py` | MOD | 3 new live-record tests (35 total) |
| `CONTRIBUTING.md` | MOD | Fix stale repo name and CR link |
| `change-requests/CR-CON-03-...md` | NEW | This file (the carrier CR) |
| `change-requests/README.md` | MOD | New row |
| `CHANGELOG.md` | MOD | [Unreleased] entry |

## 6. Acceptance criteria

- AC-01 The registry declares a Concept profile; the gate is
  data-driven from it (no code change to the gate script).
- AC-02 The gate passes non-vacuously: 2 records walked, verdict
  CONFORMANT under `--strict`.
- AC-03 All 35 entity-system tests and 21 authorship tests pass.
- AC-04 D-004 (no en/em-dash, no U+2E3B) is clean across all
  new/modified files.
- AC-05 The 118a/b/c authorship gates remain CONFORMANT.
- AC-06 `metamodel-pointer.yaml` is untouched (allocation unchanged;
  the validate-allocation pin still applies).

## 7. Out-of-scope follow-ons

- Populating `per_type_gates` (requires a Concept-specific per-type
  gate script; ES-005 currently delegates none).
- Wiring `defines` edges to real CAP/BO records once those catalogs
  admit records (cross-catalog `identity_scope` values).
- T8: filling `reconciliation/migration-id-map.yaml` at org-wide
  namespace promotion.

## 8. Cross-references

- **CR-CON-02**: the entity-system slice this CR makes non-vacuous.
- **CR-BP-121..125**: the 6-stage institutionalisation in
  `dea-catalog-processes`.
- **ADR-0004**: OpenDEAM v0.4.0 (Concept merge; `defined_by` edges).
