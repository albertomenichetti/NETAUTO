# DataType — Current AS-IS

## Purpose and authority

A `DataType` is a stable, named and versioned scalar domain. A `DataTypeVersion` describes the validity of one atomic value through one kernel `PrimitiveType` plus optional constraints.

This document owns DataType identity, version lifecycle, scalar constraints, defaults and value semantics. Persistence, public transport and concurrency realization belong to their respective current owners.

DataType does not model object structure, entity identity, relationships,
ownership or collection cardinality. A DataTypeVersion determines validity of
one atomic value. `SCALAR` / `LIST` cardinality belongs to the consuming property
declaration: ObjectTemplateVersion properties and RelationshipDefinitionVersion
properties are the current declaration families.

## Stable identity and naming

A DataType lineage has stable:

```text
id
namespace
name
```

and mutable non-semantic `description` plus nullable `default_version` policy state.

`id`, `namespace` and `name` are immutable after creation. `(namespace, name)` is unique among DataTypes.

Naming:

```text
name      = [a-z][a-z0-9_]*       # max 64
namespace = segment("." segment)*
segment   = [a-z][a-z0-9_]*       # max 64 per segment
namespace max length = 255
```

`core` and `core.*` are reserved for kernel-defined namespaces.

The derived model identifier is:

```text
datatype.<namespace>.<name>
```

It is derived and is not an additional persisted identity.

## PrimitiveType catalog

PrimitiveType is kernel-defined, immutable and not a user-managed database entity.

Current catalog:

```text
core.string
core.integer
core.number
core.boolean
core.date
core.datetime
core.ip
core.ip_prefix
core.byte_size
```

All versions in one DataType lineage use the same PrimitiveType. Cross-primitive evolution is not part of the current architecture.

## Version identity and allocation

A DataTypeVersion exact identity is:

```text
(datatype_id, version)
```

`version >= 1` and is unique among currently existing versions of the lineage.

New version allocation uses:

```text
max(existing_versions) + 1
```

Gaps are allowed. If the highest DRAFT is deleted, its version number may be reused; no irreversible version sequence is maintained.

`create-next`:

- selects an exact source in the same lineage;
- source must be PUBLISHED or DEPRECATED, never DRAFT;
- source need not be the current maximum version;
- creates `max(existing)+1` as DRAFT revision 1;
- clones the source semantic snapshot;
- does not persist a `derived_from` relationship.

Multiple DRAFT versions may coexist.

## Lifecycle and draft freshness

Lifecycle is strictly monotonic:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

DRAFT:

- constraints are mutable;
- supports revise, publish and delete;
- has optimistic generation token `revision`;
- `datatype_id`, `version` and PrimitiveType are immutable.

PUBLISHED:

- immutable semantic snapshot;
- eligible for new direct bindings;
- may be selected as lineage default;
- not individually deletable.

DEPRECATED:

- immutable historical snapshot;
- existing exact bindings remain valid;
- not eligible for new direct bindings;
- valid source for `create-next`;
- not individually deletable.

Every DRAFT starts with `revision=1`.

`revise`, `publish` and DRAFT delete require `expected_revision`. An operation based on a stale generation cannot silently reapply its intent to a newer generation.

`publish` does not increment revision because the snapshot leaves DRAFT and becomes immutable.

## Constraints and canonical values

Constraints are conjunctive. Unsupported constraints, malformed values, duplicate enum members after canonicalization, direct contradictions and enum members incompatible with the remaining constraints are rejected.

Current matrix:

| Primitive | Supported constraints |
|---|---|
| `core.string` | `min_length`, `max_length`, `pattern`, `enum` |
| `core.integer` | `minimum`, `maximum`, `enum` |
| `core.number` | `minimum`, `maximum`, `enum` |
| `core.boolean` | `enum` |
| `core.date` | `minimum`, `maximum`, `enum` |
| `core.datetime` | `minimum`, `maximum`, `enum` |
| `core.ip` | `ip_version`, `enum` |
| `core.ip_prefix` | `ip_version`, `enum` |
| `core.byte_size` | `minimum`, `maximum`, `enum` |

`ip_version` is `4` or `6`.

`core.string.pattern` uses Python standard `re`; validity is `re.compile()` and matching semantics are full-match semantics equivalent to `re.fullmatch()`.

`enum` is an unordered finite set of semantic values. Each member follows:

```text
raw input
-> primitive parse/validation
-> primitive canonicalization
-> duplicate detection
-> validation against remaining constraints
-> canonical member
```

`required`, `nullable`, `default`, `unique`, `immutable` and collection cardinality are not DataType constraints.

## Primitive canonicalization

Canonicalization is performed only when it is intrinsic and unambiguous for the primitive.

- `core.string`: identity; no automatic trim/lowercase.
- `core.integer`: exact integer; boolean is not an integer value.
- `core.number`: finite exact decimal; no NaN/Infinity; numerically equivalent forms converge.
- `core.boolean`: canonical boolean.
- `core.date`: valid calendar date, canonical ISO form.
- `core.datetime`: absolute instant requiring offset/Z input; canonical UTC `Z`; no arbitrary rounding.
- `core.ip`: canonical IPv4/IPv6 address.
- `core.ip_prefix`: valid canonical network; non-zero host bits are rejected rather than repaired.
- `core.byte_size`: exact non-negative byte quantity; SI and IEC units are distinct; fractional input is valid only when it converts to an exact integer byte count.

The canonical persistence representation is defined in `persistence.md` and the
accepted public lexical representation in `api.md`. Object and Relationship
property values, DataType constraint/enum members and ObjectTemplate property
`migration_default` values reuse the same primitive parsing/canonicalization
semantics.

JSON Schema is not a validation language, compile target or public schema representation of DataType.

## Default version and exact pinning

`default_version` is either NULL or an exact PUBLISHED version of the same lineage.

New version-sensitive bindings follow one of two modes:

```text
explicit binding
    -> caller selects exact version
    -> version must remain PUBLISHED through commit

implicit binding
    -> resolve current default_version
    -> selected version must remain PUBLISHED through commit
    -> persist the resulting exact pin
```

Floating `default`, `latest` or highest-version references are never persisted.

First publication with no current default automatically establishes that PUBLISHED version as default. Later publish operations do not change the default automatically.

`set_default` accepts only an exact PUBLISHED version in the same lineage. `clear_default` sets the pointer to NULL and disables implicit binding until a default is established again.

A current default cannot be deprecated.

## Active model graph and deprecation

A PUBLISHED DataTypeVersion cannot be deprecated while a direct PUBLISHED model
consumer depends on it through a lifecycle-sensitive exact binding.

The direct active PUBLISHED consumers are:

```text
PUBLISHED ObjectTemplateVersion property exact pin
PUBLISHED RelationshipDefinitionVersion property exact pin
```

Either family blocks deprecation of the exact DataTypeVersion on which it
depends.

DRAFT consumers and DEPRECATED consumers do not block deprecation. Direct active-consumer checks are sufficient because every PUBLISHED consumer must itself satisfy the active-model invariant.

Publication of a consumer and deprecation of the dependency are strongly consistent: they cannot both commit if the result would be:

```text
PUBLISHED consumer -> DEPRECATED dependency
```

Runtime Object creation consumes an already-certified PUBLISHED ObjectTemplateVersion and does not recursively re-certify the entire DataType dependency closure.

## Delete semantics

Individual version delete is allowed only for DRAFT and requires `expected_revision`.

Whole-lineage delete is atomic and is allowed only when no external current reference targets any version of the lineage. The internal default pointer does not itself block whole-lineage deletion.

Cross-aggregate persistence references are protected with non-cascading lifetime semantics so concurrent reference creation and deletion cannot leave dangling state.

## Read consistency

Ordinary GET/list operations are non-locking and snapshot-consistent for the single request/operation. No repeatability is promised across separate requests.

Composite reads must not expose lineage/default/version combinations that never coexisted in one coherent database snapshot.

Mutation/admission reads stabilize lifecycle/default predicates through the transaction contract defined in `concurrency.md`.

## Key invariants

- one DataTypeVersion represents one atomic domain;
- each version uses exactly one supported PrimitiveType;
- DataType stable identity and qualified name are immutable;
- PrimitiveType is stable across the lineage;
- exact version numbers are positive and unique among current rows;
- lifecycle is monotonic and PUBLISHED/DEPRECATED snapshots are immutable;
- DRAFT semantic changes respect `expected_revision` freshness;
- constraints and enum values are canonical and mutually coherent;
- default is NULL or exact PUBLISHED same-lineage;
- new direct bindings target PUBLISHED exact versions through commit;
- no version-sensitive persisted binding floats on a default/latest selector;
- active PUBLISHED consumers never point to non-PUBLISHED exact dependencies;
- supported concurrent interleavings preserve all invariants above.
