# M4 WIP — Object SCHEMA_CHANGE component admission from prepared snapshot

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the component-side preparation rule for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Inputs

At this stage the command already has:

```text
S
    complete Object intrinsic snapshot
    current attached ownership edges

MigrationPlan[(template_id, source_version, target_version)]
    immutable property rules
    immutable component rules
```

The current attached ownership edges in `S` are factual rows from `object_components` where the Object is the parent:

```text
child_object_id
slot_declaring_template_id
slot_name
```

They are not the effective component-slot schema. Effective component slots were already resolved from immutable model-plane closure and compiled into the `MigrationPlan`.

## Component-side preparation

The command evaluates:

```text
S.current_ownership_edges
+
MigrationPlan.component_rules
```

entirely outside the mutation UoW.

The preparation must not:

```text
reload child Objects
reload ObjectTemplate effective schema
reconstruct inheritance
re-resolve slot semantic identity from slot_name
query stable ancestry again
```

All semantic interpretation needed to classify source-to-target slot evolution was already performed when compiling the immutable `MigrationPlan`.

The runtime edge already carries the semantic slot identity:

```text
SlotSemanticKey = (slot_declaring_template_id, slot_name)
```

so the current ownership facts can be matched directly against the component rules.

## Admission outcomes

Examples:

```text
ADD slot
    -> no current edge can exist for the new semantic key
    -> no runtime ownership work

REMOVE slot
    -> zero current edges on removed semantic key => allowed
    -> one or more current edges => migration blocked

semantic replacement
    -> treated as REMOVE old semantic key + ADD new semantic key
    -> any edge on old semantic key => migration blocked

compatible preserved/widened slot
    -> current edges remain admitted
    -> no ownership DML

position-only change
    -> no ownership impact
```

The normal successful M4 Object SCHEMA_CHANGE therefore does not mutate `object_components`.

Ownership is an admission condition for the schema migration, not target state produced by the migration.

## Failure behavior

If the current snapshot `S` already contains an ownership blocker, preparation fails immediately before entering the UoW.

A concurrent DETACH that removes the blocker after `S` was read may therefore cause a conservative false failure. This is accepted under the already-frozen M4 asymmetry:

```text
false success -> prevent strongly
false failure -> acceptable conservative outcome
```

If preparation succeeds, the whole-aggregate fingerprint later protects against concurrent ATTACH/DETACH changing the ownership generation before commit.

## Cost

For component-side preparation after `S` and `MigrationPlan` are available:

```text
0 PostgreSQL statements
0 cache fills
0 model-plane reads
0 locks
0 object_components DML on success
```

Only application-side matching/checking of current ownership edges against compiled component rules is required.

## Frozen decision

```text
component admission source:
    current attached ownership edges already present in S

semantic source:
    immutable component rules already present in MigrationPlan

no child Object reads
no schema rereads
no ancestry rereads
no runtime slot reinterpretation
successful schema migration preserves ownership rows unchanged
```
