# M3 — Architecture Set

**Architecture set status:** DESIGN IN PROGRESS — NOT FROZEN

**Authority:** M3 TO-BE ARCHITECTURE SET CONTROL

## Purpose and authority boundary

This directory defines the M3 TO-BE architecture required to realize the frozen milestone contract in [`../contract.md`](../contract.md).

The architecture set starts from the delivered AS-IS under:

```text
docs/architecture/
```

and may change only the explicit M3 deltas frozen by the contract. Delivered guarantees not explicitly changed by M3 remain owned by their current AS-IS documents and must not be duplicated as competing M3 authority.

This README controls the M3 architecture set: document ownership, design status, open design points, freeze scope and cross-document consistency. It does not itself replace the owning architecture documents listed below.

Implementation remains unauthorized until this architecture set is `FINAL / FROZEN`, `steps.md` is subsequently frozen and `status.md` explicitly authorizes an implementation slice.

## Frozen contract inputs

The architecture set must realize exactly the frozen M3 outcome boundary:

```text
M3-OUT-01 .. M3-OUT-08
M3-AC-01  .. M3-AC-19
M3-CQG-01 .. M3-CQG-08
```

Primary contract areas:

```text
A. truthful CLI 201 / Location handling
B. public GET/read semantic-ownership correction
C. complete cursor query identity and keyset position
D. trusted historical lifecycle decoding
E. ObjectTemplate parent_template_id omitted / UUID / null carrier
F. single-request self-consistent committed read projection
```

The architecture must not broaden these outcomes into new routes, resources, schema, migrations, dependencies, mutation-lock policy or unrelated CLI behavior.

## Normative document map

The planned owning documents are:

| Document | Status | Ownership |
|---|---|---|
| [`read-projections.md`](read-projections.md) | DESIGN IN PROGRESS — ADP-01 CLOSED; ADP-02 PARTIAL; ADP-03 OPEN | Public GET/read responsibility boundary; one-statement realization for the 22-route census; UoW/snapshot model; trusted read projectors; lifecycle carrier-decoding boundary; route-level projection patterns. |
| [`api.md`](api.md) | NOT YET WRITTEN | Public HTTP query/cursor realization; complete cursor identity rule; the two path-binding corrections; ObjectTemplate `parent_template_id` tri-state and strict malformed/duplicate behavior. |
| [`cli.md`](cli.md) | NOT YET WRITTEN | `Location` token/value-path grammar and materialization boundary; exact same-release response validation; nullable selector/query carrier semantics for `parent_template_id=null`. |
| [`verification.md`](verification.md) | NOT YET WRITTEN | Architecture-level deterministic evidence: 22 GET projection/statement checks, 12 cursor routes, eight 201 operations, lifecycle decoding boundary, parent-filter HTTP/CLI tri-state, non-delta/schema/dependency and read-coherence evidence. |

Additional architecture documents may be added only if an open design point cannot be owned cleanly by this map. Adding a document must not expand the frozen contract scope.

## Current AS-IS dependencies

The M3 TO-BE set depends materially on these delivered owners:

```text
docs/architecture/README.md
    global semantic-authority and coherent-read/corruption principle being intentionally revised by M3

docs/architecture/api.md
    22-route public read surface, filters, cursor/pagination contract, DTOs and failure boundary

docs/architecture/cli.md
    static operation registry, selector grammar, request construction and response validation

docs/architecture/datatype.md
    DataType lineage/version state used by read projections

docs/architecture/objecttemplate.md
    inheritance, exact versions, effective schema, capabilities and stable parent state

docs/architecture/object.md
    Object state, ownership and intrinsic lifecycle projections

docs/architecture/relationship.md
    RelationshipDefinition, factual Relationship and relationship lifecycle projections

docs/architecture/persistence.md
    persisted representation, structural constraints and codecs

docs/architecture/concurrency.md
    UnitOfWork / PostgreSQL snapshot realization and coherent_read infrastructure

docs/architecture/verification.md
    permanent verification policy and release evidence obligations
```

The architecture design must explicitly record every intentional TO-BE contradiction with these owners and every preserved dependency required by the contract.

## Coverage / ownership map

### Area A — CLI post-create correctness

Owner:

```text
architecture/cli.md
```

Must close:

```text
registered Location token grammar
request-value versus response-JSON-path resolution
literal materialization semantics
unresolvable expected Location -> protocol failure, not ordinary exception
all 8 registered 201 operations under one common rule
no hidden post-mutation enrichment change
```

### Area B — public reads

Primary owner:

```text
architecture/read-projections.md
```

Boundary projections:

```text
architecture/api.md
architecture/verification.md
```

Must close:

```text
mutation semantic certification versus read projection responsibility
single SQL business statement target for each of the 22 canonical GET/read routes
ordinary UoW / statement-snapshot realization where the projection is one statement
no public-business GET dependence on coherent_read() in the target census
single-request self-consistent committed projection guarantee
parent-target 404 versus existing-target empty-page preservation
trusted read projector boundary when mutation-oriented loaders are too broad
historical lifecycle carrier decoding versus transition certification
```

`coherent_read()` remains infrastructure and is not globally deprecated by M3.

### Cursor correctness

Owner:

```text
architecture/api.md
```

Verification owner:

```text
architecture/verification.md
```

Must close:

```text
query identity = route + membership-affecting path targets + membership-affecting filters + semantic presence bits
position = complete canonical ordering tuple
limit excluded from semantic identity
OBJ-GET-03 includes parent_object_id
OBJ-GET-06 includes object_id
lifecycle global/object-scoped distinction remains path-bound
ObjectTemplate omitted/root/exact-parent states remain cursor-distinct
```

### Area C — ObjectTemplate parent filter

HTTP owner:

```text
architecture/api.md
```

CLI owner:

```text
architecture/cli.md
```

Must close:

```text
HTTP omitted      -> no parent filter
HTTP UUID         -> exact stable parent
HTTP lowercase null -> roots only
malformed/empty/repeated -> existing invalid_request boundary

CLI omitted       -> no query pair
CLI UUID/human selector -> resolved UUID query pair
CLI explicit null -> literal lowercase null with no selector lookup

parent_filter_set remains internal only
```

## Design-point status

```text
ADP-01  CLOSED
ADP-02  PARTIAL — 10 / 22 routes architected
ADP-03  OPEN
ADP-04  OPEN
ADP-05  OPEN
ADP-06  OPEN
ADP-07  OPEN
ADP-08  OPEN
```

Current design progress:

```text
ADP-01 boundary       CLOSED
ADP-02 DataType       4 / 4 CLOSED
ADP-02 ObjectTemplate 6 / 6 CLOSED
ADP-02 total         10 / 22
next                 ADP-02 — Object family (6 routes)
```

### ADP-01 — CLOSED — Read projection responsibility and reusable persistence boundary

Owned by [`read-projections.md`](read-projections.md).

Frozen design boundary for downstream architecture work:

```text
HTTP adapter
    -> lexical carrier parsing / DTO serialization

application read service
    -> request semantics
    -> cursor validation
    -> request UoW ownership
    -> 404 / 200 / Page classification

persistence read projector
    -> complete persisted projection
    -> target-existence evidence where required
    -> representational carrier materialization
    -> no mutation semantic certification
```

The application owns the read UoW and public outcome classification; projectors run on the caller-owned connection and do not open nested UoWs. Representational decoding remains required, while mutation-semantic re-certification is forbidden in public GET projectors. Mutation loaders/validators remain strong and are not globally weakened for GET reuse. `coherent_read()` remains infrastructure but is not a target dependency for the 22 canonical public GETs.

### ADP-02 — PARTIAL — Complete 22-route one-statement projection matrix

The current projection-pattern vocabulary is owned by [`read-projections.md`](read-projections.md):

```text
RP-01  DIRECT PAGE
RP-02  DIRECT EXACT
RP-03  PARENT-ROOTED PAGE
RP-04  EXACT AGGREGATE / INDEPENDENT CHILD SETS
RP-05  RECURSIVE EXACT-CHAIN PROJECTION
RP-06  RECURSIVE STABLE-ANCESTRY PAGE
```

Closed route families:

```text
DataType        4 / 4
ObjectTemplate  6 / 6
               ------
               10 / 22
```

Key recursive distinction already frozen:

```text
effective schema
    -> exact ObjectTemplateVersion ancestry

relationship capabilities
    -> stable ObjectTemplate lineage ancestry
```

The remaining twelve routes must be classified under these patterns or introduce an additional pattern only where a genuinely different correctness shape is required.

### ADP-03 — OPEN — Historical lifecycle trusted decoder

Define the minimum persisted JSON/carrier decoding needed to construct typed lifecycle DTOs and the exact semantic checks that are removed from the read boundary.

### ADP-04 — OPEN — Cursor identity realization

Define one application cursor-identity construction rule covering all twelve routes, including the two path-target corrections and the ObjectTemplate parent-filter presence bit.

### ADP-05 — OPEN — ObjectTemplate nullable HTTP query carrier

Define the strict HTTP lexical parser/type boundary for UUID versus exact lowercase `null` while preserving query-parameter presence as a semantic distinction.

### ADP-06 — OPEN — CLI nullable selector/query carrier

Define how nullable selector-capable query parameters treat explicit null as a terminal carrier value, skip selector resolution and serialize lowercase `null` only in an allowed query location.

### ADP-07 — OPEN — CLI Location materialization grammar

Define the shared static token grammar, resolution precedence, materialization algorithm boundary and registry verification needed to support both top-level and dotted response JSON paths without Python format-field semantics.

### ADP-08 — OPEN — Verification architecture

Define deterministic permanent evidence and statement-count instrumentation for every contract criterion, including regression checks that mutation semantic validation remains intact.

## Architecture design rules

The set must preserve these distinctions:

```text
public contract outcome
    != architecture realization
    != local implementation decomposition

request validation
    != persisted semantic certification
    != representational carrier decoding

cursor semantic query identity
    != keyset position
    != page limit

current AS-IS ownership
    != M3 TO-BE delta ownership
```

Architecture may choose SQLAlchemy/SQL composition, helper boundaries and internal DTO/projector shapes only where those choices do not change frozen public semantics or project-wide technology.

## Freeze gate

This set may become `FINAL / FROZEN` only after:

```text
all planned owning documents are written
ADP-01 .. ADP-08 are CLOSED
all M3-OUT/AC requirements have one architecture owner or explicit preserved AS-IS owner
all 22 GET routes have a complete read/projection disposition
all 12 cursor-bearing routes have a complete identity/keyset disposition
HTTP and CLI parent-filter carriers are mutually consistent
CLI Location grammar is complete for all 8 registered 201 operations
verification obligations cover every frozen contract outcome
cross-document consistency sweep passes
no stale TODO / TBD / contradictory owner remains
```

Until then:

```text
ARCHITECTURE SET = DESIGN IN PROGRESS — NOT FROZEN
IMPLEMENTATION   = NOT AUTHORIZED
```

## Reopen discipline

If architecture work discovers that the frozen contract is contradictory or insufficient to determine an observable outcome, stop the affected design point and request formal contract reopening. Architecture must not silently reinterpret the frozen contract.
