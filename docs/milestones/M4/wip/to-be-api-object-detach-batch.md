# M4 WIP — TO-BE Object DETACH batch discovery closure

Status: PUBLIC/SEMANTIC CONTRACT RETAINED / EXECUTION PATH REOPENED / M4 WIP / ALWAYS NON-NORMATIVE

## Revalidation notice

This consolidation is reopened by [`object-component-slots-data-plane-materialization.md`](object-component-slots-data-plane-materialization.md).

The public batch DETACH semantics remain the current checkpoint. The previous parent-stabilization/LockPlan statement and the resulting `3 PostgreSQL statements + COMMIT` success cost are no longer the preferred candidate if ownership edges reference current materialized slot rows and that FK becomes the SCHEMA_CHANGE arbitration point.

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

The route remains one-parent / one-slot / N-children and symmetric with ATTACH.

## Static validation retained

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

## Mutation semantics retained

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

An already-absent exact edge is not a successful no-op.

`ownership_conflict` continues to cover current-state mismatches without diagnostic-only reads:

```text
child ownerless
child owned by another parent
child owned by same parent under another slot
```

## Current persistence candidate

Current cross-operation candidate:

```text
object_component_slots
    object_id
    slot_declaring_template_id
    slot_name
    target_template_id

object_components
    child_object_id              PK
    parent_object_id             NOT NULL
    slot_declaring_template_id   NOT NULL
    slot_name                    NOT NULL
```

with:

```text
FK object_components semantic slot
    -> object_component_slots current semantic slot
```

The deleted ownership row remains the factual source of the exact semantic slot identity used by lifecycle history.

## Schema-agnostic DETACH admission retained

DETACH still does not need to reconstruct or recertify ObjectTemplate schema merely to remove an already-admitted edge.

Normal DETACH excludes:

```text
ObjectTemplate effective-schema reconstruction
component_schema lookup
ObjectTemplate ancestry loading
slot declaration re-resolution
target_template_id lookup
child lineage compatibility validation
cycle validation
OWNERSHIP_GRAPH_WRITE_GATE
immutable-model cache lookup
```

## Reopened parent stabilization

The earlier candidate used:

```text
Q1 parent Object stabilization / LockPlan parent @ NKU
```

primarily as a generic rendezvous with parent SCHEMA_CHANGE.

With edge->current-slot FK arbitration, the relevant SCHEMA_CHANGE race becomes narrower:

```text
DETACH removes last edge first
    -> slot REMOVE/replacement may proceed

SCHEMA_CHANGE attempts slot REMOVE/replacement while edge still exists
    -> referenced slot transition is blocked at FK boundary
```

Removing an edge cannot create a schema or graph violation. Therefore a dedicated parent Object stabilization statement is no longer the preferred route-local candidate solely for SCHEMA_CHANGE sequencing.

Global architecture must still prove DETACH x SCHEMA_CHANGE and DELETE interleavings before implementation.

## Current candidate Unit of Work

```text
static validation
    -> 0 DB

BEGIN

Q1  one fresh set-based PostgreSQL statement
    -> prove parent existence
    -> classify requested child existence
    -> bulk DELETE exact parent+slot+child ownership rows
    -> RETURNING persisted edge identity and lifecycle display material

Q2  one bulk INSERT DETACH_FROM
    -> no RETURNING

COMMIT

204 No Content
```

### Q1 logical result

Input:

```text
parent_object_id
slot_name
requested child_object_ids[N]
```

Logical result:

```text
parent_exists
parent_canonical_name
missing_child_ids[]

deleted_edges[]:
    child_object_id
    child_canonical_name
    parent_object_id
    slot_declaring_template_id
    slot_name
```

The statement must preserve these outcomes without a preliminary parent lock/read:

```text
parent absent
    -> rollback
    -> 404 resource_not_found

parent present + missing child ids
    -> rollback
    -> 422 referenced_resource_not_found

all children exist + deleted edge count < requested count
    -> rollback
    -> 409 ownership_conflict

deleted edge count == requested count
    -> continue
```

DELETE-first certification plus rollback remains preferred over a separate ownership precheck.

## Lifecycle retained

For each deleted edge, insert one `DETACH_FROM` lifecycle row using:

```text
child_object_id
child canonical_name
parent_object_id
parent canonical_name
slot_declaring_template_id
slot_name
```

The lifecycle write remains one bulk statement in the same transaction. No reread of ObjectTemplate or ownership state is required.

Canonical names remain best-effort historical display metadata.

## Candidate failure precedence

```text
1. invalid wire/static request
   -> 400 invalid_request

2. self-reference known from request
   -> 422 semantic_validation_failed / self_reference

3. parent path target absent in Q1
   -> 404 resource_not_found

4. one or more requested child Objects absent in Q1
   -> 422 referenced_resource_not_found

5. all requested child Objects exist but exact requested edge set is incomplete
   -> 409 ownership_conflict

6. lifecycle/persistence failure
   -> rollback + normal known persistence-failure classification
```

No PostgreSQL statement may be executed solely to improve failure diagnostics.

## Revalidated candidate cost

Excluding BEGIN/COMMIT:

```text
success
    Q1 set-based parent/child classification + DELETE + RETURNING
    Q2 bulk lifecycle INSERT
    -> 2 PostgreSQL statements

failure detected by Q1
    -> 1 PostgreSQL statement + rollback

static failure
    -> 0 PostgreSQL statements
```

There is still no cache warm/cold distinction and round-trip count does not grow with batch cardinality.

Further fusion of DELETE + lifecycle is a separate discovery question and is not assumed here.

## Current route-local state

Retained:

- explicit `/detach` public route;
- strict + atomic + non-convergent semantics;
- semantic edge identity persisted on ownership row;
- no normal model-plane/cache work;
- DELETE-first set-based certification;
- one bulk lifecycle insert;
- no diagnostic-only DB reads.

Reopened/superseded:

```text
parent stabilization / LockPlan parent @ NKU
3-statement success cost
generic parent-lock sequencing with SCHEMA_CHANGE
```

Architecture handoff now explicitly includes the final `object_component_slots` FK design and DETACH x SCHEMA_CHANGE relational-locking proof.
