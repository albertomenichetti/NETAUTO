# M4 — DataType SET_DEFAULT discovery

**Status:** WIP / NON-NORMATIVE

**Role:** bounded discovery note for `DataType.SET_DEFAULT`. This document records AS-IS evidence, findings and working hypotheses only. It does not define the M4 contract, TO-BE architecture, persistence schema, cache contract or concurrency realization.

The delivered AS-IS under `docs/architecture/` remains authoritative until M4 explicitly freezes a TO-BE delta.

## 1. Scope

This note intentionally covers only:

- the current data needed by `DataType.SET_DEFAULT`;
- whether worker-local immutable semantic cache participates in the operation;
- duplicate reads visible in the current realization;
- the phase boundary between data-access optimization and later global concurrency redesign.

Lock-mode changes, pairwise race redesign and final PostgreSQL realization are deliberately deferred to the later concurrency-design phase.

## 2. AS-IS flow

Current `SET_DEFAULT(DT, version)` performs one write UoW that:

```text
lock DataType header          FOR NO KEY UPDATE
lock target DataTypeVersion   FOR SHARE
load target DataTypeVersion
require target.status == PUBLISHED
update DataType.default_version
return updated lineage
commit
```

The target exact version is therefore first read by the locking statement and then read again through the ordinary version load.

## 3. Required information classification

`SET_DEFAULT` does not need DataType semantic payload such as:

```text
base_type
constraints
compiled regex / runtime validators
```

It needs only current mutable facts:

```text
target exact version exists now
target exact version is PUBLISHED now
current lineage default policy can be updated coherently
```

Therefore the worker-local immutable semantic cache provides no direct benefit to this operation.

## 4. Working finding: remove duplicate target read

The current realization obtains the target row once to acquire `FOR SHARE` and then issues another SELECT to obtain its lifecycle status.

Working M4 data-access direction:

```text
one locking read of the target exact version
    -> establish existence
    -> return lifecycle status
    -> stabilize the row for the existing concurrency contract
```

followed by the lineage update.

This is a data-access simplification only. It does not by itself change the required safety predicates or lock semantics.

## 5. Phase separation for M4

The first M4 audit phase records for each operation:

- required current vs immutable data;
- cache usefulness;
- repeated loads/reconstruction;
- work that can move outside the UoW;
- a candidate minimal data-access path.

Current lock modes and rendezvous are treated as the delivered safety baseline during this phase.

Only after the operation audit is complete will M4 perform a separate global concurrency-design phase:

```text
candidate operation flows
    -> semantic concurrency matrix
    -> pairwise race analysis
    -> required safety predicates
    -> proposed lock/FK/arbitration realization
    -> deterministic PostgreSQL verification
```

This prevents local query/lock simplifications from silently breaking cross-operation guarantees.

## 6. Current bounded conclusion

For `DataType.SET_DEFAULT`:

```text
semantic cache
    -> no required role

PostgreSQL current truth
    -> target existence
    -> target PUBLISHED lifecycle
    -> default policy mutation

AS-IS data-access inefficiency
    -> target exact version is effectively read twice

candidate direction
    -> locking read should also return the lifecycle carrier needed for admission
```

No lock removal or mode change is decided by this note.
