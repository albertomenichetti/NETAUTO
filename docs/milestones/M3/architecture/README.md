# M3 — Architecture Set

**Architecture set status:** DESIGN IN PROGRESS — NOT FROZEN

**Authority:** M3 TO-BE ARCHITECTURE SET CONTROL

## Purpose and authority boundary

This directory defines the M3 TO-BE architecture required to realize the frozen milestone contract in [`../contract.md`](../contract.md).

The set starts from delivered AS-IS under `docs/architecture/` and may change only explicit M3 deltas. Preserved guarantees remain owned by their current AS-IS documents and must not be duplicated as competing M3 authority.

Implementation remains unauthorized until this architecture set is `FINAL / FROZEN`, `steps.md` is subsequently frozen and `status.md` explicitly authorizes a slice.

## Frozen contract inputs

```text
M3-OUT-01 .. M3-OUT-08
M3-AC-01  .. M3-AC-19
M3-CQG-01 .. M3-CQG-08
```

Primary areas:

```text
A. truthful CLI 201 / Location handling
B. public GET/read semantic-ownership correction
C. complete cursor query identity and keyset position
D. trusted historical lifecycle decoding
E. ObjectTemplate parent_template_id omitted / UUID / null carrier
F. single-request self-consistent committed read projection
```

No M3 architecture may broaden these outcomes into new routes/resources, schema/migrations, dependencies/lockfile changes, mutation-lock redesign or unrelated CLI behavior.

## Normative document map

| Document | Status | Ownership |
|---|---|---|
| [`read-projections.md`](read-projections.md) | DESIGN IN PROGRESS — ADP-01 / ADP-02 / ADP-03 CLOSED | GET/read responsibility, one-statement route matrix, read UoW/snapshot model, trusted lifecycle decoder boundary |
| [`api.md`](api.md) | NOT YET WRITTEN | public cursor identity/keyset realization and ObjectTemplate HTTP parent tri-state |
| [`cli.md`](cli.md) | NOT YET WRITTEN | Location materialization grammar and nullable selector/query carrier |
| [`verification.md`](verification.md) | NOT YET WRITTEN | deterministic architecture/acceptance evidence |

Additional architecture documents may be added only when an open design point cannot be owned cleanly here and may not expand the frozen contract.

## Current AS-IS dependencies

Material current owners include:

```text
docs/architecture/README.md
docs/architecture/api.md
docs/architecture/cli.md
docs/architecture/datatype.md
docs/architecture/objecttemplate.md
docs/architecture/object.md
docs/architecture/relationship.md
docs/architecture/persistence.md
docs/architecture/concurrency.md
docs/architecture/verification.md
```

The M3 set must record every intentional TO-BE contradiction and every preserved dependency.

## Area ownership

### CLI post-create

Owner: `architecture/cli.md`.

Must close Location token grammar, request-vs-response JSON-path resolution, literal materialization, protocol failure on unresolvable expected Location, all eight 201 operations and no hidden mutation enrichment.

### Public reads

Primary owner: `architecture/read-projections.md`; boundary owners: `api.md`, `verification.md`.

Closed by ADP-01 / ADP-02 / ADP-03:

```text
mutation certification vs read projection responsibility
one SQL business statement for all 22 canonical GET/read routes
ordinary read UoW / statement snapshot
no target public GET dependence on coherent_read()
404 vs empty/null preservation
trusted projector boundary
complete route-specific projection-pattern matrix
historical lifecycle decoding-only boundary
no read-side lifecycle transition certification
write-side lifecycle validation remains intact
```

`coherent_read()` remains infrastructure and is not globally deprecated.

### Cursor correctness

Owner: `architecture/api.md`; verification owner: `architecture/verification.md`.

Must freeze:

```text
query identity = route + membership-affecting path targets + filters + semantic presence bits
position       = complete canonical ordering tuple
limit          = excluded from semantic identity
OBJ-GET-03 adds parent_object_id
OBJ-GET-06 adds object_id
lifecycle global/object scope remains distinct
ObjectTemplate omitted/root/exact-parent states remain distinct
```

### ObjectTemplate parent filter

HTTP owner: `api.md`; CLI owner: `cli.md`.

```text
HTTP omitted         -> no parent filter
HTTP UUID            -> exact stable parent
HTTP lowercase null  -> roots only
CLI omitted          -> no query pair
CLI UUID/human       -> resolved UUID query pair
CLI explicit null    -> lowercase null, no selector lookup
parent_filter_set    -> internal only
```

## Design-point status

```text
ADP-01  CLOSED   read projection responsibility / persistence boundary
ADP-02  CLOSED   one-statement projection matrix — 22 / 22 routes
ADP-03  CLOSED   historical lifecycle trusted decoder
ADP-04  OPEN     cursor identity realization
ADP-05  OPEN     ObjectTemplate nullable HTTP query carrier
ADP-06  OPEN     CLI nullable selector/query carrier
ADP-07  OPEN     CLI Location materialization grammar
ADP-08  OPEN     verification architecture
```

Current progress:

```text
closed design points     3 / 8
open design points       5 / 8
ADP-02 route coverage   22 / 22 CLOSED
next design work         ADP-04 — cursor identity realization
```

### ADP-01 — CLOSED

Owned by [`read-projections.md`](read-projections.md).

```text
HTTP adapter
    -> lexical carrier / DTO
application read service
    -> request semantics / cursor validation / read UoW / public classification
persistence read projector
    -> complete persisted projection / target evidence / representational decoding
    -> NO mutation semantic certification
```

Mutation validators remain intact. `coherent_read()` remains available infrastructure but is not a target dependency for the 22 canonical public GETs.

### ADP-02 — CLOSED — 22/22

Owned by [`read-projections.md`](read-projections.md).

Route-family closure:

```text
DataType             4 / 4 CLOSED
ObjectTemplate       6 / 6 CLOSED
Object               6 / 6 CLOSED
RelationshipDef      4 / 4 CLOSED
Relationship         1 / 1 CLOSED
Global lifecycle     1 / 1 CLOSED
------------------------------
total               22 / 22 CLOSED
```

The frozen projection-pattern vocabulary is `RP-01 .. RP-10`: direct pages/exacts, parent-rooted pages, exact aggregates with independent child sets, recursive exact/stable traversal, context-completed pages, optional projections, root-paged aggregates and parent-rooted exact aggregates.

All 22 target projections use one business SQL statement on an ordinary read UoW / PostgreSQL statement snapshot and require no public-GET `coherent_read()` dependency. Query/SQLAlchemy syntax that does not alter the frozen logical shape remains implementation-local.

### ADP-03 — CLOSED

Owned by [`read-projections.md`](read-projections.md).

The historical read decoder is decoding-only:

```text
KEEP
    EventKind materialization
    required field extraction needed for DTO construction
    UUID/int/string carrier conversion
    recursive JsonValue decoding
    typed lifecycle-family projection
    internal failure for materially undecodable required state

REMOVE
    historical identifier/admission revalidation
    runtime-property non-null/non-empty/homogeneous-list rules
    snapshot canonical-name/version semantic bounds
    exact internal JSON key-set certification
    outer-row/snapshot coherence checks
    intrinsic and Relationship transition certification
    duplicated database family/state-shape checks
    HTTP before/after persisted-state recertification
    live-state lookups used only to reinterpret history
```

Semantically surprising but representationally decodable history remains readable. Mutation and lifecycle-write validation remain strong; any write invariant previously coupled to a shared decoder must remain or move to the write boundary before the read decoder is weakened.

### ADP-04 .. ADP-08 — OPEN

ADP-04 must define one cursor identity construction rule for all 12 routes. ADP-05/06 must freeze HTTP/CLI explicit-null carriers. ADP-07 must freeze Location value-path materialization. ADP-08 must define deterministic verification and statement-count evidence.

## Architecture design rules

```text
public contract outcome
    != architecture realization
    != local implementation decomposition

request validation
    != persisted semantic certification
    != representational decoding

cursor query identity
    != keyset position
    != page limit

current AS-IS ownership
    != M3 TO-BE delta ownership
```

Architecture may choose SQLAlchemy/SQL composition, helper boundaries and internal carrier shapes only where those choices preserve the frozen contract and this architecture.

## Freeze gate

The set may become `FINAL / FROZEN` only after:

```text
all planned owner documents are written
ADP-01 .. ADP-08 are CLOSED
all M3 outcomes/ACs have architecture or preserved AS-IS ownership
22 / 22 GET routes have complete projection disposition
12 / 12 cursor routes have complete identity/keyset disposition
HTTP and CLI parent-filter carriers are mutually consistent
CLI Location grammar covers all 8 registered 201 operations
verification covers every frozen outcome
cross-document consistency passes
no stale TODO/TBD/contradictory owner remains
```

Until then:

```text
ARCHITECTURE SET = DESIGN IN PROGRESS — NOT FROZEN
IMPLEMENTATION   = NOT AUTHORIZED
```

## Reopen discipline

If architecture discovers that the frozen contract is contradictory or insufficient to determine an observable outcome, stop the affected design point and request formal contract reopening. Architecture must not silently reinterpret the contract.