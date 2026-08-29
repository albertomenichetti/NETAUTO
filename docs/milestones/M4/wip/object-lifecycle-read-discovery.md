# M4 WIP — Object lifecycle read discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the M4 discovery around `GET /objects/{id}/lifecycle-events` after the public `GET /objects/{id}` representation was reopened to include direct component children and after lifecycle payload responsibility was revalidated during the Object.RENAME, Object.DATA_CHANGE and Object.SCHEMA_CHANGE full sweeps.

This is discovery only. It does not freeze the complete lifecycle public contract and does not authorize implementation.

## General lifecycle payload principle

M4 has ratified the following general rule:

```text
lifecycle payload
    = complete exact semantic transition owned by the operation

not automatically
    = complete aggregate before snapshot
      + complete aggregate after snapshot
```

Therefore lifecycle event families must not be forced into one complete Object snapshot shape merely for DTO/storage uniformity.

Current Object GET representation and historical mutation payloads have different responsibilities.

## Concrete RENAME consequence

Consider current Object state:

```text
server-1
    hostname = srv01

    interfaces:
        eth0
        eth1
```

and a rename:

```text
server-1 -> web-01
```

RENAME owns only:

```text
canonical_name: server-1 -> web-01
```

Its exact lifecycle payload therefore does not need to duplicate:

```text
template_id
template_version
properties
components
ownership
Relationships
```

Conceptually:

```json
{
  "before": {
    "canonical_name": "server-1"
  },
  "after": {
    "canonical_name": "web-01"
  }
}
```

with Object identity already carried by the lifecycle event itself.

This is an **exact** historical transition, not an approximate one.

## Concrete DATA_CHANGE consequence

DATA_CHANGE owns only the runtime-property transition actually produced by the accepted request effects.

Its ratified historical payload is therefore an exact changed-property delta, not complete Object snapshots.

Event context includes:

```text
object_id
exact ObjectTemplate binding:
    template_id
    template_version
```

Each changed property is identified by:

```text
(declaring_template_id, property_name)
```

and records:

```text
before = canonical value | ABSENT
after  = canonical value | ABSENT
```

Only properties whose semantic state actually changed are included. No-op requested effects are omitted from the event, and a request with zero actual changes emits no DATA_CHANGE event when no-op recognition is available on the normal apply path without material extra work.

DATA_CHANGE does not duplicate:

```text
canonical_name
unchanged properties
components
ownership
Relationships
```

The exact JSON/DTO carrier remains Lifecycle API/persistence work; the semantic delta above is already fixed by the Object mutation owner.

## Concrete SCHEMA_CHANGE consequence

SCHEMA_CHANGE owns the real transition between two exact ObjectTemplate bindings plus the runtime-property state changes produced by that migration.

Its ratified historical payload is:

```text
object_id

binding transition
    template_id
    source_version
    target_version

changed runtime properties only
    semantic identity:
        (declaring_template_id, property_name)

    before:
        canonical value | ABSENT

    after:
        canonical value | ABSENT
```

A successful real binding transition emits exactly one SCHEMA_CHANGE event even when the property-change list is empty:

```text
T@4 -> T@5
property_changes = []
```

Property semantic replacement is represented as separate old-semantic-key removal and new-semantic-key addition rather than as one false name-based transition.

SCHEMA_CHANGE does not duplicate:

```text
canonical_name
revision
complete properties before/after snapshots
unchanged properties
object_component_slots materialized rows
object_components / ownership membership
Relationships
effective-schema snapshots
```

The current slot materialization changes atomically with the new binding but is derived from that exact binding and is not copied into the lifecycle payload. Ownership membership itself remains unchanged on successful normal SCHEMA_CHANGE; blockers fail instead of causing implicit DETACH/rebind.

Equal-target semantic no-op and failed/rolled-back SCHEMA_CHANGE attempts emit no lifecycle event.

The exact JSON/detail carrier remains Lifecycle API/persistence work; the operation-owned semantic content is already fixed by the SCHEMA_CHANGE owner.

## Components remain outside intrinsic mutation payloads

Enriching current `GET /objects/{id}` with direct components still does not imply embedding component state in intrinsic lifecycle payloads.

Ownership changes are already represented by distinct lifecycle events:

```text
ATTACH_TO
DETACH_FROM
```

which carry the semantic ownership transition and required historical display metadata.

An intrinsic mutation must not reload and duplicate all direct children merely because the current Object GET representation includes them.

## Intrinsic payloads are operation-specific

The previous strong candidate used one generic intrinsic snapshot shape:

```text
id
canonical_name
template_id
template_version
properties
```

for every intrinsic event.

That universal rule is superseded.

Current direction is operation-by-operation:

```text
CREATED
    -> may legitimately carry broad created current state
       because the resource enters existence

RENAME
    -> exact old/new canonical_name only

DATA_CHANGE
    -> exact changed-property delta
       + exact ObjectTemplate binding context

SCHEMA_CHANGE
    -> exact binding transition
       + exact changed-property delta
       + no full intrinsic snapshots or slot/ownership duplication

DELETED
    -> may legitimately carry broad final current state
       because the resource leaves current existence
```

The CREATE/DELETE observations above express the current rationale, not a generic requirement that their final payloads must mirror the public Object DTO.

## DTO consequence

Today lifecycle intrinsic event DTOs/persistence decoding are shaped around a common Object before/after carrier.

M4 should not preserve that coupling merely for uniformity.

Candidate direction is a discriminated event-detail model whose payload depends on `kind`.

Conceptually:

```text
LifecycleEventDetail
    common historical metadata
    + kind-specific transition payload

RENAME payload
    before.canonical_name
    after.canonical_name

DATA_CHANGE payload
    exact binding context
    changed property deltas keyed by semantic property identity

SCHEMA_CHANGE payload
    exact source/target binding transition
    changed property deltas keyed by semantic property identity

ObjectSnapshotDto
    retained only for event kinds whose semantic contract genuinely requires
    a complete intrinsic Object snapshot
```

Therefore `ObjectSnapshotDto` is no longer the universal before/after type for every intrinsic lifecycle event.

The exact public discriminated-union shape remains part of the later Lifecycle API closure.

## Read data path

The current `GET /objects/{id}/lifecycle-events` projection remains conceptually close to the desired M4 collection path:

```text
one statement
    -> verify target Object existence
    -> page lifecycle event summaries involving the Object
    -> order by (occurred_at, id) DESC
```

Required public distinction remains:

```text
Object absent
    -> 404

Object exists + no matching events
    -> empty page

Object exists + matching events
    -> paged event summaries
```

No ObjectTemplate/DataType/effective-schema lookup is needed for the read.

Complete kind-specific historical payload belongs to the single-event detail surface rather than the collection summary path.

## Abstract architectural reading

Lifecycle is historical/audit state, not an implicit event-sourcing authority for rebuilding current Object state.

Therefore:

```text
current Object state
    -> current persistence/read surfaces

historical lifecycle event
    -> exact semantic transition owned by its mutation kind
```

This keeps audit data semantically complete without making every mutation/event scale with unrelated aggregate state.

## Current conclusion

- Lifecycle payloads are operation-specific, not universally full Object snapshots.
- RENAME stores/returns only the exact old/new canonical-name transition.
- DATA_CHANGE stores/returns the exact changed-property delta plus exact binding context.
- SCHEMA_CHANGE stores/returns the exact source/target binding transition plus the exact delta of runtime properties that actually changed.
- SCHEMA_CHANGE does not duplicate full Object snapshots, materialized slot rows or ownership membership.
- Components remain outside intrinsic event payloads; ATTACH/DETACH own ownership history.
- Collection reads should use bounded summaries; complete kind-specific payload belongs to event detail.
- No cache or new read-side denormalization is justified by these decisions.
