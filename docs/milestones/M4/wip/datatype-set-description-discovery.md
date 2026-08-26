# M4 — DataType SET_DESCRIPTION discovery

**Status:** WIP / NON-NORMATIVE

**Role:** bounded discovery note for `DataType.SET_DESCRIPTION`. This document records AS-IS evidence and first-phase M4 findings only. It does not define the M4 contract, TO-BE architecture, persistence schema, cache contract or concurrency realization.

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 explicitly freezes a TO-BE delta.

## AS-IS flow

Current `SET_DESCRIPTION` performs:

```text
BEGIN UoW

1. lock DataType header FOR NO KEY UPDATE
2. UPDATE datatypes
       SET description = :value
   RETURNING lineage
3. COMMIT
```

The operation does not perform a separate read before the update.

## First-phase findings

`description` is mutable non-semantic metadata and must not be part of the immutable worker-local semantic cache.

For the current M4 data-access/cache audit, the operation is already minimal:

```text
worker semantic cache
    -> no role

PostgreSQL current state
    -> lineage existence
    -> description mutation
```

There is no current denormalization or read-elimination finding for this operation.

## Explicitly deferred point

Whether the explicit header lock remains necessary, can be absorbed by the DML, or must rendezvous with other lineage operations is deliberately deferred to the second M4 phase that will redesign concurrency globally against the complete semantic concurrency matrix.
