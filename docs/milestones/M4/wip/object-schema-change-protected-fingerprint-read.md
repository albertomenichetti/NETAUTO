# M4 WIP — Object SCHEMA_CHANGE protected fingerprint read

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note freezes the route-local realization direction for the protected aggregate fingerprint read used by:

```http
POST /api/v1/core/objects/{object_id}/schema
```

It refines the already-frozen optimistic preparation / whole-aggregate fingerprint protocol.

## Purpose

A prepared successful `SCHEMA_CHANGE` candidate may commit only if the authoritative current Object aggregate still represents the same aggregate generation used during preparation.

After the parent Object concurrency-owner lock has been acquired, the command therefore performs one fresh protected aggregate read and compares its fingerprint with the fingerprint stored in `PreparedSchemaChange`.

## Statement boundary

The protected aggregate read remains a distinct PostgreSQL statement after the parent Object lock-acquisition statement.

```text
Q2
    acquire parent Object @ FOR NO KEY UPDATE

Q2 completes

Q3
    NEW READ COMMITTED statement
    read authoritative aggregate state
    compute application fingerprint
```

This preserves the already-frozen requirement that Q3 obtains a new PostgreSQL statement snapshot after any wait on the Object lock.

## Q3 authoritative state

Q3 reads only the authoritative current state that participates in the agreed whole-Object aggregate fingerprint.

Conceptually:

```text
Object intrinsic state
    id
    canonical_name
    template_id
    template_version
    properties

outgoing ownership facts where Object is parent
    child_object_id
    slot_declaring_template_id
    slot_name
```

The runtime ownership rows are emitted in deterministic order before fingerprinting:

```text
(slot_declaring_template_id, slot_name, child_object_id)
```

The exact SQL syntax may use ordered row output or ordered aggregation. The frozen requirement is that one Q3 database statement returns one deterministic representation of the complete authoritative fingerprint scope.

## Explicit exclusions

Q3 does not join or load state that is not part of the Object aggregate fingerprint.

Excluded examples:

```text
child canonical_name
child properties
child exact schema binding
ObjectTemplate display metadata
ObjectTemplate effective schema
Relationship state
lifecycle history
owner/incoming ownership fact
```

Those values either belong to other aggregates or are not part of the agreed Object concurrency generation.

## Application-side fingerprint computation

The fingerprint is computed in the application, not by PostgreSQL.

Both preparation and protected Q3 use the same canonical aggregate encoding and the same fingerprint function:

```text
prepare snapshot S
    -> canonical_encode(S)
    -> F(S)

protected Q3 snapshot S'
    -> canonical_encode(S')
    -> F(S')
```

This gives one implementation authority for ordering / canonicalization and avoids coupling the semantic concurrency protocol to PostgreSQL-specific hashing functions or extensions.

The comparison remains:

```text
F(S') == prepared.expected_object_fingerprint
    -> prepared candidate is still current

F(S') != prepared.expected_object_fingerprint
    -> rollback
    -> apply the already-frozen bounded retry policy
```

## Why application-side hashing

The route already needs the complete aggregate state during optimistic preparation, so application-side fingerprinting has negligible additional semantic complexity there.

For Q3, the selected direction deliberately prefers:

```text
one bounded DB read
+
one shared application canonicalization/hash implementation
```

over introducing:

```text
DB-specific canonical JSON construction
DB-specific hash implementation
extension dependency
separate DB/application equivalence rules
```

The M4 design therefore does not require `pgcrypto`, PostgreSQL `hash*` functions, generated hash columns or persisted Object revisions merely to implement this route.

## One-query requirement

Q3 must not split the authoritative fingerprint scope across independent PostgreSQL statements.

Forbidden shape:

```text
SELECT Object intrinsic state
then
SELECT outgoing ownership rows
```

because those would use two different `READ COMMITTED` statement snapshots.

Required shape:

```text
one PostgreSQL statement
    -> Object intrinsic state
    + complete outgoing ownership facts
    -> one statement snapshot
```

The result may physically contain one root row plus repeated edge columns or one root row plus an ordered aggregate; that is an implementation/query-shape choice to be proven by physical evidence.

## Missing Object during Q3

Q2 already acquired the exact parent Object row and holds it through Q3, so Q3 not finding that Object is an invariant/persistence failure rather than a normal caller-visible not-found race.

A normal concurrent Object delete cannot remove the row while this transaction owns the parent Object lock.

## Physical-design handoff

The final M4 relational/index review must prove that Q3 has a bounded access path:

```text
objects PK lookup by object_id
+
outgoing object_components lookup by parent_object_id
```

with deterministic edge ordering supported efficiently by the final TO-BE ownership index shape.

No additional physical index is frozen route-locally here; index selection remains part of the architecture-wide physical review.

## Frozen decision

```text
Q3 = one fresh PostgreSQL statement after Object lock acquisition

Q3 returns:
    complete Object intrinsic fingerprint state
    complete outgoing ownership fingerprint state
    deterministic edge order

fingerprint computation:
    application-side
    same canonical encoding during preparation and Q3
    same fingerprint function during preparation and Q3

no PostgreSQL hash dependency
no hash extension requirement
no persisted hash/revision introduced for this route
no split multi-statement protected fingerprint read
```

The exact canonical byte encoding and concrete hash algorithm remain the next implementation-level decision to freeze.
