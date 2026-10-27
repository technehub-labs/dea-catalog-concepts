# CR-CON-04: Cross-Catalog Defines Wiring (Concepts -> Capabilities)

| Field | Value |
|-------|-------|
| **CR** | CR-CON-04 |
| **Title** | Cross-Catalog Defines Wiring (Concepts -> Capabilities) |
| **Status** | Proposed (this PR) |
| **Layer** | L1 (Concepts Catalog) |
| **Depends on** | CR-CON-03 |
| **Owner** | Emmanuel A. Otchere |
| **Author** | Emmanuel A. Otchere |
| **Date** | 2026-10-27 |

## 1. Purpose

CR-CON-03 identified wiring real `defines` edges to CAP/BO records as a
follow-on. This CR lands the first cross-catalog edge: the
`dea:concept-customer` concept now defines the Customer Management
business capability in `dea-catalog-business-capabilities` (the
model's CON -> CAP governance edge per the OpenDEAM v0.4.0 pointer).

## 2. Registry change

`relationships.type_constraints.defines` gains
`target_identity_scopes: [dea-catalog-business-capabilities,
dea-catalog-business-objects]`. A `defines` edge whose
`identity_scope` is not one of the registered target catalogs now
fires ES-003. `broader-than` and `related-to` remain catalog-internal
(no target-scope constraint).

## 3. Record change

`entities/concepts/customer.yaml` gains:

- a `defines` edge to
  `capabilities:capability-customer-management-f3n8wb` scoped to
  `dea-catalog-business-capabilities` (target verified live in that
  catalog; the record is `lifecycle_status: active`)
- a `provenance.change_history` entry naming this CR

`dea:concept-order` keeps its catalog-internal edges only: the
capabilities catalog has no Order/Fulfilment capability record yet, so
a `defines` edge would point at nothing. Wiring it is deferred to when
that capability is admitted.

## 4. Verification

The gate validates the cross-catalog edge shape (canonical type,
source type, target scope). The gate does not resolve cross-catalog
targets at check time; target existence was verified manually against
the live `dea-catalog-business-capabilities` tree.

## 5. Repository changes

| Path | Status | Notes |
|---|---|---|
| `reconciliation/entity-system-registry.yaml` | MOD | `defines` target_identity_scopes |
| `entities/concepts/customer.yaml` | MOD | `defines` edge + provenance entry |
| `tests/test_check_entity_system.py` | MOD | 3 new tests (38 total) |
| `change-requests/CR-CON-04-...md` | NEW | This file (the carrier CR) |
| `change-requests/README.md` | MOD | New row |
| `CHANGELOG.md` | MOD | [Unreleased] entry |

## 6. Acceptance criteria

- AC-01 The registry constrains `defines` target scopes to the CAP and
  BO catalogs; wrong-scope edges fire ES-003 (tested).
- AC-02 The live `dea:concept-customer` record carries exactly one
  `defines` edge to the Customer Management capability, scoped to
  `dea-catalog-business-capabilities` (tested).
- AC-03 The gate remains CONFORMANT under `--strict` with the wired
  edge.
- AC-04 All 38 entity-system tests and 21 authorship tests pass.
- AC-05 D-004 clean across all new/modified files.
- AC-06 The 118a/b/c authorship gates remain CONFORMANT.

## 7. Out-of-scope follow-ons

- Wiring `dea:concept-order` once an Order/Fulfilment capability is
  admitted to `dea-catalog-business-capabilities`.
- Cross-catalog target resolution (live dereference of `defines`
  targets against the target catalog's tree) as a per-type gate.
- BO-catalog edges once `dea-catalog-business-objects` admits records.

## 8. Cross-references

- **CR-CON-03**: seeded the pilot concepts and identified this
  follow-on.
- **capabilities:capability-customer-management-f3n8wb**: the live
  target record in `dea-catalog-business-capabilities`
  (`entities/v1-alpha/customer-management-f3n8wb/`).
- **ADR-0004**: OpenDEAM v0.4.0 (CON -> CAP `defines`, governance).
