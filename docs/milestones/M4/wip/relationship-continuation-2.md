# M4 — Factual Relationship temporary continuation 2

**Status:** TEMPORARY CONTINUATION / WIP / NON-NORMATIVE / MUST MERGE BACK

This file is an ordered continuation of `relationship.md` + `relationship-continuation.md`. It exists only because the current connector cannot safely replace the large existing continuation losslessly. It is not an independent factual Relationship owner.

Before factual Relationship review is considered complete, merge this file losslessly after `relationship-continuation.md` into `relationship.md`, verify the merged content, then delete both temporary continuation files.

---

## C-REL-35 RATIFIED — post-definition Relationship DELETE discovery is complete

```text
DELETE /api/v1/core/relationships/{relationship_id}

DISCOVERY COMPLETE
PUBLIC CONTRACT CLOSED
ARCHITECTURE CLOSING PENDING
```

Public contract remains:

```text
relationship_id UUID required
query none
body none
success -> 204 No Content
absent/repeated DELETE -> 404 resource_not_found / relationship
static invalid request -> 400 invalid_request
unexpected persistence/lifecycle/infrastructure failure -> 500 internal_error
no normal 409 or 422
```

### Root deletion / owned closure

Application explicitly deletes only the factual root:

```text
relationships[id = relationship_id]
```

`runtime_relationship_cells` is owned child state and is removed through the `relationship_id -> relationships.id` FK with `ON DELETE CASCADE`. Application code does not explicitly delete runtime cells.

DELETE consumes the persisted runtime closure only as historical source material. It does not recertify it:

```text
NO expected-cell-count check
NO closure reconstruction
NO RelationshipDefinition / relationship_definition_space read
NO ObjectTemplate ancestry
NO RDV/DataType semantic read
NO semantic cache
```

### Revision

DELETE terminates the current factual generation; it does not prepare a replacement generation:

```text
NO preliminary generation SELECT
NO expected_revision
NO revision CAS
NO revision increment
NO DELETE-owned stabilization retry
```

The factual root row actually deleted is the authoritative DELETE before-state. DATA_CHANGE and SCHEMA_CHANGE remain responsible for their own generation freshness.

### Lifecycle

DELETE is the inverse of CREATE:

```text
RELATIONSHIP_CREATED
    before_state = null
    after_state = { relationship_definition_version, properties }

RELATIONSHIP_DELETED
    before_state = { relationship_definition_version, properties }
    after_state = null
```

`relationships.revision` is excluded from historical factual state.

Each persisted runtime semantic cell supplies one historical DELETE perspective:

```text
relationship_id
relationship_definition_id
object_id              <- from_object_id
relationship_name      <- runtime cell name
destination_object_id  <- to_object_id
canonical_name / destination_canonical_name
    <- one coherent current Object display observation
```

A concurrent Object RENAME may make DELETE observe either old or new committed display names; both are valid, but the complete event set must be internally coherent.

Required atomicity:

```text
relationships root disappearance
+ FK CASCADE of owned runtime cells
+ complete RELATIONSHIP_DELETED event set
-> one atomic COMMIT
```

### Logical target cost

```text
static invalid request -> 0 DB
missing Relationship   -> max 1 PostgreSQL business statement
successful DELETE      -> 1 PostgreSQL business statement + COMMIT
model/cache work        -> 0
revision preparation   -> 0
```

The one statement must be able to consume the factual/runtime/display information required by lifecycle before cascade removes the runtime cells, delete only the root explicitly, persist the DELETE event set and return a minimal result carrier. Exact SQL/SQLAlchemy realization remains architecture work.

### Semantic concurrency

```text
DELETE x DELETE
    one -> 204 + one complete DELETE transition
    other -> 404

DELETE x DATA_CHANGE / SCHEMA_CHANGE
    mutation first -> DELETE removes resulting current generation
    DELETE first -> prepared mutation cannot commit after root disappearance

DELETE x equivalent CREATE
    old fact current -> semantic-cell uniqueness prevents duplicate current fact
    DELETE first -> later CREATE may create new fact Y with new id
    late DELETE(old_id) -> 404 and never affects Y

DELETE x Object.DELETE
    Relationship DELETE first -> endpoint references disappear
    Object DELETE while Relationship remains current -> runtime FK keeps Object alive

DELETE x RelationshipDefinition.DELETE
    Relationship DELETE first -> factual reference released
    Definition DELETE while Relationship remains current -> factual reference blocks deletion
```

Lock modes, waits, FK/UNIQUE rendezvous, ordering and deadlock proof remain architecture-closing work.

### Architecture handoff

Remaining physical decisions:

```text
exact FK / ON DELETE CASCADE DDL
exact one-statement SQL/SQLAlchemy carrier
pre-cascade lifecycle source carrier
server-side vs application-side before_state construction
coherent canonical_name projection
lifecycle batch insert sequencing
lock/wait/FK interaction and deadlock proof
SQLSTATE translation
indexes / EXPLAIN / runtime measurements
```

Architecture must preserve exact-id deletion, root-only explicit DELETE, owned-child cascade, no closure recertification, no model/cache work, no DELETE revision protocol, atomic DELETE history, ABA safety and the one-business-statement target.

### Factual-domain delta discovered during DELETE review — self-reference forbidden

M4 ratifies:

```text
from_object_id != to_object_id
```

A factual Relationship cannot relate an Object to itself.

CREATE behavior:

```text
from_object_id == to_object_id
    -> 422 semantic_validation_failed
    -> rule = self_reference
```

This intentionally supersedes the delivered AS-IS self-loop allowance and the self-loop branches recorded earlier in C-REL-23, C-REL-25, C-REL-29 and C-REL-33.

The invariant is enforced at CREATE/admission/relational-authority boundaries. DELETE and other consumers of current persisted closure do not recertify it.

### Closure

Relationship DELETE is full-sweep complete. No additional factual Relationship route-local discovery point is currently known. Existing architecture-closing items from earlier checkpoints remain open, including the C-REL-26 CREATE Candidate A vs Candidate B selector decision and the global physical/concurrency closure.
