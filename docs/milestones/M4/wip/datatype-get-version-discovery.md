# DataType GET exact version discovery

Status: WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `GET /datatypes/{datatype_id}/versions/{version}`. This note does not redesign concurrency or freeze the public contract.

## AS-IS

The current exact-version DTO exposes:

- `datatype_id`
- `version`
- `revision`
- `status`
- `base_type`
- `constraints`

The persistence path is already a single exact-version read.

## M4 findings

### `base_type` belongs to the stable lineage

The DataType architecture guarantees one PrimitiveType for the whole lineage; cross-primitive evolution is not supported. Therefore `base_type` is semantically stable lineage state rather than exact-version state.

Candidate relational direction:

- move `base_type` from `datatype_versions` to `datatypes`;
- expose `base_type` from the DataType lineage DTO;
- evaluate removing `base_type` from the exact-version DTO rather than adding a join merely to preserve the current projection.

No join from exact-version reads to the lineage is assumed or required by this discovery.

A candidate exact-version representation therefore becomes:

- `datatype_id`
- `version`
- `revision`
- `status`
- `constraints`

This keeps the exact-version GET as a simple one-row read from version state.

### Cache implications

The exact-version GET cannot generally be served only from the semantic cache because current state is still required:

- `status` is mutable (`DRAFT -> PUBLISHED -> DEPRECATED`);
- `revision` is mutable for DRAFT versions;
- `constraints` are mutable for DRAFT versions.

For PUBLISHED or DEPRECATED versions, the semantic payload is immutable and may be placed in worker-local cache when it is already available from the required read. DRAFT exact semantics must never be cached as immutable knowledge.

Compiled validator structures may be built either opportunistically during such a read or lazily on first semantic consumer. That compilation policy remains open as a performance decision.

## Current direction

- Keep the exact-version GET at one PostgreSQL statement.
- Do not introduce a lineage join solely to reproduce `base_type` on the version DTO.
- Treat removal of `base_type` from the exact-version DTO as the preferred API direction to evaluate when the M4 contract is frozen.
- Never cache DRAFT exact semantics.
- PUBLISHED/DEPRECATED semantic payload may opportunistically populate the immutable local cache without an extra database round trip.

## Open questions

- Final public DTO shape after the M4 contract revision.
- Eager versus lazy compilation of immutable version validators.
- Exact cache object shape and lifecycle.
