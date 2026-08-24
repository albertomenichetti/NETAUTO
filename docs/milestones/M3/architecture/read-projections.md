# M3 — Public Read Projection Architecture

**Status:** DESIGN IN PROGRESS — ADP-01 CLOSED; ADP-02 / ADP-03 OPEN

**Authority:** M3 TO-BE ARCHITECTURE — PUBLIC READ PROJECTION OWNER

## Purpose and scope

This document owns the M3 TO-BE architecture for public business GET/read projection responsibilities.

It derives from the frozen M3 contract and changes only the explicit read-boundary delta. Delivered domain identities, mutation semantics, persistence schema, public DTOs, routing and failure behavior remain owned by the current AS-IS except where the frozen M3 contract explicitly changes them.

This document currently closes only:

```text
ADP-01 — Read projection responsibility and reusable persistence boundary
```

The complete route-by-route one-statement matrix (`ADP-02`) and the historical lifecycle trusted decoder details (`ADP-03`) remain open and will extend this owner without changing the responsibility boundary frozen below.

Implementation remains unauthorized while the M3 architecture set is not frozen.

## Frozen contract inputs

This owner realizes the read-side portions of:

```text
M3-OUT-03 — Read semantic-authority correction
M3-OUT-04 — Public read compatibility
M3-OUT-06 — Historical lifecycle trusted decoding
M3-OUT-08 — Regression and traceability closure

M3-AC-04 — Twenty-two-route read compatibility
M3-AC-05 — Request and path-target failure preservation
M3-AC-06 — No read-side mutation-semantic re-certification
M3-AC-07 — Materially undecodable carrier boundary
M3-AC-08 — Lifecycle historical decoding
M3-AC-18 — Complete outcome traceability
M3-AC-19 — Single-request committed read coherence
```

Cursor construction details remain owned by `api.md`; verification realization remains owned by `verification.md`.

## ADP-01 — CLOSED decision

### 1. Read-path architecture boundary

Every canonical public business GET/read path follows this responsibility chain:

```text
HTTP adapter
    |
    | lexical request-carrier parsing
    | public DTO serialization
    v
application read service
    |
    | request semantics
    | cursor query-identity/key validation
    | request Unit of Work ownership
    | public outcome classification
    |     404 / 200 / Page / internal failure
    v
persistence read projector
    |
    | complete persisted projection for the request
    | target-existence evidence where required
    | row / scalar / JSON carrier materialization
    | no mutation semantic certification
    v
typed application/public projection
```

The layers may use existing modules and local helper structures. M3 does not require a new package, class hierarchy or framework abstraction. The architectural requirement is the ownership boundary, not a particular code shape.

### 2. Application read-service responsibility

The application read service owns semantics that arise from the request rather than from re-certifying persisted business state.

It owns:

```text
request-level dependency rules
    example: template_version requires template_id

cursor validation
    route/query identity compatibility
    key carrier shape/type validation

request Unit of Work
    open/close the ordinary read UoW used by the projector

path-target public classification
    missing target -> resource_not_found where defined
    existing target + zero members -> successful empty page where defined

public outcome composition
    Page/items/next-cursor assembly
    application failure classification
```

The application service may receive explicit target-presence information from a persistence projection. Persistence supplies the fact; application owns the public `404` versus successful-empty classification.

### 3. Persistence read-projector responsibility

A persistence read projector is an explicit architectural role: a persistence operation whose purpose is to materialize the complete persisted fact set required by one public read projection.

It owns:

```text
relational fact selection
joins / recursion / aggregation required by the projection
parent/target existence evidence when collection semantics require it
canonical route ordering and keyset predicate realization
row-to-projection carrier materialization
persisted JSON/scalar extraction needed by the typed projection
```

A projector executes on the caller-owned read connection. It does not open, commit or nest its own Unit of Work.

The exact reusable projector types and route patterns are owned by ADP-02.

### 4. Semantic certification is forbidden in public GET projectors

A public read projector must not answer this question:

```text
"Would this persisted state pass current mutation admission/transition validation?"
```

Therefore public GET/read paths must not invoke semantic certification merely to re-prove state already admitted and persisted by mutation ownership.

Examples include:

```text
default-version publication admissibility re-certification
persisted aggregate domain validation
inheritance cycle/agreement/admissibility re-certification
runtime schema/DataType resolution used only to prove persisted values again
ownership slot/parent semantic revalidation
factual Relationship Definition/schema/topology certification
historical lifecycle transition correctness certification
```

Mutation paths retain all semantic validation needed for admission, transition correctness and protected-state freshness. M3 does not weaken those validators.

### 5. Representational decoding remains required

Read-time semantic certification and representational decoding are different responsibilities.

```text
semantic certification
    "is the persisted state semantically admissible under mutation rules?"
    -> forbidden in public GET/read projection

representational decoding
    "can these persisted facts be converted into the required typed projection?"
    -> required in public GET/read projection
```

Representational decoding may therefore require:

```text
row/column extraction
UUID conversion
integer/boolean/string conversion
closed-enum materialization
required persisted field presence
JSON object/array shape needed by the response carrier
historical before/after snapshot materialization
```

If required persisted state is structurally or representationally undecodable, the complete public representation may fail with the existing bounded internal-error boundary. A read must not fabricate required fields, repair persisted state or silently omit required members.

ADP-03 will freeze the exact historical lifecycle decoder boundary under this rule.

### 6. Reuse rules

M3 does not prohibit code reuse. It prohibits importing mutation-owned semantic responsibility into a read.

Reusable code is allowed when it is semantically neutral, for example:

```text
row -> typed carrier mapping
UUID / enum / primitive carrier conversion
query-fragment construction
pure ordering/key helpers
pure response-shape assembly
```

Reuse is not allowed when it causes the GET path to:

```text
run mutation admission or transition validation
load dependencies solely to certify persisted semantics
invoke a mutation-oriented aggregate validator as a read prerequisite
perform extra persistence statements solely because the reused loader is broader than the public projection
```

Where an existing mutation-oriented loader is materially broader than a GET projection, the GET uses a dedicated trusted read projector instead of weakening the mutation loader globally.

### 7. Unit of Work and snapshot ownership

The application read service owns the request read Unit of Work and supplies its connection to the persistence projector.

For the M3 canonical public GET census, ADP-02 must realize each complete public projection as one authoritative business SQL statement. Such a statement uses its PostgreSQL statement snapshot and therefore does not require `coherent_read()`.

This preserves the frozen public guarantee:

```text
one request
    -> one self-consistent committed projection
```

while continuing not to promise cross-request repeatable membership.

`coherent_read()` remains valid infrastructure for workflows outside this M3 public-GET census that genuinely require a coherent multi-statement read. M3 does not deprecate or remove it globally.

### 8. Parent/target existence and empty collection semantics

For a path-scoped collection whose public contract distinguishes an absent target from an existing target with no matching members, the persistence projection must carry enough information to distinguish:

```text
target absent
    -> application classifies 404 resource_not_found

target present + zero matching rows
    -> application returns successful empty page
```

ADP-02 will choose the one-statement relational pattern for each affected route. An outer-join, target-rooted subquery or equivalent pattern is valid only if it preserves this distinction and the canonical keyset behavior.

## Preserved AS-IS responsibilities

ADP-01 does not change:

```text
PostgreSQL as the only persistence backend
PK / UNIQUE / FK / CHECK / NOT NULL structural authority
mutation Unit-of-Work semantic admission and transition ownership
mutation lock-plan and concurrency guarantees
public DTO field meanings and route identities
public bounded failure envelope
opaque keyset pagination contract
exact persisted identities and bindings
schema / migration / dependency baseline
```

The delivered concurrency architecture already permits a single authoritative projection statement to use its statement snapshot; M3 specializes that existing mechanism across the canonical public GET census.

## Intentional AS-IS contradiction

The delivered global read principle treated persisted semantic invariant corruption as a reason to fail the complete representation after read-side certification.

M3 intentionally narrows that principle:

```text
mutation
    -> semantic certification

database
    -> structural invariant enforcement

public GET/read
    -> request/cursor validation
    -> persisted fact projection
    -> representational decoding
    -> no mutation-semantic re-certification
```

Representationally undecodable required state still fails safely. M3 introduces neither read-time repair nor silent corruption tolerance.

This contradiction is authorized by the frozen M3 contract and must be propagated to the delivered AS-IS during post-implementation consolidation.

## Downstream architecture constraints

ADP-02 must comply with ADP-01 by ensuring every one of the 22 canonical GET/read routes:

```text
has one complete persistence projection boundary
uses no mutation semantic validator as a read prerequisite
preserves target-absence versus empty-collection behavior
preserves canonical ordering/filtering/keyset semantics
observes one committed statement snapshot
requires no public-GET coherent_read() dependency
```

ADP-03 must comply with ADP-01 by defining lifecycle decoding exclusively as representational materialization, not transition certification.

`api.md` must preserve request/cursor and failure classification ownership without moving persistence semantic validation into the HTTP adapter.

`verification.md` must prove both sides of the boundary:

```text
public GETs do not re-certify mutation semantics
mutation semantic validation remains intact
```

## ADP status

```text
ADP-01  CLOSED
ADP-02  OPEN
ADP-03  OPEN
```

No implementation authority is created by this closure. The architecture set remains `DESIGN IN PROGRESS — NOT FROZEN`.
