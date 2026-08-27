# M4 WIP — Object SCHEMA_CHANGE component-slot migration semantics

Status: PARTIAL FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the runtime ownership/component semantics frozen incrementally for `Object.SCHEMA_CHANGE` after the component-slot delta taxonomy was established.

Component-slot continuity uses:

```text
SlotSemanticKey = (declaring_template_id, slot_name)
```

Name equality alone does not establish continuity.

The normal ObjectTemplate evolution contract already permits only monotonic target widening toward an ancestor lineage for one continuous slot. Target narrowing or migration to an unrelated lineage is not a normal admitted delta.

The execution model follows the Object optimistic-preparation protocol:

```text
outside mutation UoW
    read coherent Object aggregate snapshot S
    including complete outgoing ownership facts
    compute aggregate fingerprint F(S)
    apply immutable MigrationPlan(source,target)

prepared failure derived from S
    -> may fail immediately
    -> no lock/fingerprint recheck required
    -> conservative stale failure is acceptable

prepared success
    -> enter short UoW
    -> protect Object concurrency owner
    -> recompute authoritative current fingerprint F(S')

    F(S') != F(S)
        -> prepared success is stale
        -> rollback + bounded restart

    F(S') == F(S)
        -> prepared success may proceed to final mutable admissions and commit
```

The protocol is intentionally asymmetric:

```text
false success
    -> must be prevented STRONGLY

false failure
    -> acceptable conservative outcome
    -> cannot make persisted data model incoherent
```

## ADD component slot

A slot whose semantic key is absent from SOURCE and present in TARGET needs no ownership migration.

```text
ADD_SLOT
    -> existing object_components rows unchanged
    -> new slot is semantically empty for the migrating Object
    -> no row is materialized merely to represent an empty 0..N slot
```

A valid SOURCE Object cannot already contain a current ownership edge through a slot that does not exist in its current exact effective schema.

Example:

```text
SOURCE Server v4
    disks -> Disk

TARGET Server v5
    disks      -> Disk
    interfaces -> NetworkInterface
```

After migration, existing disk edges are preserved and `interfaces` is simply empty until future explicit ATTACH operations create edges.

## REMOVE component slot

A source slot may be absent from TARGET, but Object schema migration never performs implicit detach/remediation.

For one removed `SlotSemanticKey`:

```text
no current outgoing edge through the slot
    -> removal is admissible for this Object
    -> object_components unchanged

one or more current outgoing edges through the slot
    -> SCHEMA_CHANGE fails
    -> no child is detached implicitly
```

Example:

```text
SOURCE Server v4
    interfaces -> NetworkInterface

TARGET Server v5
    interfaces removed
```

If `server-1` currently owns `eth0` through `interfaces`, the caller must explicitly DETACH that edge before retrying the schema change.

A negative decision may be returned directly from the preparatory snapshot even if a concurrent DETACH later removes the blocker before the caller receives the response.

```text
T1 SCHEMA_CHANGE snapshot sees eth0 attached
T2 DETACH eth0 commits
T1 may still return migration failure
```

This conservative false failure is accepted. The next caller retry observes fresh state.

Conversely, a preparatory success based on observing no blocking edges cannot commit unless the protected aggregate fingerprint still matches, preventing a concurrent ATTACH from creating a false success.

## Continuous slot target widening

Normal model evolution may widen a continuous slot target toward an ancestor lineage.

Example:

```text
SOURCE
    interfaces -> EthernetInterface

TARGET
    interfaces -> NetworkInterface
```

where `EthernetInterface` is the same lineage as, or a descendant of, `NetworkInterface`.

Compatibility is monotonic by construction:

```text
SOURCE-admissible child lineages
    subset of
TARGET-admissible child lineages
```

Therefore every current child that was valid under the SOURCE slot remains valid under the TARGET slot.

Frozen runtime consequence:

```text
TARGET WIDENING
    -> existing ownership edges are preserved unchanged
    -> no per-child compatibility query or revalidation is required
    -> no object_components mutation is required
```

The widening guarantee comes from model-plane certification of the immutable SOURCE/TARGET exact schemas and stable lineage ancestry, not from rechecking each runtime child during Object migration.

The target remains a stable ObjectTemplate lineage; no child exact version participates in this compatibility rule.

## Frozen in this increment

```text
ADD SLOT
    -> no ownership rows created
    -> new slot starts empty

REMOVE SLOT
    zero current edges
        -> admissible
        -> ownership state unchanged

    >= 1 current edge
        -> fail
        -> never implicit detach

prepared negative result based on mutable Object state
    -> may fail immediately outside UoW
    -> stale/conservative false failure accepted

prepared positive result
    -> protected aggregate fingerprint must still match before commit
    -> false success prevented STRONGLY

TARGET WIDENING toward ancestor
    -> all SOURCE-compatible current children remain TARGET-compatible by construction
    -> preserve all edges unchanged
    -> no per-child runtime compatibility revalidation
```

Still to define incrementally:

```text
semantic-identity replacement through remove/add under different declaring lineage
position-only changes
inheritance-driven component deltas
complete ownership portion of PreparedSchemaChange / UoW realization
```
