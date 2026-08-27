# M4 — Object.ATTACH discovery

**Status:** WIP / NON-NORMATIVE

## Scope

First-phase discovery for factual Object ownership ATTACH. Lock/concurrency redesign remains deferred to the global concurrency phase.

## Current structural issue

Current `object_components` persists only:

```text
child_object_id
parent_object_id
slot_name
```

while slot semantic identity is:

```text
(slot_declaring_template_id, slot_name)
```

The runtime edge therefore loses part of the semantic identity resolved at admission time.

## Candidate current ownership fact

```text
object_components
    child_object_id              PK
    parent_object_id
    slot_declaring_template_id
    slot_name
```

Do **not** persist `slot_declaring_template_version`: the current edge is interpreted against the parent Object's current exact effective schema, and the semantic slot identity must survive Object schema evolution without rewriting the edge.

Candidate FK:

```text
slot_declaring_template_id -> object_templates.id ON DELETE RESTRICT
```

Do not FK the edge to a specific exact component declaration/version. Current slot-contract validity is an admission rule against the parent's current exact effective schema.

## ATTACH data path candidate

```text
load current parent Object
    -> template_id/template_version/canonical_name

load_compiled_object_template(parent.template_id, parent.template_version)
    -> resolve requested slot_name
    -> declaring_template_id/name/target_template_id

load current child Object
    -> template_id/canonical_name

validate parent != child
validate child stable lineage compatible with slot.target_template_id
inspect current child ownership
check current ownership graph cycle

INSERT object_components(
    child_object_id,
    parent_object_id,
    slot_declaring_template_id,
    slot_name
)

INSERT ATTACH lifecycle event with the same semantic slot identity
```

At cache warm state, effective-slot resolution comes from the immutable compiled ObjectTemplate cache, and child lineage compatibility may use stable ObjectTemplate ancestry knowledge. PostgreSQL remains authoritative for current parent/child existence, current owner and current ownership graph cycle state.

## Idempotence

Same-edge convergence should compare the complete semantic edge identity:

```text
current.parent_object_id == requested parent
AND current.slot_declaring_template_id == resolved declaring template
AND current.slot_name == resolved slot name
```

Name equality alone is not semantic slot equality.

## Persistence responsibilities

PostgreSQL remains the direct authority for:

- one-owner uniqueness via `child_object_id` PK;
- parent/child existence via FKs;
- no self edge via CHECK;
- current edge persistence;
- final race arbitration.

The mutation plane resolves and validates the model semantics once, then persists the resolved semantic edge.

## Explicit non-decisions

- lock/gate redesign;
- exact cycle-check concurrency realization;
- exact indexes and migration DDL;
- final lifecycle metadata concurrency shape.
