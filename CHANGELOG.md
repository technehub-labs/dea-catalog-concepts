# Changelog

All notable changes to the Concepts Catalog (dea-catalog-concepts) are documented here. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
repository is governed by change requests (`change-requests/`).

## [Unreleased]

### CR-CON-04: Cross-Catalog Defines Wiring (Concepts -> Capabilities)

First cross-catalog edge: `dea:concept-customer` now `defines`
`capabilities:capability-customer-management-f3n8wb` scoped to
`dea-catalog-business-capabilities` (the model's CON -> CAP governance
edge). The registry's `defines` constraint gains
`target_identity_scopes` limited to the capabilities and
business-objects catalogs; a wrong-scope edge fires ES-003.
`dea:concept-order` wiring deferred until an Order/Fulfilment
capability is admitted. 3 new tests (38 entity-system tests total, all
pass); gates remain CONFORMANT under `--strict`. Carrier:
`change-requests/CR-CON-04-cross-catalog-defines.md`.

### CR-CON-03: First Concept Record Admission (Registry Enrichment + Pilot Seeding)

First governed content: the entity-system registry's generic stubs are
enriched into a working Concept profile (required envelope fields,
lifecycle state machine `proposed..retired`, relationship types
`defines` / `broader-than` / `related-to` with source constraints). Two
pilot concept records admitted (`dea:concept-customer`,
`dea:concept-order`), each with full envelope, scoped `related-to` edge,
and CR-named provenance. The entity-system gate now passes
NON-VACUOUSLY (2 records walked, CONFORMANT under `--strict`).
`reconciliation/migration-id-map.yaml` ships as an empty T8-prep stub.
`CONTRIBUTING.md` stale references fixed (repo name, CR link). 3 new
live-record tests (35 entity-system tests total, all pass); 118a/b/c
authorship gates remain CONFORMANT. Carrier:
`change-requests/CR-CON-03-first-concept-admission.md`.

### CR-CON-02: Entity System Stage 5-6 (Concepts Slice)

CON slice of the General Entity System institutionalisation (cross-repo cascade T7 of the umbrella programme). New `reconciliation/entity-system-registry.yaml` (per-repo; generic; no profiles; canonical pattern `^dea:concept-[a-z0-9-]+$`). New `scripts/check_entity_system.py` (5-rule umbrella gate; copied verbatim from `dea-catalog-processes`). New `tests/test_check_entity_system.py` (32 tests; 4 pilot-specific tests made generic for cross-repo portability; all pass). New `.github/workflows/validate-entity-system.yml` (CI). Live: gate vacuously CONFORMANT (no `entities/` directory). D-004 clean. 118a/b/c authorship gates remain CONFORMANT.

### CR-CON-01: Authorship Cardinal Rule (R1, R2) - Org-Wide Propagation Slice

User directive 2026-10-13: "no `Coder` / `Agent` / agent or tool names in any
authorship field of any published artifact". The CR-BP-118 cardinal rules (R1
and R2) are propagated to this repo. New blocking gate
`scripts/check_authorship.py` (CR-BP-118 / AUT-001..003), data-driven from
`reconciliation/authorship-fields.yaml` (allowlist
`{Emmanuel A. Otchere, TechNeHub Labs}`; denylist
`{Coder, Agent, Hermes, Claude, GPT, Cline, OpenAI, MiniMax, MiniMax-M3}`).
The repo's authorship-bearing field set is identical to the 118a baseline
(`**Owner**`, `**Author**` in `change-requests/CR-*.md`); no per-repo
extension is needed. CI wiring: new workflow
`.github/workflows/validate-authorship.yml` runs the gate in `--strict` mode
on every push and PR. 21/21 `test_check_authorship` pass. Carrier:
`change-requests/CR-CON-01-authorship-cardinal-rule.md`.
