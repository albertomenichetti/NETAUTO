# M4 WIP — Stable ObjectTemplate ancestry cache

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Purpose

This note records the worker-local cache shape used to answer stable ObjectTemplate lineage compatibility questions in O(1), initially motivated by batch Object ATTACH and reusable by other M4 consumers.

The persistent source is the denormalized stable closure:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

The closure includes the reflexive row for every ObjectTemplate lineage:

```text
(A, A, 0)
```

Therefore even a root template with no parent has at least one ancestry fact.

## Required runtime lookup

The semantic operation is:

```text
cache[source_template_id][target_template_id]
```

with O(1) lookup semantics:

```text
TRUE
    source is target itself or a descendant of target

FALSE
    the source ancestry row is fully READY and target is absent

MISS
    the source ancestry row has not yet been fully loaded
```

Conceptually:

```text
cache[EthernetInterface][NetworkInterface] -> TRUE
cache[EthernetInterface][Device]           -> TRUE
cache[EthernetInterface][Disk]             -> FALSE
```

The implementation may use a hash map keyed by source whose value contains a READY marker plus a hash-set/hash-map of positive target ids. It does not need to materialize an O(N^2) matrix of explicit negative entries. The externally useful semantics remain `cache[source][target]` in O(1).

## Completeness rule

A negative answer is authoritative only when the complete ancestry of `source_template_id` is READY.

Therefore:

```text
source not READY
    -> MISS

source READY + target present
    -> TRUE

source READY + target absent
    -> FALSE
```

There is no DB fallback after a READY negative result. ObjectTemplate parent lineage is stable, so a complete cached source ancestry cannot later gain a new ancestor.

## Cold fill

For all distinct missing source ids in one consumer operation, fill in bounded bulk:

```sql
SELECT
    descendant_template_id,
    ancestor_template_id,
    depth
FROM object_template_ancestry
WHERE descendant_template_id = ANY(:missing_source_ids);
```

The result is grouped by `descendant_template_id`; each source is loaded completely, then marked READY. The consumer resumes the same O(1) cache-hit lookup path.

There must be no N+1 query per source or per source/target pair.

## Reflexive invariant

Every existing ObjectTemplate lineage must yield at least:

```text
cache[A][A] -> TRUE
```

because persistence materializes:

```text
(A, A, 0)
```

If a cold load for an existing lineage returns ancestry data without the required reflexive row, this is invariant corruption rather than a legitimate negative compatibility result.

## ATTACH usage

For batch ATTACH, Object stable lineage knowledge is prepared cache-first as:

```text
ObjectLineageCache[object_id] -> template_id
```

ATTACH collects the DISTINCT requested child `template_id` values from that READY stable Object-lineage knowledge and evaluates each against the current materialized slot `target_template_id`.

```text
READY positive
    -> compatible

READY negative
    -> fail the batch immediately; DB cannot reveal a new stable ancestor

MISS
    -> accumulate source id for one bounded bulk fill
```

All ancestry MISS sources required by the operation are filled together from `object_template_ancestry`; each source receives its full denormalized neighborship/ancestor set before being marked READY. There is no recursive ObjectTemplate traversal on the ATTACH data plane and no N+1 query per child/source/target pair.

The Object-lineage cache is not defined by this file and does not make this cache authoritative for current Object existence. This file owns only stable ObjectTemplate ancestry knowledge.

## Lifecycle / invalidation

The cache contains only stable lineage ancestry. No TTL or distributed invalidation protocol is required for normal ObjectTemplate version lifecycle changes. PUBLISHED/DEPRECATED version transitions do not affect stable lineage ancestry.

Creation of a new descendant lineage does not change the ancestry of already existing descendant source ids; it creates a new source row to be loaded when first needed.
