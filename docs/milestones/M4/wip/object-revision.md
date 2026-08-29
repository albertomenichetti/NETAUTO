# M4 WIP — Object intrinsic revision / generation token

**Status:** RATIFIED CROSS-OPERATION DIRECTION / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file owns the M4 cross-operation direction for a persisted intrinsic Object `revision`.

The goal is to give every committed generation of the `objects` row one cheap explicit generation token and one uniform stale-success protocol for intrinsic Object mutations.

This is technical concurrency/persistence state, not public business state.

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
    = universal technical intrinsic-row generation token

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

# 3. Universal intrinsic-generation rule

Every intrinsic Object mutation that was prepared or derived from a previously observed current Object generation carries that observed revision as:

```text
expected_revision = R
```

The mutation may commit a new intrinsic Object generation only if that generation is still current:

```text
current revision == expected_revision
    -> mutation may proceed if its own semantic admissions succeed

current revision != expected_revision
    -> stale attempt
    -> no Object mutation
    -> no lifecycle transition for that failed attempt
    -> bounded retry from a fresh Object generation
```

Every committed mutation that actually writes a new intrinsic `objects` row generation increments revision atomically with that row mutation:

```text
new_revision = expected_revision + 1
```

This rule is deliberately uniform even when the concurrent intrinsic mutation touched a field that the retrying operation did not semantically depend on.

Example:

```text
RENAME prepared from revision 12
concurrent DATA_CHANGE commits revision 12 -> 13
RENAME expected_revision = 12 no longer matches
    -> retry
```

That retry is a conservative false-positive from the narrower operation-specific dependency perspective, but it is accepted in exchange for one simple, reusable intrinsic-generation protocol.

Canonical priority:

```text
one intrinsic generation token
one stale-success rule
one bounded retry protocol

preferred over
operation-specific freshness mechanisms
```

If later measured evidence shows unacceptable retry amplification under high same-Object write contention, M4/future architecture may reopen this trade-off. No operation-specific exception is introduced speculatively now.

---

# 4. Revision is the freshness token, PostgreSQL remains the physical serializer

`revision` does not itself create PostgreSQL row-update waiting/serialization.

Canonical distinction:

```text
physical row serialization / waiting
    -> PostgreSQL concurrency realization

revision
    -> explicit intrinsic-generation identity
    -> universal expected-generation/CAS predicate
    -> stale-success detection
```

The exact SQL/locking realization remains architecture work, but every intrinsic mutation must preserve the logical CAS contract above.

A successful expected-revision check also proves that **no committed intrinsic Object-row mutation occurred** since the generation was observed.

Therefore an operation does not need a second independent freshness mechanism merely to prove that another intrinsic field stayed unchanged over the same interval.

Examples:

```text
DATA_CHANGE prepared under exact binding T@V + revision R
current revision still R
    -> no committed SCHEMA_CHANGE occurred
    -> binding is still T@V

RENAME observed canonical_name A + revision R
current revision still R
    -> A still belongs to the same current intrinsic generation
```

Operation-specific semantic admission remains separate: revision freshness does not prove target schema admissibility, property-value validity, or any fact outside `objects`.

---

# 5. Increment rule and semantic no-op distinction

Current intrinsic mutation families include:

```text
RENAME
DATA_CHANGE when it performs a persisted Object-row mutation
SCHEMA_CHANGE when it commits a new intrinsic Object generation
```

`revision` describes **row-generation change**, not necessarily a semantically different business value.

Therefore a mutation that deliberately performs an Object-row UPDATE even when assigned values are equal still creates a new technical row generation and increments `revision`.

Current consequences:

```text
RENAME same-name assignment
    -> normal persisted RENAME mutation
    -> revision increments

DATA_CHANGE semantic no-op elided on the normal cheap path
    -> no Object UPDATE
    -> no lifecycle event
    -> revision does not increment

future DATA_CHANGE realization that intentionally performs a normal row mutation
for a same-result request because no-op recognition would be materially costly
    -> revision increments because a new row generation was written
```

The revision counter therefore must not be interpreted as a count of semantically distinct business values.

---

# 6. DELETE

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

DELETE concurrency still relies on the already-ratified Object lifetime arbitration; revision does not replace external-reference integrity.

---

# 7. Scope boundary — intrinsic row, not every Object-related fact

`revision` is universal for **intrinsic `objects`-row generations**, not a global counter for every fact reachable from an Object.

Current structural/factual mutations do not bump an Object revision solely because an Object participates:

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

Where a mutation also depends on current structural facts, those facts still need their own relational admission/protection mechanism.

---

# 8. RENAME focused revalidation

RENAME is the only already-full-swept intrinsic Object mutation that needed focused revalidation after revision introduction.

Its public contract and lifecycle responsibility remain unchanged.

Current logical generation protocol:

```text
Q1
    read current canonical_name = old_name
    read current revision = R

Q2
    commit only against expected_revision = R

    canonical_name := requested_name
    revision := R + 1
    append exact RENAME lifecycle:
        old_name -> requested_name
```

Revision mismatch produces no mutation/lifecycle for that stale attempt and triggers bounded retry from a fresh current generation.

Same-name RENAME remains a normal persisted mutation:

```text
old_name == requested_name
    -> success path
    -> revision increments
    -> exact RENAME lifecycle may contain equal old/new values
```

The revision protocol replaces the need for a separate canonical-name-specific freshness/protection mechanism at the logical level. Exact SQL/lock realization remains architecture work.

---

# 9. DATA_CHANGE full-sweep consequence

The DATA_CHANGE full sweep is route-locally closed and adopts the universal revision protocol.

Its current generation read retains:

```text
object_id
template_id
template_version
revision = R
full properties
```

Requested effects are validated against the exact binding from that generation and applied to the complete current property map in the application/domain layer.

A real final mutation may commit only if:

```text
current revision == R
```

Because SCHEMA_CHANGE is itself an intrinsic row mutation that increments revision, the successful revision check also proves that the exact binding used for preparation is still current. A second independent binding-freshness protocol is not required for the same attempt.

On a real persisted DATA_CHANGE:

```text
properties := complete application-derived candidate
revision := R + 1
DATA_CHANGE exact changed-property lifecycle delta
```

must commit atomically.

On cheap semantic no-op elision:

```text
no Object-row mutation
no lifecycle event
revision remains R
```

No revision refresh is required solely to return a no-op or a semantic failure proven from one coherent observed generation, because those outcomes commit no stale state transition.

Revision mismatch on the real-write branch is an internal stale-attempt condition and triggers bounded retry from the current generation. If the retry budget is exhausted, DATA_CHANGE maps that internal stabilization failure to `500 internal_error`, not a normal public `409`.

The complete DATA_CHANGE route contract/data path remains owned by its route owner until lossless absorption into `object.md`.

---

# 10. SCHEMA_CHANGE consequence

The existing SCHEMA_CHANGE discovery uses an intrinsic Object fingerprint to prove that an expensive prepared candidate is still based on the current intrinsic Object generation.

The universal persisted revision supersedes that fingerprint role for intrinsic-row freshness:

```text
prepare
    observe revision = R
    derive candidate from intrinsic state at R

final mutation UoW
    current revision == R
        -> intrinsic generation unchanged

    current revision != R
        -> stale candidate
        -> candidate must not commit
        -> bounded retry according to the final SCHEMA_CHANGE protocol
```

This direction must be absorbed when the SCHEMA_CHANGE full sweep reaches its data-path/concurrency block.

Revision does not replace separate relational admission/protection for component-slot/ownership facts because those are outside intrinsic-row scope.

---

# 11. Already-full-swept route impact

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
    -> focused revalidation completed by the universal expected-revision rule

POST /objects/{id}/properties
    -> route-local full sweep completed under the universal revision rule
    -> pending only lossless absorption/cleanup into object.md

DELETE /objects/{id}
    -> deletes current revisioned generation
    -> no surviving increment
    -> revision not automatically added to DELETED semantic payload
```

---

# 12. Architecture handoff

M4 discovery does not yet freeze:

```text
exact SQL type width if architecture later proves BIGINT unsuitable
exact CHECK/default/DDL details
whether CREATE also has a physical database default as a defensive backstop
exact CAS statement syntax
exact row-lock/wait realization around CAS
exact bounded retry count/backoff policy
physical index implications
```

The semantic/persistence direction that architecture must preserve is:

```text
first intrinsic generation starts explicitly at revision 1
all prepared/derived intrinsic mutations use expected_revision
revision mismatch cannot commit stale Object state or lifecycle
stale mismatch is handled by bounded retry
persisted intrinsic row mutation advances revision atomically
revision is monotonic for one Object lifetime
revision is never a substitute for operation-specific semantic admission
revision does not implicitly serialize structural/Relationship facts outside objects
revision is internal technical state unless a later public contract explicitly exposes it
```
