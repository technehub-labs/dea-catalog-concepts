# Changelog

All notable changes to the Concepts Catalog (dea-catalog-concepts) are documented here. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
repository is governed by change requests (`change-requests/`).

## [Unreleased]

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
