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
| [`api.md`](api.md) | DESIGN IN PROGRESS — ADP-04 / ADP-05 CLOSED | public cursor identity/keyset realization and ObjectTemplate HTTP parent tri-state |
| [`cli.md`](cli.md) | DESIGN IN PROGRESS — ADP-06 CLOSED; ADP-07 OPEN | nullable selector/query carrier and Location materialization grammar |
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

Closed by ADP-04:

```text
query identity = route + membership-affecting path targets + filters + semantic presence bits
position       = complete canonical ordering tuple
limit          = excluded from semantic identity
OBJ-GET-03 adds parent_object_id
OBJ-GET-06 adds object_id
lifecycle global/object scope remains distinct
ObjectTemplate omitted/root/exact-parent states remain distinct
codec v1 payload/invalid_cursor behavior preserved
```

### ObjectTemplate parent filter

HTTP owner: `architecture/api.md`; CLI owner: `architecture/cli.md`.

ADP-05 closes HTTP:

```text
HTTP omitted         -> parent_template_id=None, parent_filter_set=False
HTTP UUID            -> parent_template_id=UUID, parent_filter_set=True
HTTP lowercase null  -> parent_template_id=None, parent_filter_set=True
malformed/repeated   -> 400 invalid_request
parent_filter_set    -> internal only
```

ADP-06 closes CLI:

```text
CLI omitted          -> no query pair
CLI UUID/human       -> normal selector resolution -> UUID query pair
CLI explicit null    -> parsed None -> zero selector lookup -> lowercase null query pair
```

The nullable-selector rule is metadata-driven for direct selector parameters. Nullable QUERY None emits lexical `null`; nullable BODY None remains JSON null; PATH None remains invalid. The generic scalar serializer is not broadened to accept None.

### CLI post-create

Owner: `architecture/cli.md`.

ADP-07 must close Location token grammar, request-vs-response JSON-path resolution, literal materialization, protocol failure on unresolvable expected Location, all eight 201 operations and no hidden mutation enrichment.

## Design-point status

```text
ADP-01  CLOSED   read projection responsibility / persistence boundary
ADP-02  CLOSED   one-statement projection matrix — 22 / 22 routes
ADP-03  CLOSED   historical lifecycle trusted decoder
ADP-04  CLOSED   cursor identity realization — 12 / 12 routes
ADP-05  CLOSED   ObjectTemplate nullable HTTP query carrier
ADP-06  CLOSED   CLI nullable selector/query carrier
ADP-07  OPEN     CLI Location materialization grammar
ADP-08  OPEN     verification architecture
```

Current progress:

```text
closed design points     6 / 8
open design points       2 / 8
GET route coverage      22 / 22 CLOSED
cursor route coverage   12 / 12 CLOSED
HTTP parent tri-state   CLOSED
CLI parent tri-state    CLOSED
next design work         ADP-07 — CLI Location materialization grammar
```

## Closed architecture summaries

### ADP-01 — Read responsibility

Application owns request semantics, cursor validation, read UoW and public outcome classification. Persistence projectors own complete persisted fact projection and representational decoding on the caller-owned connection. Public GETs do not run mutation-semantic certification.

### ADP-02 — Projection matrix

All 22 canonical GET/read routes have one complete business SQL statement target under an ordinary read UoW / PostgreSQL statement snapshot. The frozen projection vocabulary is `RP-01 .. RP-10`; no target public GET requires `coherent_read()`.

### ADP-03 — Historical decoder

Historical reads keep typed carrier materialization and materially-undecodable failure, while removing mutation-transition recertification, duplicated database family/state-shape checks and live-state reinterpretation. Mutation/lifecycle-write validation remains strong.

### ADP-04 — Cursor identity

The delivered opaque cursor v1 payload is preserved. Application constructs one canonical `route + filters` identity after request parsing and reuses it for decode/encode. The complete twelve-route matrix is frozen; only components and Object-relative Relationships add their missing path targets. No canonical keyset tuple changes.

### ADP-05 — HTTP parent tri-state

`GET /object-templates` accepts exactly:

```text
parent_template_id omitted
parent_template_id=<valid delivered UUID carrier>
parent_template_id=null
```

A local nullable-UUID lexical adapter intercepts only exact lowercase `null` and delegates all other values to the delivered UUID parser. Raw query presence remains the internal source of `parent_filter_set`, preserving omission versus explicit root-only filtering. Empty, uppercase/special sentinels, malformed UUIDs and repeats remain `400 invalid_request`. No domain/persistence/cursor redesign is introduced.

### ADP-06 — CLI parent tri-state

The ObjectTemplate list registry marks only `parent_template_id` as nullable while retaining its ObjectTemplate selector capability.

```text
omitted
    -> no selector target
    -> no query pair

UUID
    -> exact-ID selector precedence
    -> canonical UUID query pair

human selector
    -> normal ObjectTemplate discovery
    -> resolved UUID query pair

explicit null
    -> parser None
    -> terminal nullable selector value
    -> zero selector discovery
    -> query pair parent_template_id=null
```

The request planner is location-aware: nullable QUERY None emits lexical `null`; nullable BODY None preserves JSON null; PATH None is invalid. `_wire_string(None)` is not introduced globally.

## Open architecture work

### ADP-07 — CLI Location materialization grammar

Must define the static token grammar, request-value precedence, response JSON-path resolution and exact literal replacement used to validate expected `Location` across all eight registered 201 operations.

### ADP-08 — Verification architecture

Must define deterministic permanent evidence for all frozen contract outcomes, including 22 GET statement/projection checks, 12 cursor routes, lifecycle decoding, HTTP/CLI parent tri-state, eight create/Location operations, mutation-validation preservation and no schema/dependency delta.

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

public lexical carrier
    != internal semantic presence bit

CLI parsed explicit null
    != omitted parameter
    != arbitrary None scalar

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
