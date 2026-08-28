# M4 WIP — TO-BE Object DETACH batch discovery closure

Status: ROUTE-LOCAL CLOSED DISCOVERY INPUT / M4 WIP / ALWAYS NON-NORMATIVE

## Scope

This note is the current route-local consolidation point for the M4 Object DETACH discovery.

It does not create architecture authority. Per project governance, every conclusion in this file remains subject to dependency-driven architecture-phase revalidation before implementation.

## Public signature

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}/detach
```

Request body:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>"
  ]
}
```

Success:

```http
204 No Content
```

The route is one-parent / one-slot / N-children and remains symmetric with the candidate ATTACH command surface.

## Static validation

Before opening the mutation Unit of Work:

```text
malformed/missing body
missing/empty child_object_ids
malformed UUID carriers
duplicate child_object_ids
invalid transport carriers
    -> 400 invalid_request

parent_object_id included in child_object_ids
    -> 422 semantic_validation_failed / self_reference
```

These failures require zero PostgreSQL statements.

## Candidate mutation semantics

DETACH is strict, non-convergent and atomic.

Every requested child must exist and must currently own the exact requested parent/slot edge.

```text
all N requested exact edges are current
    -> remove all N
    -> emit N DETACH_FROM lifecycle events
    -> commit once

any requested child missing
    -> fail whole batch
    -> remove nothing committed

any requested child exists but requested exact edge is absent/different
    -> fail whole batch
    -> remove nothing committed
```

An already-absent exact edge is not a successful no-op in this M4 candidate.

`ownership_conflict` intentionally covers existing-child current-state mismatches without extra diagnostic reads:

```text
child ownerless
child owned by another parent
child owned by same parent under another slot
```

## Candidate persistence dependency

The current preferred M4 ownership row is:

```text
object_components
    child_object_id              PK
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

The stable semantic slot identity is materialized as:

```text
SlotSemanticKey = (slot_declaring_template_id, slot_name)
```

`slot_declaring_template_id` is resolved and persisted at ATTACH admission time. It is not supplied by the DETACH caller.

The direct FK choice for `slot_declaring_template_id` remains a persistence/architecture handoff and is not closed by this route note.

## Schema-agnostic DETACH admission

Given the materialized ownership fact, DETACH does not need to reconstruct or re-certify the parent ObjectTemplate schema merely to remove an already-admitted current edge.

Normal DETACH data-path work excludes:

```text
ObjectTemplate effective-schema reconstruction
component_schema lookup
ObjectTemplate ancestry loading
slot declaration re-resolution from slot_name
target_template_id lookup
child lineage compatibility validation
cycle validation
OWNERSHIP_GRAPH_WRITE_GATE
immutable-model cache lookup
```

The deleted `object_components` row is the source for `slot_declaring_template_id` used by lifecycle history.

## Current candidate Unit of Work

```text
static validation
    -> 0 DB

BEGIN

Q1  parent stabilization
    current candidate: centralized LockPlan entry for parent Object

Q2  one fresh set-based PostgreSQL statement
    -> classify requested child existence
    -> bulk DELETE exact parent+slot+child ownership rows
    -> RETURNING persisted edge identity and lifecycle display material

Q3  one bulk INSERT DETACH_FROM
    -> no RETURNING

COMMIT

204 No Content
```

### Q1 candidate

Current route-local candidate reuses the delivered parent concurrency-owner model:

```text
LockPlan
    gate = none
    parent Object @ NKU
```

No PostgreSQL preparation is required before this plan because the parent identity is already known from the route.

A missing planned parent maps to:

```text
404 resource_not_found
```

This is a discovery candidate, not a statement that architecture must preserve the exact AS-IS lock realization unchanged.

### Q2 candidate

Input:

```text
parent_object_id
slot_name
requested child_object_ids[N]
```

Logical result:

```text
parent_canonical_name
missing_child_ids[]

deleted_edges[]:
    child_object_id
    child_canonical_name
    parent_object_id
    slot_declaring_template_id
    slot_name
```

The DELETE matches the public requested edge through:

```text
parent_object_id
slot_name
child_object_id
```

and obtains `slot_declaring_template_id` from the row actually deleted.

Admission uses only required execution output:

```text
missing_child_ids not empty
    -> ROLLBACK
    -> 422 referenced_resource_not_found

missing_child_ids empty
AND deleted edge count < requested count
    -> ROLLBACK
    -> 409 ownership_conflict

deleted edge count == requested count
    -> continue to Q3
```

Q2 deliberately prefers DELETE-first certification plus rollback over a separate pre-certification SELECT followed by DELETE. This avoids a success-path round trip and duplicate ownership-fact access.

### Q3 candidate

For each Q2 deleted edge, insert one lifecycle row:

```text
kind                       = DETACH_FROM
object_id                  = child_object_id
canonical_name             = child_canonical_name
destination_object_id      = parent_object_id
destination_canonical_name = parent_canonical_name
slot_declaring_template_id = slot_declaring_template_id
slot_name                  = slot_name
```

Q3 performs one bulk INSERT and does not reread Object, ownership or model-plane state.

No `RETURNING` is required because the route returns `204` and no later step consumes generated lifecycle row identities or timestamps.

Q2 and Q3 remain in the same semantic transaction. Q3 failure restores all Q2 deletions through rollback.

## Candidate failure precedence

```text
1. invalid wire/static request
   -> 400 invalid_request

2. self-reference known from request
   -> 422 semantic_validation_failed / self_reference

3. parent path target absent at Q1
   -> 404 resource_not_found

4. one or more requested child Objects absent at Q2
   -> 422 referenced_resource_not_found

5. all requested child Objects exist but exact requested edge set is incomplete
   -> 409 ownership_conflict

6. Q3 persistence failure
   -> rollback + normal known persistence-failure classification
```

No PostgreSQL statement may be executed solely to improve failure diagnostics.

## Lifecycle display-name policy

Parent and child canonical names in ownership lifecycle rows are historical display metadata, not ownership semantic identity.

The candidate does not add a child lock or extra reread solely to make these labels fresher. Q2 captures the names already needed for Q3.

## Candidate cost profile

Excluding BEGIN/COMMIT:

```text
success
    Q1 parent stabilization
    Q2 set-based classification + DELETE + RETURNING
    Q3 bulk lifecycle INSERT
    -> 3 PostgreSQL statements

failure detected by Q2
    Q1 + Q2
    -> 2 PostgreSQL statements + rollback

static failure
    -> 0 PostgreSQL statements
```

There is no cache warm/cold distinction.

Candidate round-trip count does not grow with child batch cardinality; row volume grows with N.

These are WIP candidate costs, not normative architecture budgets.

## Supersession map

The following WIPs remain useful historical discovery evidence but their route-local direction is superseded by this current consolidation:

```text
object-detach-discovery.md
    -> initial exploration; current closure is this file

object-detach-schema-agnostic.md
    -> semantic finding retained; superseded by the later reconciled schema-agnostic candidate

object-detach-no-parent-lock.md
    -> superseded

object-detach-parent-share-lock.md
    -> superseded

object-detach-two-statement-uow.md
    -> superseded statement split/count

object-detach-q1-parent-and-delete.md
    -> superseded Q1 responsibility/numbering

object-detach-q1-failure-mapping.md
    -> old Q1 carrier superseded; child-missing vs ownership-conflict taxonomy retained
```

Current supporting WIPs for this consolidation are:

```text
object-ownership-command-routes.md
object-detach-static-validation.md
object-detach-batch-non-convergent-semantics.md
object-components-physical-schema-discovery.md
object-detach-schema-agnostic-with-parent-lockplan.md
object-detach-lockplan-entry.md
object-detach-q2-set-based-delete.md
object-detach-lifecycle-bulk.md
```

All remain non-normative WIP inputs.

## Architecture handoff

Before implementation, the architecture phase must revalidate and compose this candidate globally, including at least:

```text
public API/failure contract propagation
strict non-convergent DETACH semantic delta
final object_components relational schema and migration
slot_declaring_template_id FK decision
final transaction boundary
final LockPlan/concurrency realization
DETACH x ATTACH ownership-fact sequencing
DETACH x DETACH sequencing
DETACH x parent SCHEMA_CHANGE
DETACH x parent/child DELETE reference lifetime
supported-path deadlock absence
lifecycle atomicity and snapshot semantics
verification-registry updates
physical index/EXPLAIN evidence
```

The architecture phase may adopt, modify, supersede or discard any realization choice recorded here while preserving or explicitly redefining the required semantic guarantees.

## Current discovery takeaway

```text
signature:
    POST /objects/{parent}/components/{slot}/detach
    { child_object_ids: [...] }
    -> 204

semantics:
    strict + atomic + non-convergent

runtime authority:
    current materialized object_components facts

model-plane work:
    none on normal DETACH path

candidate UoW:
    Q1 parent stabilization
    Q2 set-based classify + exact-edge bulk DELETE + RETURNING
    Q3 bulk DETACH_FROM INSERT without RETURNING

candidate success cost:
    3 PostgreSQL statements + COMMIT

architecture closure:
    explicitly deferred to the future M4 architecture phase
```
