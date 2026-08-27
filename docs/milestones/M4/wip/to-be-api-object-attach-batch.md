# M4 WIP — TO-BE Object ATTACH batch contract

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note records the caller-facing batch shape for Object ownership ATTACH.

## Public signature

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

Path:

```text
parent_object_id UUID
slot_name        effective component slot name
```

Request body:

```json
{
  "child_object_ids": [
    "<child-1>",
    "<child-2>",
    "<child-3>"
  ]
}
```

Candidate request constraints:

- `child_object_ids` is non-empty;
- duplicate child ids in the same request are rejected rather than given ordering semantics;
- request ordering has no semantic meaning.

Successful mutation returns:

```http
204 No Content
```

The operation does not return persisted `object_components` rows. Public reads use the Object component read surface.

## Why batch by slot

ATTACH is commonly population-shaped rather than single-edge shaped. A caller may need to attach multiple Objects to the same effective slot of one parent, for example:

```text
server-1
  interfaces
    eth0
    eth1
    eth2
    eth3
```

A single-child path such as:

```text
PUT /objects/{parent}/components/{slot}/{child}
```

would force N HTTP requests and repeat parent/slot stabilization and model resolution N times.

The batch route instead amortizes work that is naturally shared across every requested child:

```text
one request
one mutation UoW
one parent stabilization
one exact parent-slot resolution
one immutable schema/cache resolution
one ownership-cycle add gate acquisition, if the final concurrency design retains a global gate
bulk child/current-owner reads
bulk compatibility evaluation
bulk edge insertion
bulk lifecycle event insertion
one commit
```

This does **not** imply that the final PostgreSQL realization uses literally one row lock total. Child-specific ownership arbitration may still require deterministic locking or rely on the `child_object_id` uniqueness authority. The important frozen property is that per-parent/per-slot coordination is paid once for the whole batch rather than once per child HTTP request.

## Mutation semantics

The batch is atomic:

```text
all requested new attachments are admissible
    -> persist all required new edges/events
    -> commit once

any requested child is inadmissible
    -> persist none of the batch
    -> rollback/fail
```

Reasons for batch failure include, subject to later exact error mapping:

- parent absent;
- requested slot absent from the parent's current exact effective schema;
- child absent;
- child is the parent itself;
- child stable lineage is incompatible with the slot target lineage;
- child is currently owned by a different parent/semantic edge;
- adding any requested edge would violate ownership acyclicity.

## Existing identical edge

An already-current identical semantic edge converges successfully and does not require a duplicate persisted edge.

Semantic identity is:

```text
parent_object_id
slot_declaring_template_id
slot_name
child_object_id
```

The persisted ownership table remains one-owner shaped with `child_object_id` as the unique current child ownership authority.

For a mixed request, for example:

```text
10 requested child ids
7 already attached through the same semantic edge
3 genuinely new
```

the successful batch may persist only the 3 new edges and their corresponding ATTACH lifecycle events, then return one `204 No Content`.

## Lifecycle direction

Lifecycle remains edge-oriented rather than request-oriented. A batch HTTP request may therefore create zero or more ATTACH lifecycle rows, one for each genuinely new ownership edge.

Exact lifecycle payload and write realization remain to be reconciled during the route-local data-path/concurrency pass.

## Preliminary parent and slot resolution

The first authoritative data-plane read obtains only the current parent Object binding needed to identify the exact governing ObjectTemplateVersion:

```text
parent object
    -> id
    -> template_id
    -> template_version
```

Parent current existence remains PostgreSQL authority.

The requested effective slot is then resolved cache-first from immutable exact ObjectTemplate knowledge:

```text
ImmutableObjectTemplateCache[(parent.template_id, parent.template_version)]
    facet = component_schema
```

### Cache HIT

The READY `component_schema` facet resolves `slot_name` entirely in memory and yields the semantic information needed by ATTACH, including:

```text
slot_name
slot_declaring_template_id
target_template_id
```

No PostgreSQL semantic query is issued on this warm path.

### Cache MISS / partial entry

A missing or non-READY `component_schema` facet does not create an alternate semantic path. The command loads only the missing immutable effective-component knowledge for the exact parent OTV, canonicalizes/compiles it, marks the facet READY, and resumes the same cache-hit resolution path.

Conceptually:

```text
component_schema MISS
    -> bounded load of exact immutable effective components
    -> compile/canonicalize
    -> component_schema READY
    -> resolve slot_name from cache
```

The full ObjectTemplate validation facet is not required: ATTACH does not need effective properties, DataType semantics or property validators merely to resolve a component slot.

The parent Object may currently be pinned to a `DEPRECATED` exact OTV. That exact schema remains immutable and continues to govern the existing Object, so no current OTV lifecycle-status admission query is required for slot resolution.

## Child batch semantic direction

The request is not restricted to one child ObjectTemplate lineage. Different child lineages may coexist in the same batch provided each stable `template_id` is compatible with the resolved slot `target_template_id`.

For example, a slot targeting `NetworkInterface` may accept in one batch Objects whose stable lineages are `EthernetInterface`, `WirelessInterface` and `BondInterface`, if each is a descendant/compatible lineage.

The child read and compatibility check must therefore be bulk-oriented rather than N+1:

```text
bulk read requested child Objects
    -> verify every requested id exists
    -> reject parent==child
    -> collect DISTINCT child.template_id values

for each distinct child.template_id
    -> verify stable-lineage compatibility with slot.target_template_id
```

The exact child `template_version` is irrelevant to slot compatibility.

Compatibility checks should consume stable ObjectTemplate ancestry cache knowledge. Missing ancestry facts should be filled in bounded bulk rather than through one query per child or per distinct lineage.

## Relation to reads and DETACH

The route aligns with the already-agreed slot-specific component collection read:

```text
GET  /objects/{parent_object_id}/components/{slot_name}
POST /objects/{parent_object_id}/components/{slot_name}
```

`POST` adds membership; it does not replace the full slot collection and therefore never implies hidden DETACH operations.

A batch DETACH shape should be evaluated independently when DETACH is reviewed.

## Route-local status

Frozen here:

- batch-by-slot public shape;
- no child id in the path;
- list request body;
- success `204 No Content`;
- atomic batch semantics;
- identical-edge convergence direction;
- one parent/slot coordination context per batch rather than per child request;
- parent exact OTV component-slot resolution is cache-first;
- only the `component_schema` facet is required for ATTACH slot resolution;
- cache miss fills the immutable facet and resumes the same READY path;
- heterogeneous child stable lineages are allowed in one batch;
- child compatibility is evaluated against the slot target using stable-lineage ancestry, not exact child versions.

Still to close:

- exact bulk child/current-owner read shape;
- warm/cold ancestry-cache fill path;
- current-owner arbitration;
- cycle detection and concurrency realization;
- exact statement count;
- bulk SQL realization;
- lifecycle payload/write shape;
- final relational/index implications.
