# M4 WIP — Object intrinsic revision / generation token

**Status:** RATIFIED CROSS-OPERATION DIRECTION / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file owns the M4 cross-operation direction for a persisted intrinsic Object `revision`.

The goal is to give every committed generation of the `objects` row a cheap explicit generation token that can be used by Object mutations for freshness/CAS checks where their semantic preparation actually depends on a previously observed intrinsic generation.

This is a technical concurrency/persistence fact, not public business state.

Everything under `wip/` remains globally non-normative and does not authorize implementation.

---

# 1. Candidate Object row shape

M4 adds the following technical column to the intrinsic Object row:

```text
objects
    id
    canonical_name
    template_id
    template_version
    properties JSONB
    revision BIGINT NOT NULL
```

`revision` identifies the committed generation of the **intrinsic Object row**.

Canonical interpretation:

```text
Object.revision
    = technical intrinsic-row generation token

Object.revision
    != ObjectTemplate version
    != business/domain version
    != lifecycle event sequence
    != aggregate-wide ownership generation
    != Relationship generation
    != public Object identity
```

The public Object DTOs do not expose `revision` merely because the persistence row carries it.

---

# 2. CREATE initializes generation 1 explicitly

Object CREATE materializes the first intrinsic Object generation.

The INSERT contract must therefore explicitly create:

```text
revision = 1
```

This must be visible in the M4 CREATE persistence direction rather than being left as an implicit database default whose semantic meaning is undocumented.

Conceptually:

```text
INSERT new Object
    id
    canonical_name
    template_id
    template_version
    properties
    revision = 1
```

This is an alignment of the already-full-swept CREATE persistence model. It does not reopen CREATE public admission/property/component semantics.

---

# 3. Increment rule

Every committed mutation that actually writes a new intrinsic `objects` row generation increments the current revision atomically with that row mutation:

```text
new_revision = old_revision + 1
```

Current intrinsic mutation families include:

```text
RENAME
DATA_CHANGE when it performs a persisted Object-row mutation
SCHEMA_CHANGE when it commits a new intrinsic Object generation
```

The increment is part of the same atomic current-state write as the mutated intrinsic fields.

`revision` describes **row-generation change**, not necessarily a semantically different business value.

Therefore a mutation that deliberately performs an Object-row UPDATE even when assigned values are equal still creates a new technical row generation and increments `revision`.

Current consequences:

```text
RENAME same-name assignment
    -> still a normal persisted RENAME mutation
    -> revision increments

DATA_CHANGE semantic no-op elided on the normal cheap path
    -> no Object UPDATE
    -> revision does not increment

future DATA_CHANGE realization that intentionally performs a normal row mutation
for a same-result request because no-op recognition would be materially costly
    -> revision increments because a new row generation was written
```

This keeps `revision` independent from the higher-level question "did a semantically different business value result?".

---

# 4. DELETE

DELETE removes the current intrinsic Object row and therefore consumes/terminates the current revisioned generation.

There is no surviving current row on which to persist `revision + 1`.

Canonical rule:

```text
DELETE
    -> remove current Object generation
    -> no surviving revision increment required
```

`revision` is technical concurrency metadata and is not automatically part of the semantic DELETED lifecycle payload.

The already-ratified DELETED historical snapshot remains about the intrinsic Object state whose lifetime ended, not about exposing the technical generation counter as domain history.

---

# 5. Scope boundary — intrinsic row, not every Object-related fact

`revision` must not become a global counter for every fact reachable from an Object.

In particular, current structural/factual mutations do not bump an Object revision solely because an Object participates:

```text
ATTACH
DETACH
Relationship.CREATE
Relationship.DATA_CHANGE
Relationship.SCHEMA_CHANGE
Relationship.DELETE
```

unless a later operation contract independently requires writing the intrinsic `objects` row for a semantic reason.

This avoids turning `objects` into a global serialization hot spot and avoids introducing extra parent/child/endpoint row updates merely to advance a counter.

Current structural state remains owned by its dedicated persistence:

```text
object_component_slots
object_components
factual Relationship runtime state
```

`Object.revision` therefore proves freshness only for intrinsic `objects`-row state. It does not by itself prove freshness of ownership or Relationship facts.

---

# 6. Revision is a freshness token, not the serializer itself

PostgreSQL still provides the physical row-update serialization for concurrent writes to the same `objects` row.

The revision column adds an explicit, cheap generation identity that operations may use as an optimistic compare-and-swap predicate where appropriate.

Canonical distinction:

```text
row serialization / waiting
    -> PostgreSQL concurrency realization

revision
    -> explicit intrinsic-generation identity
    -> optional expected-generation/CAS input for an operation
```

A mutation must not automatically use `expected_revision` merely because the column exists.

Freshness predicates remain operation-responsibility-specific.

Example:

```text
prepared mutation depends on the complete previously observed intrinsic generation
    -> expected_revision is a natural stale-success guard

prepared mutation depends only on exact ObjectTemplate binding
and applies effects to fresh current properties in the final UoW
    -> unrelated RENAME revision change need not automatically invalidate preparation
```

This prevents `revision` from becoming an unnecessarily conservative global optimistic mutex.

---

# 7. SCHEMA_CHANGE consequence

The existing SCHEMA_CHANGE discovery uses an intrinsic Object fingerprint to prove that an expensive prepared candidate is still based on the current intrinsic Object generation.

A persisted revision can replace that expensive intrinsic-state fingerprint role where the preparation depends on the complete intrinsic generation:

```text
prepare
    observe revision = R
    derive candidate from intrinsic state at R

final protected UoW
    current revision == R
        -> intrinsic generation unchanged

    current revision != R
        -> candidate stale
        -> candidate must not commit
```

This direction must be revalidated when the SCHEMA_CHANGE full sweep reaches its concurrency/data-path block.

`revision` does not automatically replace separate relational admission/protection for component-slot/ownership facts because those are outside intrinsic-row scope.

---

# 8. RENAME revalidation consequence

RENAME is the only already-full-swept intrinsic Object mutation whose current mutation realization must be explicitly reopened because `revision` becomes part of every persisted Object-row mutation.

At minimum, RENAME must now preserve:

```text
canonical_name := requested_name
revision := revision + 1
```

atomically with its exact RENAME lifecycle transition.

The existing public contract and minimal lifecycle responsibility remain intact unless the focused revalidation discovers a real conflict.

The focused RENAME pass must decide whether `revision` changes the preferred current-name protection/CAS realization; it must not automatically widen RENAME semantic responsibility.

---

# 9. DATA_CHANGE consequence

DATA_CHANGE is currently under full-sweep revalidation and therefore adopts `revision` directly rather than requiring a later route reopening.

Current direction:

```text
persisted DATA_CHANGE row mutation
    -> revision increments atomically

cheap semantic no-op elision
    -> no Object-row mutation
    -> no revision increment
```

Whether DATA_CHANGE uses an expected revision as a commit predicate depends on its final data path and actual preparation dependencies; the existence of the revision column alone does not require a full-generation CAS.

---

# 10. Already-full-swept route impact

Current impact classification:

```text
POST /objects
    -> persistence alignment only
    -> INSERT explicitly includes revision = 1

GET /objects
GET /objects/{id}
    -> no public representation change
    -> revision not exposed merely because it exists

PUT /objects/{id}/canonical-name
    -> focused route revalidation required

DELETE /objects/{id}
    -> deletes current revisioned generation
    -> no surviving increment
    -> revision not automatically added to DELETED semantic payload
```

This keeps the revalidation surface minimal while making the cross-operation generation model explicit before more intrinsic mutation routes are closed.

---

# 11. Architecture handoff

M4 discovery does not yet freeze:

```text
exact SQL type width if architecture later proves BIGINT unsuitable
exact CHECK/default/DDL details
whether increment is expressed in application SQL, generated statement helper or another database mechanism
exact CAS statement syntax
exact retry policy for operations that use expected_revision
physical index implications
```

The semantic/persistence direction that architecture must preserve is:

```text
first intrinsic generation starts at revision 1
persisted intrinsic row mutation advances revision atomically
revision is monotonic for one Object lifetime
revision is never a substitute for operation-specific semantic admission
revision does not implicitly serialize structural/Relationship facts outside objects
revision is internal technical state unless a later public contract explicitly exposes it
```
