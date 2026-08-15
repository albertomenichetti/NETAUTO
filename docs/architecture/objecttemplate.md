# ObjectTemplate — Current AS-IS

## Responsibility

An `ObjectTemplate` lineage is the stable identity of an entity type. An `ObjectTemplateVersion` is an exact, versioned schema snapshot for that type.

ObjectTemplate defines:

- inheritance between template lineages;
- exact parent-version pinning;
- typed properties;
- ownership/component slots;
- effective schema derivation;
- lifecycle/default policy;
- model-plane dependency certification.

ObjectTemplate properties describe values. ObjectTemplate components describe ownership/composition of child Objects that retain their own identity. Relationships are a separate association model and are not ownership slots.

## Stable lineage identity

A lineage has stable:

```text
id
namespace
name
abstract
parent_template_id
```

plus mutable non-semantic `description` and nullable `default_version`.

`(namespace, name)` is unique among ObjectTemplates. Naming uses the same lowercase segmented grammar as DataType.

The parent **lineage** is stable for the lifetime of the ObjectTemplate. Current normal operations do not reparent a lineage.

Inheritance is acyclic.

## Exact version identity and parent pinning

An exact ObjectTemplateVersion identity is:

```text
(template_id, version)
```

A non-root exact version materializes an exact parent dependency:

```text
(parent_template_id, parent_version)
```

The stable parent lineage belongs to the ObjectTemplate header; the exact parent version belongs to the version snapshot.

Every version-sensitive dependency is exact. No persisted floating parent/default/latest reference is allowed.

Version allocation follows the same `max(existing)+1` policy as DataType, with gaps allowed and reuse of a deleted highest DRAFT version number possible.

`create-next` creates a new DRAFT revision 1 by cloning an eligible exact PUBLISHED/DEPRECATED source snapshot. Multiple DRAFT versions may coexist.

## Lifecycle and freshness

Lifecycle is:

```text
DRAFT -> PUBLISHED -> DEPRECATED
```

DRAFT:

- is mutable through explicit revise operations;
- must always remain structurally/semantically well-formed;
- need not yet satisfy every publication precondition;
- uses `expected_revision` freshness for revise, publish and delete.

PUBLISHED and DEPRECATED:

- are immutable snapshots;
- PUBLISHED may be selected for new bindings and may be default;
- DEPRECATED remains valid for historical exact bindings but cannot receive new direct lifecycle-sensitive bindings.

The lineage default is NULL or an exact PUBLISHED version of the same lineage. First publish may auto-establish a missing default; later publications do not replace it automatically.

## Properties

A property declaration belongs to one exact ObjectTemplateVersion and has semantic identity derived from:

```text
PropertySemanticKey = (declaring_template_id, name)
```

A local declaration contains, at minimum:

```text
name
position
datatype_id
datatype_version
value_mode
required
migration_default
```

Each property materializes an exact DataTypeVersion pin.

Current value modes:

```text
SCALAR
LIST
```

Property presence/cardinality is part of the property contract rather than the DataType contract.

`required=false` implies no `migration_default`. A required property that is introduced into a schema migration path requires a valid `migration_default` when absence must be filled.

`migration_default`:

- uses the same PrimitiveType parsing/canonicalization as runtime values;
- fills absence during controlled Object schema migration;
- never silently overwrites an existing incompatible source value.

Property and component names share one effective member namespace; shadow/override ambiguity is not allowed.

After first publication, property semantic identity is stable. Normal evolution does not rename a historical property identity or move it across DataType lineages.

Current normal value-mode evolution is monotonic `SCALAR -> LIST`; narrowing back to SCALAR requires a future explicit controlled migration capability.

`position` is explicit declaration state and is the ordering authority. Request-array order is not a second ordering authority.

## Components / ownership slots

A component declaration is a named `0..N` ownership slot.

A local slot contains:

```text
name
position
target_template_id
```

The target is a stable ObjectTemplate lineage, not an exact version.

A child Object is compatible when its stable template lineage is the target lineage or a descendant lineage.

Normal slot evolution may widen a target toward an ancestor; narrowing or unrelated target migration requires an explicit future workflow because it can invalidate current ownership state.

Slot semantic identity is:

```text
SlotSemanticKey = (declaring_template_id, name)
```

Ownership runtime edges are interpreted against the parent Object's **current exact effective schema**, not against a version-pinned slot row.

## Effective schema

The effective schema is derived from:

```text
exact parent chain
+
local property declarations
+
local component declarations
```

It is a derived semantic projection, not a separately authoritative materialized schema.

No authoritative effective-schema cache, generic compiled schema representation or JSON Schema artifact exists in the current architecture.

A DRAFT must remain well-formed. Publication performs the stronger certification required to make the exact schema an active model-plane dependency source.

The effective schema must preserve:

- acyclic exact inheritance;
- unique effective property/slot names;
- exact DataType property pins;
- valid property defaults/cardinality;
- valid component targets;
- stable semantic identity of inherited/local members;
- lifecycle-admissible direct exact dependencies.

## Active model graph

A PUBLISHED ObjectTemplateVersion belongs to the active model graph.

Every direct lifecycle-sensitive dependency of a PUBLISHED version must remain PUBLISHED, including:

- exact parent ObjectTemplateVersion;
- exact DataTypeVersion pins of properties.

A dependency cannot be deprecated while a direct active PUBLISHED consumer remains.

Publication of a consumer and deprecation of a dependency are strongly consistent and cannot both commit if the resulting graph would contain an active edge to a non-PUBLISHED exact dependency.

The invariant is enforced on direct dependencies; recursive validity follows because every active PUBLISHED consumer satisfies the same rule.

## Create/revise/publication model

ObjectTemplate CREATE establishes a stable lineage and an initial DRAFT v1.

REVISE is a complete replacement of the **local** candidate declarations for the exact DRAFT. It does not represent a generic partial PATCH of the effective schema.

The current public command contract requires explicit local property/component arrays on REVISE, including `[]` when the local set is empty.

Publication validates and certifies the complete effective result after exact parent/dependency stabilization.

## Schema evolution vs runtime data

ObjectTemplate mutation does not silently remediate existing Object data or ownership state.

Model-plane evolution and data-plane migration are distinct concerns:

- a new exact version may define a different valid schema within allowed evolution rules;
- existing Objects remain pinned to their current exact version until an explicit `Object.SCHEMA_CHANGE` is requested;
- model changes do not implicitly detach children, transform values or move Objects between lineages.

## Delete semantics

Individual version delete is allowed only for DRAFT and requires `expected_revision`.

Whole-lineage delete is allowed only when no external current reference remains, including version pins, parent/component references or runtime dependencies protected by the persistence model.

Owned local declarations are removed with their owning version only after semantic delete admission succeeds.

## Read semantics

Current read surfaces distinguish:

```text
stable lineage read
exact local-version read
effective-schema read
relationship-capability projection
```

The exact version read exposes the local snapshot and exact parent pin. Effective schema is a separate derived projection and identifies the declaring lineage of each effective member.

Ordinary reads are snapshot-consistent for the request but do not promise repeatability across requests.

## Key invariants

- stable lineage identity, abstract flag and parent lineage do not change through normal mutation;
- qualified template name is unique;
- inheritance is acyclic;
- every non-root version has an exact parent pin;
- lifecycle is monotonic and stable snapshots are immutable;
- DRAFT mutation uses `expected_revision` freshness;
- every persisted DRAFT is well-formed;
- every property uses an exact DataTypeVersion pin;
- property and slot names are unambiguous in the effective schema;
- effective schema is derived from exact parent chain plus local declarations;
- default is NULL or exact PUBLISHED same-lineage;
- PUBLISHED active-model direct dependencies remain PUBLISHED;
- model mutation performs no implicit runtime remediation;
- individual delete is DRAFT-only and whole-lineage delete is reference-safe;
- supported concurrent interleavings preserve all invariants above.
