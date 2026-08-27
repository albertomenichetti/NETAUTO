# M4 WIP — Object SCHEMA_CHANGE immutable MigrationPlan premise

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the agreed architectural premise that the semantic migration plan between two exact ObjectTemplateVersions is immutable and reusable across Objects.

## Immutability premise

For `Object.SCHEMA_CHANGE`:

```text
source = (template_id, source_version)
target = (template_id, target_version)
target_version > source_version
```

The source exact ObjectTemplateVersion is already bound by an existing Object. It may be `PUBLISHED` or `DEPRECATED`; both states are immutable semantic snapshots.

The target exact ObjectTemplateVersion must be `PUBLISHED` to receive a new Object binding, and a PUBLISHED snapshot is immutable.

Therefore:

```text
EffectiveSchema(source) = immutable
EffectiveSchema(target) = immutable
```

and consequently:

```text
MigrationPlan(source,target)
    = f(EffectiveSchema(source), EffectiveSchema(target))
    = immutable
```

The plan does not depend on one concrete Object instance.

## Reusable plan identity

The natural reusable key is:

```text
(template_id, source_version, target_version)
```

Conceptually:

```text
ObjectTemplateMigrationPlanCache[
    (template_id, source_version, target_version)
]
```

Once built from complete immutable source/target semantics, the plan never becomes semantically stale because neither exact schema can change.

No distributed invalidation or cache-coherency protocol is required for correctness.

## Target lifecycle state remains PostgreSQL authority

Immutability of the target schema does not mean a cached plan can admit a new binding.

Example:

```text
build plan Server v4 -> v7 while v7 is PUBLISHED
later v7 becomes DEPRECATED
```

The cached plan remains semantically correct:

```text
what migration v4 -> v7 means
    -> unchanged
```

but a new Object schema binding to v7 is no longer admissible:

```text
may Object bind to v7 now?
    -> PostgreSQL current lifecycle authority
```

Therefore the authority split is:

```text
immutable cache
    source exact semantics
    target exact semantics
    source -> target MigrationPlan

PostgreSQL
    target still PUBLISHED for new binding admission
```

Cache presence never proves current target admission.

## Plan contents

The plan may precompute all Object-independent semantic work derived from the frozen source/target effective schemas, including for example:

```text
properties
    semantic continuity by (declaring_template_id, name)
    additions/removals
    requiredness transition
    SCALAR -> LIST widening
    exact target DTV validator/spec
    migration_default use rule
    source-only drop

component slots
    semantic continuity by (declaring_template_id, slot_name)
    additions/removals
    target-lineage widening
```

Where useful, the plan may directly reference or embed compiled immutable validation structures derived from exact DataTypeVersion semantics.

The exact cache representation and fill contract will be normed when the ObjectTemplate exact-version loader/cache architecture is finalized.

## Runtime state deliberately excluded from the plan

The plan cannot contain facts that depend on one concrete current Object.

Examples:

```text
current properties
current outgoing ownership edges
current Object exact binding
current target PUBLISHED lifecycle state
```

For example:

```text
target removes semantic slot interfaces
```

is immutable plan knowledge.

But:

```text
server-1 currently has eth0 attached through interfaces
```

is mutable runtime state and must be checked from fresh protected PostgreSQL state during the mutation UoW.

## Intended SCHEMA_CHANGE split

The resulting design boundary is:

```text
IMMUTABLE / reusable outside Object lock
    SourceSchema READY
    TargetSchema READY
    MigrationPlan(source,target) READY

MUTABLE / concrete Object mutation
    fresh current Object properties
    fresh outgoing ownership edges
    current source binding still matches preparation
    target still PUBLISHED through new-binding commit
```

No cache fill or migration-plan construction belongs inside the Object row-lock critical section.

## Consequence for cold and warm execution

Cold path:

```text
resolve source/target identities
ensure immutable source/target schema facets READY
build/cache MigrationPlan once
then enter Object-specific mutation path
```

Warm path:

```text
resolve source/target identities
MigrationPlan cache hit
then enter Object-specific mutation path
```

All Objects migrating between the same exact versions reuse the same semantic plan.

## Frozen discovery rule

`Object.SCHEMA_CHANGE` must treat the source/target effective-schema comparison as immutable reusable model knowledge, not as per-Object work.

The next design step is to define, delta class by delta class, how that immutable plan transforms or admits fresh Object runtime state.