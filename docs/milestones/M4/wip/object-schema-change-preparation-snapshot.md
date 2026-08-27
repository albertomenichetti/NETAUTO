# M4 WIP — Object SCHEMA_CHANGE preparation snapshot

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the distinction between model-plane effective component slots and the current runtime ownership facts read when preparing:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Context

After the exact source-to-target `MigrationPlan` has been made READY, the command re-reads the current Object aggregate to prepare the concrete migration candidate and compute the optimistic Object fingerprint.

This second Object read is different from the initial lightweight binding discovery used to obtain:

```text
object_id
template_id
source_version
```

## What the preparation snapshot reads

The preparation snapshot contains the current intrinsic Object state:

```text
id
canonical_name
template_id
template_version
properties
```

plus the current **attached ownership edges** for which the Object is the parent:

```text
child_object_id
slot_declaring_template_id
slot_name
```

These rows come from `object_components` and represent only ownership facts that actually exist now.

Example:

```text
Effective schema slots:
    interfaces
    disks

Current runtime attachments:
    eth0 -> interfaces
    eth1 -> interfaces
```

The preparation snapshot contains the two actual `interfaces` edges. It does not synthesize or read an empty `disks` slot from runtime ownership state.

## What the preparation snapshot does not read

The preparation Object read does **not** read the ObjectTemplate effective component-slot schema.

Effective component slots are immutable model-plane knowledge already contained in the READY source/target semantic inputs and the compiled `MigrationPlan`.

Therefore the two concepts remain separate:

```text
MigrationPlan / exact effective closures
    -> which component slots exist semantically
    -> source/target slot identities and target-template compatibility

object_components
    -> which child Objects are actually attached now
    -> current runtime ownership facts
```

## Why current attached edges are part of the snapshot

They are needed for two distinct purposes.

### Migration admission

A schema migration may remove or semantically replace a component slot. The planner can know that the slot disappears, but only current `object_components` rows can tell whether the Object currently has children attached through that semantic slot.

For example:

```text
source slot: interfaces
target schema: interfaces removed
```

If no current edge uses the slot, the ownership admission can succeed.

If one or more current edges use the slot, normal M4 schema migration fails rather than implicitly detaching children.

### Optimistic concurrency fingerprint

Current attached edges are part of the authoritative Object aggregate fingerprint.

This ensures that a concurrent:

```text
ATTACH
DETACH
```

between optimistic preparation and protected commit changes the fingerprint and prevents a prepared success from being committed against stale ownership state.

## Terminology

To avoid ambiguity, discovery should prefer:

```text
current attached ownership edges
current ownership edges
```

rather than relying on the shorter phrase `outgoing ownership` when discussing the preparation snapshot.

`effective component slots` always refers to model-plane ObjectTemplate schema knowledge, not runtime attachment rows.

## Frozen preparation boundary

Once `MigrationPlanCache[(template_id, source_version, target_version)]` is READY, the next caller-side step is conceptually:

```text
read one coherent current Object aggregate snapshot S
    intrinsic Object
    + current attached ownership edges

compute:
    expected_object_fingerprint = SHA-256(canonical_json(S))
```

The exact SQL shape of this coherent Object + ownership read remains a physical realization detail to be closed next.
