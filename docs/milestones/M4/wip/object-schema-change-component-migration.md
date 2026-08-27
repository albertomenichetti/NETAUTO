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

## Semantic-identity replacement

If SOURCE and TARGET expose the same effective slot name under different `SlotSemanticKey` values, name equality does not create continuity.

Example:

```text
SOURCE
    (Device, interfaces) -> NetworkInterface

TARGET
    (Server, interfaces) -> NetworkInterface
```

is classified as:

```text
REMOVE (Device, interfaces)
ADD    (Server, interfaces)
```

not as migration of one continuous slot.

This remains true even when the old and new slots have exactly the same target lineage and every current child would be compatible with the new slot. Compatibility does not transfer ownership semantic identity.

Persisted ownership facts carry the declaring-lineage identity explicitly:

```text
object_components
    child_object_id
    parent_object_id
    slot_declaring_template_id
    slot_name
```

Therefore an edge through:

```text
(Device, interfaces)
```

must never be silently reinterpreted as an edge through:

```text
(Server, interfaces)
```

Frozen runtime rule:

```text
old SlotSemanticKey has zero current outgoing edges
    -> replacement is admissible for this Object
    -> old slot disappears
    -> new slot starts semantically empty
    -> object_components unchanged

old SlotSemanticKey has one or more current outgoing edges
    -> SCHEMA_CHANGE fails
    -> no implicit rebinding
    -> no implicit detach + reattach
```

Example:

```text
SOURCE
    (Device, interfaces) -> NetworkInterface

runtime
    server-1 owns eth0 through (Device, interfaces)

TARGET
    (Server, interfaces) -> NetworkInterface
```

Even though `eth0` would also satisfy the new slot target, migration fails until the caller explicitly removes the old ownership fact. If desired, a later explicit ATTACH after schema migration may create a new ownership fact through `(Server, interfaces)`.

The governing invariant is:

```text
child compatibility with a new slot
    !=
continuity of the old ownership fact
```

and more generally:

```text
name equality never transfers runtime state across semantic identities
```

As with REMOVE SLOT, a blocker observed in the preparatory snapshot may produce an immediate conservative failure. A prepared success based on observing no edge through the removed semantic key must still pass the protected aggregate-fingerprint check before commit.

## Position-only change

`position` belongs to one exact component declaration as explicit ordering/presentation state. It is not part of `SlotSemanticKey` and it is not persisted on an ownership edge.

A new DRAFT ObjectTemplateVersion may therefore preserve the same local semantic slots while revising only their positions before publication.

Example:

```text
SOURCE Server v4
    disks       position = 1
    interfaces  position = 2

TARGET Server v5
    interfaces  position = 1
    disks       position = 2
```

The semantic identities remain unchanged:

```text
(Server, disks)
(Server, interfaces)
```

and Object migration therefore treats this as metadata evolution, not REMOVE+ADD.

Frozen runtime consequence:

```text
POSITION-ONLY CHANGE
    -> preserve every current ownership edge unchanged
    -> no compatibility revalidation
    -> no detach/reattach
    -> no object_components mutation
```

The target exact schema becomes the new ordering authority after migration. Any read projection that orders component slots from the exact schema may therefore expose the new order, but the ownership facts themselves remain identical.

`ObjectTemplate.REVISE` is a complete replacement of the local declaration candidate, so a persistence implementation may physically delete/reinsert declaration rows. That DML shape has no semantic meaning for runtime migration. SOURCE/TARGET comparison is based on semantic identity and declaration state, not on how the model-plane rows happened to be rewritten.

This position-only rule applies to a slot continuous under the same declaring lineage. A child lineage cannot locally override/redeclare an inherited effective slot merely to change its inherited position, because normal ObjectTemplate inheritance does not permit hiding/override of inherited members.

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

SEMANTIC-IDENTITY REPLACEMENT
    same effective name + different SlotSemanticKey
        -> REMOVE old semantic slot + ADD new semantic slot

    old semantic slot has zero edges
        -> admissible
        -> new semantic slot starts empty

    old semantic slot has >= 1 edge
        -> fail
        -> no implicit rebinding/detach+reattach

POSITION-ONLY CHANGE
    same SlotSemanticKey
        -> schema ordering/presentation metadata only
        -> preserve ownership facts unchanged
        -> no runtime compatibility revalidation or ownership DML
```

Still to define incrementally:

```text
inheritance-driven component deltas
complete ownership portion of PreparedSchemaChange / UoW realization
```
