# M3 — Architecture Set

**Architecture set status:** DESIGN IN PROGRESS — NOT FROZEN

**Authority:** M3 TO-BE ARCHITECTURE SET CONTROL

## Purpose and authority boundary

This directory defines the M3 TO-BE architecture required to realize the frozen milestone contract in [`../contract.md`](../contract.md).

The architecture starts from the delivered AS-IS under `docs/architecture/` and may change only the explicit M3 deltas frozen by the contract. Delivered guarantees not explicitly changed by M3 remain owned by their current AS-IS documents and must not be duplicated as competing M3 authority.

This README controls document ownership, design-point state, coverage, freeze scope and cross-document consistency. Implementation remains unauthorized until the architecture set is `FINAL / FROZEN`, `steps.md` is subsequently frozen and `status.md` explicitly authorizes an implementation slice.

## Frozen contract inputs

The set must realize exactly:

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

The architecture must not broaden these outcomes into new routes, resources, schema, migrations, dependencies, mutation-lock policy or unrelated CLI behavior.

## Normative document map

| Document | Status | Ownership |
|---|---|---|
| [`read-projections.md`](read-projections.md) | DESIGN IN PROGRESS — ADP-01 CLOSED; ADP-02 PARTIAL 16/22; ADP-03 OPEN | Public GET/read responsibility boundary; one-statement projection patterns and route matrix; read UoW/snapshot model; trusted projector rules; lifecycle decoding boundary. |
| [`api.md`](api.md) | NOT YET WRITTEN | Public HTTP cursor/query realization; complete cursor identity rule; two path-binding corrections; ObjectTemplate `parent_template_id` tri-state. |
| [`cli.md`](cli.md) | NOT YET WRITTEN | `Location` token/value-path grammar; exact response validation; nullable selector/query carrier for `parent_template_id=null`. |
| [`verification.md`](verification.md) | NOT YET WRITTEN | Deterministic evidence for 22 GETs, 12 cursor routes, eight 201 operations, lifecycle decoding, parent-filter tri-state, read coherence and non-delta obligations. |

Additional architecture documents may be added only when an open design point cannot be owned cleanly by this map. Adding a document must not expand the frozen contract scope.

## Current AS-IS dependencies

Material current owners include:

```text
docs/architecture/README.md
    global semantic-authority and read-corruption principle intentionally revised by M3

docs/architecture/api.md
    public routes, DTOs, filters, pagination and failure boundary

docs/architecture/cli.md
    registry, selector grammar, request construction and response validation

docs/architecture/datatype.md
    DataType lineage/version semantics

docs/architecture/objecttemplate.md
    stable/exact inheritance, effective schema, capabilities and parent state

docs/architecture/object.md
    Object, ownership and lifecycle projections

docs/architecture/relationship.md
    RelationshipDefinition/Relationship projection semantics

docs/architecture/persistence.md
    persisted representation, structural constraints and codecs

docs/architecture/concurrency.md
    UnitOfWork, statement snapshot and coherent_read infrastructure

docs/architecture/verification.md
    permanent verification policy
```

Every intentional TO-BE contradiction must be explicit in an M3 owner. Every preserved dependency remains traceable to its current owner.

## Area ownership

### Area A — CLI post-create correctness

Owner: `architecture/cli.md`.

Must close:

```text
registered Location token grammar
request-value versus response-JSON-path resolution
literal materialization semantics
unresolvable expected Location -> cli_protocol_error
all 8 registered 201 operations under one common rule
no hidden post-mutation enrichment change
```

### Area B — public reads

Primary owner: `architecture/read-projections.md`.
Boundary owners: `architecture/api.md`, `architecture/verification.md`.

Must close:

```text
mutation semantic certification versus read projection responsibility
one business SQL statement for each of 22 canonical GET/read routes
ordinary UoW / statement snapshot realization
no target GET dependence on coherent_read()
single-request self-consistent committed projection
404 versus empty/null distinctions
trusted read projector boundary
historical carrier decoding versus transition certification
```

`coherent_read()` remains valid infrastructure outside this M3 census.

### Cursor correctness

Owner: `architecture/api.md`.
Verification owner: `architecture/verification.md`.

Must close:

```text
query identity = route + membership-affecting path target(s) + membership-affecting filters + semantic presence bits
position = complete canonical ordering tuple
limit excluded from semantic identity
OBJ-GET-03 includes parent_object_id
OBJ-GET-06 includes object_id
lifecycle global/object-scoped distinction remains path-bound
ObjectTemplate omitted/root/exact-parent states remain cursor-distinct
```

### Area C — ObjectTemplate parent filter

HTTP owner: `architecture/api.md`.
CLI owner: `architecture/cli.md`.

Must close:

```text
HTTP omitted         -> no parent filter
HTTP UUID            -> exact stable parent
HTTP lowercase null  -> roots only
malformed/empty/repeated -> existing invalid_request boundary

CLI omitted          -> no query pair
CLI UUID/human       -> resolved UUID query pair
CLI explicit null    -> literal lowercase null, no selector lookup

parent_filter_set remains internal only
```

# Design-point status

```text
ADP-01  CLOSED
ADP-02  PARTIAL — 16 / 22 routes architecturally defined
ADP-03  OPEN
ADP-04  OPEN
ADP-05  OPEN
ADP-06  OPEN
ADP-07  OPEN
ADP-08  OPEN
```

Current route-family progress inside ADP-02:

```text
DataType             4 / 4 CLOSED
ObjectTemplate       6 / 6 CLOSED
Object               6 / 6 CLOSED
RelationshipDef      0 / 4 OPEN
Relationship         0 / 1 OPEN
Global lifecycle     0 / 1 OPEN
------------------------------
total               16 / 22
```

## ADP-01 — CLOSED — Read projection responsibility

Owned by [`read-projections.md`](read-projections.md).

Frozen boundary:

```text
HTTP adapter
    -> lexical parsing / DTO serialization

application read service
    -> request semantics
    -> cursor validation
    -> ordinary read UoW ownership
    -> public outcome classification

persistence read projector
    -> complete persisted projection
    -> target-existence evidence
    -> required contextual completion
    -> representational decoding
    -> NO mutation semantic certification
```

Mutation loaders/validators remain strong. Required public fields may be completed from persisted context, but unmaterializable members must fail rather than disappear silently. `coherent_read()` remains infrastructure but is not a target dependency for the 22 canonical GETs.

## ADP-02 — PARTIAL — Complete 22-route one-statement matrix

Owned by [`read-projections.md`](read-projections.md).

Current named patterns:

```text
RP-01  DIRECT PAGE
RP-02  DIRECT EXACT
RP-03  PARENT-ROOTED PAGE
RP-04  EXACT AGGREGATE / INDEPENDENT CHILD SETS
RP-05  RECURSIVE EXACT-CHAIN PROJECTION
RP-06  RECURSIVE STABLE-ANCESTRY PAGE
RP-07  TARGET-ROOTED CONTEXT-COMPLETED PAGE
RP-08  TARGET-ROOTED OPTIONAL PROJECTION
```

Closed route families:

```text
DataType        4 / 4
ObjectTemplate  6 / 6
Object          6 / 6
```

Notable frozen distinctions:

```text
effective schema       -> exact ObjectTemplateVersion ancestry
relationship capability -> stable ObjectTemplate lineage ancestry

Object components
    -> page ownership facts first
    -> exact-chain context completes slot_declaring_template_id
    -> missing/ambiguous required context is internal failure, not silent omission

Object owner
    -> absent child = 404
    -> existing detached child = 200 null
    -> existing ownership must materialize exactly one declaring slot

Object relationships
    -> derive/deduplicate public semantic views before keyset/limit semantics
    -> raw runtime-row limiting before public dedupe is forbidden when behavior changes
```

Next dependency-ordered work:

```text
RelationshipDefinition 4-route family
-> factual Relationship exact GET
-> global lifecycle page
-> ADP-02 closure
```

## ADP-03 — OPEN — Historical lifecycle trusted decoder

Define the minimum persisted JSON/carrier decoding needed to construct typed lifecycle DTOs and the exact mutation-semantic checks removed from the read boundary.

## ADP-04 — OPEN — Cursor identity realization

Define one application cursor-identity construction rule covering all twelve routes, including the two Object path-target corrections and ObjectTemplate parent-filter presence semantics.

## ADP-05 — OPEN — ObjectTemplate nullable HTTP query carrier

Define strict UUID versus exact lowercase `null` lexical parsing while preserving raw query presence.

## ADP-06 — OPEN — CLI nullable selector/query carrier

Define explicit null as terminal for nullable selector-capable query parameters and allow lowercase `null` serialization only in the permitted query location.

## ADP-07 — OPEN — CLI Location materialization grammar

Define token grammar, request/response path resolution precedence, materialization and registry verification without Python format-field semantics.

## ADP-08 — OPEN — Verification architecture

Define deterministic permanent evidence and statement-count instrumentation for every frozen contract criterion, including regression proof that mutation semantic validation remains intact.

# Architecture design rules

The set preserves these distinctions:

```text
public contract outcome
    != architecture realization
    != local implementation decomposition

request validation
    != persisted semantic certification
    != representational decoding

projection completion
    != semantic certification

cursor semantic identity
    != keyset position
    != page limit

current AS-IS ownership
    != M3 TO-BE delta ownership
```

SQLAlchemy syntax, local helper names and equivalent query decomposition remain implementation choices only where the frozen logical pattern and guarantees are preserved.

# Freeze gate

The architecture set may become `FINAL / FROZEN` only after:

```text
all planned owner documents are written
ADP-01 .. ADP-08 are CLOSED
all M3-OUT/AC requirements have an M3 TO-BE owner or explicit preserved AS-IS owner
22 / 22 GET routes have a complete projection disposition
12 / 12 cursor-bearing routes have a complete identity/keyset disposition
HTTP and CLI parent-filter carriers are mutually consistent
CLI Location grammar covers all 8 registered 201 operations
verification obligations cover every frozen contract outcome
cross-document consistency sweep passes
no stale TODO / TBD / contradictory owner remains
```

Until then:

```text
ARCHITECTURE SET = DESIGN IN PROGRESS — NOT FROZEN
IMPLEMENTATION   = NOT AUTHORIZED
```

# Reopen discipline

If architecture work discovers that the frozen contract is contradictory or insufficient to determine an observable outcome, the affected design point enters STOP and requires formal contract reopening. Architecture must not silently reinterpret the frozen contract.