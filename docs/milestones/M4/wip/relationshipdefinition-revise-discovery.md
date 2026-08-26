# RelationshipDefinition REVISE — M4 discovery

Status: WIP / NON-NORMATIVE.

## Scope

This note records M4 discovery findings for `RelationshipDefinition.REVISE`. It does not authorize implementation and does not change the current concurrency contract.

## Current semantics retained

- The target exact version must exist and be `DRAFT`.
- `expected_revision` remains the optimistic generation token.
- The candidate replaces the complete local property declaration set.
- Property history continuity is checked against every committed `PUBLISHED`/`DEPRECATED` generation, because publication order can differ from version-number order.
- New or changed exact DataType dependencies remain lifecycle-sensitive and must satisfy the current admission rules.
- DRAFT exact semantics are not cacheable.

## Finding 1 — eliminate full Definition over-fetch

The current service loads the complete `RelationshipDefinition` aggregate only to distinguish missing Definition/version before revising an exact version. The aggregate topology, Resolution names and default state do not otherwise participate in REVISE.

M4 candidate: start from the existing one-statement exact-version projection (`project_version`) which can distinguish:

- Definition absent;
- Definition present but requested exact version absent;
- exact version present, with revision/status and complete properties.

This makes the initial current-DRAFT load one authoritative SQL statement and avoids loading the complete Resolution aggregate.

## Finding 2 — keep historical semantics, make conflict detection set-based

The current `published_history()` loads all historical version headers and all declarations into application memory, then `validate_relationship_property_history()` uses them only to enforce, for candidate property names:

1. historical datatype lineage cannot differ from the candidate datatype lineage;
2. once any historical declaration is `LIST`, a candidate `SCALAR` is forbidden.

M4 candidate: retain the exact same complete-history semantics, but perform one set-based historical-conflict query against the persisted `PUBLISHED`/`DEPRECATED` rows for candidate names and return only a violating fact (if any).

Do not introduce a relationship-property history summary/materialization merely for this rare model-plane operation.

## Finding 3 — compute declaration delta from stabilized application state

Before persistence, the application already owns both:

- stabilized `current.properties`;
- complete `candidate.properties`.

The current `replace_candidate()` re-reads the current properties solely to compute the delta. This read is redundant independently of the locking strategy.

M4 candidate: compute a declaration delta in application memory and pass it to persistence.

## Finding 4 — set-based differential DML

Persist the application-computed delta with statement count independent of property count:

- at most one DELETE for removed/changed names;
- at most one bulk INSERT for added/changed rows;
- one version-row UPDATE incrementing revision exactly once.

Empty mutation groups should omit their statement. Delete-before-insert preserves uniqueness correctly when positions are swapped.

## Finding 5 — no post-mutation reload

The application constructs the complete resulting candidate before DML:

- same Definition/version identity;
- `revision = current.revision + 1`;
- `status = DRAFT`;
- complete canonical property declarations.

After successful delta persistence and a successful version-row revision UPDATE, that candidate is exactly the persisted result. Return it after commit rather than re-reading the exact version and its properties.

## Candidate conceptual data path

```text
project current DRAFT                 1 SQL
resolve current DataType operands     set-based
stabilize current concurrency state   deferred to phase 2
historical conflict detection         1 set-based SQL
build candidate + declaration delta   in memory
bulk DELETE changed/removed           <= 1 DML
bulk INSERT added/changed              <= 1 DML
increment revision                     1 DML
commit
return candidate
```

Reads/reloads required solely by the current lock-plan stabilization protocol remain deliberately unresolved until the global M4 concurrency phase.

## Cache / denormalization conclusion

- DRAFT version: no immutable cache.
- No new historical-property materialization is justified by REVISE.
- Existing immutable DataType semantics may support dependency processing, but current lifecycle/admission remains authoritative where required.
