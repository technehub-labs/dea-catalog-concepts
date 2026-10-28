# Change Requests

This directory tracks formal change requests (CRs) for `technehub-labs/dea-catalog-concepts`.

| CR | Title | Status | Summary |
|---|---|---|---|
| [CR-CON-02](CR-CON-02-entity-system-concepts.md) | Entity System Stage 5-6 (Concepts Slice) | Merged |
| [CR-CON-03](CR-CON-03-first-concept-admission.md) | First Concept Record Admission (Registry Enrichment + Pilot Seeding) | Merged |
| [CR-CON-04](CR-CON-04-cross-catalog-defines.md) | Cross-Catalog Defines Wiring (Concepts -> Capabilities) | Merged |
| [CR-CON-05](CR-CON-05-vocabulary-target-resolution.md) | Vocabulary Growth + Cross-Catalog Target-Resolution Gate | Merged |
| [CR-CON-06](CR-CON-06-vocabulary-completion-drift.md) | Vocabulary Completion + Target Drift Detection | **Proposed (this PR)** | Concepts slice of the General Entity System institutionalisation (cross-repo cascade T7). New `reconciliation/entity-system-registry.yaml` (per-repo; generic; no profiles; canonical pattern matches the repo namespace). New `scripts/check_entity_system.py` (5-rule umbrella gate; copied verbatim from `dea-catalog-processes`). New `tests/test_check_entity_system.py` (32 tests; 4 pilot-specific tests made generic; all pass). New `.github/workflows/validate-entity-system.yml` (CI). Live: gate vacuously CONFORMANT. D-004 clean. 118a/b/c authorship gates remain CONFORMANT. Follow-on: T8 legacy ID reconciliation. |
