# M3 — Implementation Steps

**Status:** DESIGN IN PROGRESS — NOT YET FROZEN — NO IMPLEMENTATION AUTHORITY

**Authority:** PRE-IMPLEMENTATION PLANNING AUTHORITY

## Purpose

This file now owns M3 implementation decomposition planning after contract and architecture freeze. It does **not** yet authorize software changes.

Frozen prerequisite state:

```text
M3 discovery                         COMPLETE
M3 contract                          FINAL / FROZEN
M3 architecture design points        8 / 8 CLOSED
M3 architecture consistency review   PASS
M3 architecture set                  FINAL / FROZEN
architecture freeze approval         GRANTED
```

Implementation planning may now define the ordered `M3-Snn` slice registry, bounded scope, dependencies, assigned `M3-VER-*` evidence and completion conditions.

Planning must not introduce or reinterpret domain semantics, public contracts, persistence guarantees, concurrency guarantees or architecture decisions. Any contradiction with frozen authorities requires the applicable reopen process.

## Current slice registry

```text
none — implementation decomposition not yet designed/frozen
```

No `M3-Snn` slice is active.

## Required decomposition properties

Before this file may become `FINAL / FROZEN`, the implementation plan must define:

```text
complete ordered slice registry
bounded code/document scope per slice
frozen architecture owner(s) realized by each slice
M3-VER-* bundles/targets assigned per slice
required real-PostgreSQL evidence where applicable
AS-IS regression obligations per slice
no schema/migration/runtime-dependency/lockfile delta
slice prerequisites and completion conditions
final integration/acceptance closure path
no orphan M3-OUT / M3-AC / M3-VER obligation
```

The plan must preserve the frozen 22-route GET matrix, 12-route cursor matrix, 8-create Location matrix, HTTP/CLI parent tri-state, trusted lifecycle decoder boundary and 19 verification bundles.

## Implementation gate

Implementation remains in STOP until all of the following are true:

```text
steps consistency review       PASS
steps.md                        FINAL / FROZEN
project-owner steps approval    GRANTED
status.md                       explicitly authorizes an M3-Snn slice
```

Until then:

```text
active implementation    NONE
software implementation  NOT AUTHORIZED
```

When frozen, this document will own only implementation order, slice scope, evidence assignment and completion conditions. It will not become semantic authority over the frozen contract or architecture.

## Immediate next action

Design the complete M3 implementation slice decomposition and evidence allocation, then run a separate steps consistency/freeze review before requesting explicit steps freeze approval.