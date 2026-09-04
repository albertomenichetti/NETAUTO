
---

# 23. CS-07 — committed property-history linearization — RESOLVED

Committed RelationshipDefinition property history consists of every exact version whose lifecycle state is:

```text
PUBLISHED | DEPRECATED
```

For each historical property name, the current continuity rule is:

```text
datatype_id
    -> stable across committed history

exact datatype_version
    -> may change

value_mode
    -> may change SCALAR <-> LIST
```

Because exact version number does not encode publication order, every successful `PUBLISH` must be compatible with all committed history linearized before its own commit.

## 23.1 Concurrent PUBLISH of different exact versions

Two different DRAFT versions of the same Definition may be published concurrently. They do not compete on the same DRAFT generation, so target-local lifecycle/revision arbitration alone is insufficient.

Required semantic result:

```text
compatible candidates
    -> both may eventually commit

incompatible candidates
    -> they cannot both commit
```

If the first committed publication introduces a same-name `datatype_id` lineage that conflicts with the second candidate, the second publication must observe the enlarged committed history at its final admission boundary and fail with the reviewed historical semantic-validation outcome.

The concrete Definition-local rendezvous may use a history gate, row protection, serializable arbitration, a suitable relational authority, or an equivalent mechanism. Exact lock, wait, retry, deadlock and constraint realization remains architecture work.

Canonical invariant:

```text
every successful PUBLISH
    -> compatible with every PUBLISHED/DEPRECATED declaration
       linearized before that publication commit
```

## 23.2 Concurrent PUBLISH of the same exact version

For:

```text
PUBLISH D@V
vs
PUBLISH D@V
```

same-target generation/lifecycle arbitration remains sufficient. Only one operation may consume the exact DRAFT generation. After one commit changes the target to `PUBLISHED`, another invocation can no longer satisfy the DRAFT lifecycle gate.

This race is distinct from publication of different exact versions, which requires Definition-level committed-history arbitration.

## 23.3 REVISE versus concurrent history growth

A successful `REVISE` certifies its complete DRAFT candidate against the committed history visible at the REVISE commit boundary.

```text
incompatible PUBLISH commits before REVISE final admission
    -> REVISE must observe the new history
    -> REVISE cannot commit that incompatible candidate
```

The inverse order is intentionally different:

```text
REVISE commits first
later PUBLISH of another RDV extends committed history
    -> the already revised DRAFT may become no longer publishable
    -> the later PUBLISH is not blocked merely to preserve that DRAFT's future publishability
```

`PUBLISH` re-certifies the selected DRAFT against then-current committed history. It does not scan, protect or preserve compatibility for every other DRAFT version. A later history extension may therefore require another REVISE before the affected DRAFT can be published.

Conceptually:

```text
REVISE
    -> provisional candidate certification at its commit boundary

PUBLISH
    -> final certification for admission into committed history
```

## 23.4 History membership is monotonic across lifecycle operations

```text
PUBLISHED -> DEPRECATED
    -> remains part of committed property history
    -> does not release historical datatype-lineage continuity

DELETE_DRAFT
    -> no committed-history effect
    -> DRAFT was never a history member
```

DEPRECATE therefore does not make a formerly used same-name `datatype_id` available for replacement by a different lineage.

## 23.5 Data-path boundary

This checkpoint does not introduce a worker-side full-history load or a dedicated persisted history summary.

Current direction remains:

```text
early set-based conflict probe
    -> optional fail-fast

final concurrency-safe set-based admission/arbitration
    -> correctness requirement

full committed-history materialization in worker
    -> NO

dedicated history-summary materialization
    -> not currently justified
```
