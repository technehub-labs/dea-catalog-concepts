# OpenDEA Concepts (dea-catalog-concepts)

> DEA catalog for **Concepts** — OpenDEAM v0.4.0 (ADR-0004; renamed from `dea-catalog-glossary`, absorbs `dea-catalog-taxonomy`).

## Concept (`CON`)

- **Entity id:** `dea:entity-concept`
- **Allocation:** semantic-dimension (orthogonal allocator) · scope layers L1–L5
- **Status:** proposed

A canonical, definable unit of meaning (business term or classification node)
that other entities link to via `defined_by`. Merged from **Glossary Term** +
**Taxonomy Node** in v0.4.0 (ADR-0004 D2) — a queryable concept graph, not a
static glossary document. Not allocated to a layer/building block — it belongs
to the orthogonal semantic dimension.

## Relationships (from the OpenDEAM model)

- **CON → CAP** — defines (governance, 0..N:0..N)
- **CON → BO** — defines (governance, 0..N:0..N)

## Allocation contract

This repo's `metamodel-pointer.yaml` is validated in CI against the pinned
OpenDEAM root model (`v0.4.0`) via the reusable
`validate-against-model.yml` workflow. Drift fails CI.

Content (entity instances) lands when the entity promotes from
`proposed` to `planned`/`scaffold` per the model lifecycle.

## License

Apache 2.0 — see [LICENSE](./LICENSE) and [NOTICE](./NOTICE).
