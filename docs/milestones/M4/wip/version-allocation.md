# M4 WIP — Cross-domain exact-version allocation

**Status:** REVIEWED BASELINE / CROSS-DOMAIN DISCOVERY OWNER / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file owns the current M4 cross-domain working direction for allocating numeric exact-version identifiers.

It separates:

```text
the domain meaning guaranteed by version numbers
from
the persistence mechanism used to allocate them safely
```

Everything under `wip/` remains globally non-normative and does not authorize implementation.

---

# 1. Domain guarantee

For every versioned domain lineage, `version` identifies one exact version.

M4 guarantees one and only one generic ordering property:

```text
if exact version VX is created after exact version VY
for the same versioned lineage,
then X > Y
```

Equivalently, version numbers are monotonically increasing in **creation/allocation order inside one lineage**.

This rule exists because it would be counterintuitive for a user to create a new exact version and receive a number lower than an exact version that had already been created for the same lineage.

The rule does **not** imply any other ordering semantics.

From:

```text
X > Y
```

it remains invalid to infer:

```text
VX was derived from VY
VX is the semantic successor of VY
VX is wider or more permissive than VY
VX is compatible with VY
VY -> VX is migratable
VX was published after VY
VX is the current/default/preferred version
```

Canonical distinction:

```text
version order
    -> creation/allocation order only

version order
    != genealogy
    != semantic evolution order
    != compatibility order
    != migrability order
    != publication order
```

A later-created exact version may therefore be based on, cloned from, or otherwise derived according to an operation-specific contract from an older exact version without making the version number encode that derivation relationship.

---

# 2. No version-number reuse

The temporal monotonicity guarantee implies that an allocated version number is never reused inside the same lineage.

Example:

```text
create v1
create v2
create v3
DELETE_DRAFT v3
create another exact version
    -> v4
    -> never v3 again
```

Deleting an exact version does not move the allocation sequence backward.

This is an allocation invariant, not a claim that the deleted exact version remains part of current domain state.

---

# 3. Shared `last_versions` persistence candidate

Current M4 direction uses one cross-domain allocator table:

```text
last_versions
    id
    last_version
```

where:

```text
id
    = UUID of one versioned domain lineage/resource

last_version
    = highest version number ever allocated for that id
```

The table is intentionally shared by all versioned domain families; separate allocator tables per family are not required.

Current versioned lineage consumers are:

```text
DataType
ObjectTemplate
RelationshipDefinition
```

The allocator does not need to persist the semantic type of the owning resource. It owns only the mapping:

```text
versioned lineage UUID -> last allocated numeric version
```

## 3.1 Cross-family UUID namespace invariant

The single-column allocator key relies on the project-wide UUID allocation convention:

```text
kernel-generated entity UUIDs
    -> Python uuid4
    -> one undifferentiated practical UUID namespace across families
```

For the versioned lineage families relevant to this allocator:

```text
DataType.id
ObjectTemplate.id
RelationshipDefinition.id
```

are treated by NETAUTO as globally unique across those families. The same UUID value is not a supported identity for two different lineages, even when the lineages belong to different model families.

Consequently:

```text
last_versions.id
```

is sufficient to identify one version-allocation sequence and no `resource_kind` discriminator is required merely to avoid cross-family ambiguity.

This does **not** mean that public API resource type can be inferred from an arbitrary UUID without route/type context. It is an internal identity-allocation invariant: cross-family UUID collision or intentional UUID reuse is unsupported internal state rather than a legitimate pair of resources.

If the project ever changes away from this shared UUID allocation invariant, the `last_versions` key shape must be revalidated.

# 4. Allocation rule

Creation of a new exact version must obtain its number from `last_versions`, not from the currently existing version rows.

Logical operation:

```text
allocate_next_version(id):
    atomically advance last_versions.last_version
    return the new value
```

Conceptually:

```text
new_version = previous_last_version + 1
```

The advance and returned value must be concurrency-safe so two concurrent exact-version creations for the same `id` cannot receive the same number or observe the sequence moving backward.

The exact PostgreSQL statement/lock realization remains architecture work.

# 5. Initialization and lifetime

When the first exact version of a newly created versioned lineage/resource is allocated, `last_versions` must establish the initial sequence state consistently with that first assigned version.

Afterward:

```text
exact-version deletion
    -> does not decrement last_version

new exact-version allocation
    -> increments from last_version
```

The exact lifetime coupling between a lineage/resource row and its `last_versions` row, including deletion of the complete lineage/resource, remains a relational architecture detail.

# 6. Cross-operation consequence

Any existing discovery or AS-IS path that allocates a new exact version using a rule equivalent to:

```text
max(currently persisted version numbers) + 1
```

must be revalidated against this owner.

In particular, deletion of a high-number DRAFT must not make that number allocatable again.

This is a cross-domain concern and should not be independently redefined by each versioned-family operation.

# 7. Boundary with migration semantics

This allocation rule changes only what numeric order guarantees to callers.

It does not change the previously ratified separation:

```text
validity of exact version
    !=
cross-version migrability
```

and does not add migration speculation to operations such as `REVISE` or `PUBLISH`.

A migration operation must continue to evaluate whatever SOURCE/TARGET compatibility its own contract requires; it must not infer semantic compatibility merely from:

```text
target_version > source_version
```

# 8. Architecture handoff

Later architecture must decide the concrete relational realization while preserving the logical invariant above, including:

```text
primary/unique key of last_versions
atomic increment/upsert shape
initial allocation shape
concurrency behavior for same-id allocation
lifetime behavior on complete lineage/resource deletion
FK or no-FK realization across heterogeneous owning tables
migration/backfill from existing versioned data
```

The current discovery decision is only that one shared logical allocator is sufficient, that the relevant lineage UUIDs share one cross-family UUID namespace, and that version numbers never move backward or get reused within one lineage.
