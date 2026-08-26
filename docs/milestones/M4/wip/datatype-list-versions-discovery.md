# DataType LIST versions discovery

Status: WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `GET /datatypes/{datatype_id}/versions`. This note focuses on data-access shape, projection size, and cache interaction. It does not redesign locking/concurrency or freeze the public contract.

## AS-IS

The current version-summary DTO exposes:

- `datatype_id`
- `version`
- `revision`
- `status`
- `base_type`

It intentionally does not expose `constraints`; constraints are returned only by the exact-version GET.

The persistence query currently uses a single `OUTER JOIN` from `datatypes` to `datatype_versions`. This allows one statement to distinguish:

- parent DataType absent -> 404;
- parent DataType present but no versions matching the filter/page -> empty list.

The query currently selects all version columns (`*datatype_versions.c`), including `constraints`, even though the summary response does not return them.

## M4 findings

### Keep summary/detail separation

`constraints` is semantically a property of a DataTypeVersion, but it does not need to be present in the collection summary representation. The current contract already follows this useful distinction:

- LIST versions -> summary/catalog information;
- GET exact version -> full exact-version detail including constraints.

### Avoid loading unused constraints

The LIST path should read only the columns needed by its response and pagination logic. Loading the full constraints JSONB for every version is unnecessary I/O and deserialization work.

If `base_type` moves to the stable lineage and is removed from the version-summary DTO, a candidate summary projection becomes:

- `datatype_id`
- `version`
- `revision`
- `status`

The query should therefore select only those version fields plus the minimal parent-existence projection needed to preserve the current one-statement 404-vs-empty-list behavior.

### No cache warm-up that widens the query

LIST versions should not load `constraints` merely to populate immutable semantic cache entries. That would reintroduce the exact payload the optimized summary query is intended to avoid.

Likewise, it should not fetch stable-lineage fields solely for cache warming if they are not otherwise needed by the response.

Working rule:

> Opportunistic cache population is useful only when the required operation already provides the complete immutable information; the cache must not widen an otherwise minimal query.

## Current direction

- Preserve the one-statement distinction between missing parent and empty filtered/page result unless a later design offers a clearly better equivalent.
- Keep LIST versions as a summary endpoint; constraints remain exact-version detail.
- Stop selecting/deserializing `constraints` for the LIST path.
- Evaluate removing `base_type` from `DataTypeVersionSummaryDto` after moving it to the stable lineage.
- Do not use this LIST operation as a reason to load extra data for cache warm-up.

## Open questions

- Final version-summary DTO after the M4 public-contract revision.
- Exact minimal SQL projection while retaining parent-existence semantics and pagination behavior.
