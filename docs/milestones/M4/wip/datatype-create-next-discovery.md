# M4 — DataType CREATE_NEXT discovery

**Status:** WIP / NON-NORMATIVE

**Role:** bounded discovery note for `DataType.CREATE_NEXT`. This document records AS-IS evidence, findings and working hypotheses only. It does not define the M4 contract, TO-BE architecture, persistence schema, cache contract or concurrency realization.

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 explicitly freezes a TO-BE delta.

## 1. Scope

This note intentionally covers only the points discussed while analysing `DataType.CREATE_NEXT`:

- semantic eligibility and immutability of the exact source version;
- use of worker-local cache for the source semantic snapshot;
- separation between immutable source knowledge and current version-set state;
- role of the stable DataType header lock in version allocation and lineage lifetime.

The exact final SQL shape, alternative version-allocation schemes and wider DataType lifecycle redesign remain open.

## 2. AS-IS flow

Current `DataType.CREATE_NEXT`:

```text
BEGIN UoW

lock DataType header          FOR NO KEY UPDATE
lock source DataTypeVersion   FOR KEY SHARE
load exact source
require source status in {PUBLISHED, DEPRECATED}
read max(existing version) + 1
construct DRAFT revision 1 by cloning source semantics
insert new exact version
commit
```

The current source payload includes `base_type` and `constraints`; the new DRAFT clones both.

## 3. Source semantic snapshot is immutable knowledge

A valid source is always either:

```text
PUBLISHED
DEPRECATED
```

Both lifecycle states carry an immutable exact semantic snapshot. In addition, `PUBLISHED -> DEPRECATED` does not change `CREATE_NEXT` source eligibility because both states remain valid sources.

Therefore the source semantic payload can be treated as immutable worker-local knowledge.

Working direction:

```text
cache[(datatype_id, source_version)]
    -> exact canonical semantic contract
```

On cache hit, `CREATE_NEXT` need not reload the exact source merely to obtain its semantic payload.

On cache miss, the general DataType cold-load path may load the stable lineage plus all exact PUBLISHED/DEPRECATED semantic versions, compile their runtime representations and populate the cache.

A cache entry is not proof that the current lineage still exists; PostgreSQL remains authoritative for current lifetime.

## 4. Current vs immutable responsibilities

Working separation:

```text
IMMUTABLE / CACHE
    source exact semantic snapshot
    stable base_type
    canonical constraints
    compiled validation artifacts

CURRENT / WRITE UoW
    lineage still exists
    current existing version set
    next exact version allocation
    insertion of the new DRAFT
```

The new version number cannot be derived outside the UoW because current allocation semantics are:

```text
max(existing versions) + 1
```

and a deleted highest DRAFT version number may be reused.

## 5. Exact source lock/read working finding

Given a cache hit for an exact source that was admitted to cache only after becoming PUBLISHED/DEPRECATED:

- the semantic snapshot cannot change;
- the source can only move `PUBLISHED -> DEPRECATED`, which preserves source eligibility;
- the source cannot be deleted individually;
- it can disappear only through whole-lineage deletion.

Working finding:

> the current exact-source lock/read appears unnecessary on the cache-hit path for `CREATE_NEXT`, provided current lineage lifetime remains protected inside the UoW.

This is a discovery finding, not yet a frozen concurrency decision.

## 6. Stable header lock remains semantically justified

Current `DT.H@NKU` has two distinct responsibilities.

### Version-set serialization

`CREATE_NEXT × CREATE_NEXT` on the same lineage must not independently allocate the same next version. The required behavior is serial re-evaluation of the current version set.

Example:

```text
current versions: 1, 2, 3

CREATE_NEXT A
CREATE_NEXT B

valid serial outcome:
    A creates 4
    B wakes, re-evaluates, creates 5
```

A PK conflict alone would not implement that semantic outcome.

`CREATE_NEXT × DELETE_DRAFT` also interacts when deleting the highest DRAFT changes the maximum relevant to allocation.

Example:

```text
1 PUBLISHED
2 DRAFT
```

Valid serial outcomes include:

```text
CREATE_NEXT first
    -> creates 3
    -> DELETE_DRAFT removes 2

DELETE_DRAFT first
    -> removes 2
    -> CREATE_NEXT reuses 2
```

The current stable-header serialization provides the required coherent ordering.

### Lineage lifetime

Whole-lineage delete takes the stable header in the conflicting strongest mode. Holding `DT.H@NKU` therefore also prevents the lineage from disappearing while `CREATE_NEXT` computes the current version set and inserts the new DRAFT.

Since a cached PUBLISHED/DEPRECATED source cannot disappear independently from its lineage, protecting the lineage lifetime is sufficient to protect the historical cached source identity for this operation.

## 7. Current working target shape

With a warm cache:

```text
outside write UoW
    obtain exact source semantic snapshot from cache

inside write UoW
    lock stable DataType header @ NKU
    read current max(version)
    allocate max + 1
    INSERT new DRAFT revision 1 with cloned canonical semantics
    COMMIT
```

Conceptually this reduces the successful cache-hit database path to:

```text
1 locking read
1 max(version) read
1 INSERT
COMMIT
```

while preserving the current version-set and lineage-lifetime guarantees.

## 8. Explicitly open points

This note does not yet decide:

- the final SQL used to compute/allocate the next version;
- whether M4 should retain `max(existing)+1` as the version-allocation contract;
- whether an alternative durable allocator could remove the stable-header serialization requirement;
- final lock modes and LockPlan realization;
- cold-cache SQL projection details;
- exact cache object layout;
- behavior of other DataType operations.
