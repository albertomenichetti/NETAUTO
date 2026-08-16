# ObjectTemplate — Current AS-IS

## Responsibility

An `ObjectTemplate` lineage is the stable identity of an entity type. An `ObjectTemplateVersion` is an exact, versioned schema snapshot for that type.

ObjectTemplate defines:

- stable inheritance between template lineages;
- exact parent-version pinning per version snapshot;
- typed properties;
- ownership/component slots;
- effective-schema derivation;
- lifecycle/default policy;
- model-plane dependency certification.

ObjectTemplate properties describe values. Components describe ownership/composition of child Objects that retain their own identity. Relationships are a separate association model and are not ownership slots.

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

`abstract=true` prevents direct Object instantiation but does not prevent the lineage from being used as an inheritance, component-target or Relationship compatibility contract.

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

Version allocation uses `max(existing)+1`; gaps are allowed and a deleted highest DRAFT version number may be reused.

`create-next` creates a new DRAFT revision 1 by cloning an eligible exact PUBLISHED/DEPRECATED source snapshot. The source need not be the current maximum. Multiple DRAFT versions may coexist.

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
- PUBLISHED may receive new bindings and may be default;
- DEPRECATED remains valid for historical exact bindings but cannot receive new direct lifecycle-sensitive bindings.

The lineage default is NULL or an exact PUBLISHED version of the same lineage. First publish may auto-establish a missing default; later publications do not replace it automatically.

## Properties

A local property declaration belongs to one exact ObjectTemplateVersion and contains:

```text
name
position
datatype_id
datatype_version
value_mode
required
migration_default
```

Every property materializes an exact DataTypeVersion pin.

Current value modes:

```text
SCALAR
LIST
```

Property presence/cardinality belongs to the property contract, not the DataType contract.

```text
SCALAR + required=false -> 0..1
SCALAR + required=true  -> 1
LIST   + required=false -> 0..N
LIST   + required=true  -> 1..N
```

The `migration_default` rule is exact and unconditional for current property declarations:

```text
required = false
    -> migration_default is absent / SQL NULL

required = true + SCALAR
    -> migration_default contains exactly one concrete valid value

required = true + LIST
    -> migration_default contains a non-empty ordered list of valid values
```

Every migration-default value is parsed, canonicalized and validated against the exact pinned DataTypeVersion.

`migration_default` fills absence during controlled Object schema migration. It is not an Object CREATE default and never overwrites an existing incompatible source value.

Property and component names share one effective member namespace; shadow/override ambiguity is not allowed.

### Property semantic identity and history

Property continuity uses:

```text
PropertySemanticKey = (declaring_template_id, name)
```

The declaring lineage is the lineage that locally owns the declaration.

A property introduced only in DRAFT and never published remains editorial. Before first publication its declaration may be revised, provided the DRAFT remains well-formed.

After first publication, normal evolution preserves historical property identity:

- `name` and `datatype_id` are stable;
- exact `datatype_version`, `required`, `migration_default` and `position` may evolve subject to validation;
- current normal value-mode evolution is monotonic `SCALAR -> LIST`;
- `LIST -> SCALAR` or cross-DataType-lineage migration requires a future explicit controlled migration capability.

A published property may be removed in a later version. If the **same declaring lineage** later reintroduces the same name, it retains the same historical semantic identity and all evolution constraints continue across the gap. Remove/re-add cannot reset stable `name`, `datatype_id`, value-mode direction or other historical rules.

A property with the same effective name but a different declaring lineage is a different semantic property.

`position` is explicit declaration state and is the ordering authority. Request-array order is not a second ordering authority.

## Components / ownership slots

A component declaration is a named `0..N` ownership slot containing:

```text
name
position
target_template_id
```

The target is a stable ObjectTemplate lineage, not an exact version.

Slot declaration admission requires only that the target lineage exist. The target:

- may be abstract;
- need not have a default version;
- need not currently have a PUBLISHED exact version;
- is not exact-version pinned by the slot.

A child Object is compatible when its stable template lineage is the target lineage or a descendant lineage.

Normal slot evolution may widen the target toward an ancestor. Narrowing or migration to an unrelated target requires a future explicit workflow because it can invalidate current ownership state.

### Slot semantic identity and history

Slot continuity uses:

```text
SlotSemanticKey = (declaring_template_id, name)
```

A slot introduced only in DRAFT and never published remains editorial.

After first publication the slot name is stable under normal evolution. A published slot may be removed in a later version. If the **same declaring lineage** later reintroduces the same name, historical semantic identity and target-evolution constraints continue across the gap. Remove/re-add cannot be used to bypass target-widening rules.

A same-name slot declared by a different lineage is a different semantic slot.

Ownership runtime edges are interpreted against the parent Object's **current exact effective schema**, not against a version-pinned slot row.

`position` is positive, unique within the local component set and presentation/order metadata only; gaps are allowed.

## Effective schema

The effective schema is derived from:

```text
exact parent chain
+
local property declarations
+
local component declarations
```

It is a semantic projection, not a separately authoritative materialized schema.

No authoritative effective-schema cache, generic compiled schema representation or JSON Schema artifact exists in the current architecture.

A DRAFT must remain well-formed. Publication performs the stronger certification required to make the exact schema an active model-plane dependency source.

The effective schema must preserve:

- acyclic exact inheritance;
- unique effective property/slot names across one shared member namespace;
- exact DataType property pins;
- valid property cardinality and migration defaults;
- existing stable component-target lineages;
- stable semantic identity of inherited/local members;
- lifecycle-admissible direct exact dependencies.

A child lineage cannot override, hide or remove an inherited property or slot.

## Active model graph

A PUBLISHED ObjectTemplateVersion belongs to the active model graph.

Every direct lifecycle-sensitive dependency of a PUBLISHED version must remain PUBLISHED, including:

- exact parent ObjectTemplateVersion;
- exact DataTypeVersion pins of properties.

A dependency cannot be deprecated while a direct active PUBLISHED consumer remains.

Publication of a consumer and deprecation of a dependency are strongly consistent and cannot both commit if the resulting graph would contain an active edge to a non-PUBLISHED exact dependency.

The invariant is enforced on direct dependencies. Recursive validity follows because each PUBLISHED dependency-owning model is itself certified.

Component target lineages and Relationship endpoint lineages are stable-lineage references, not active exact-version dependencies.

## Create/revise/publication model

ObjectTemplate CREATE establishes a stable lineage and an initial DRAFT v1.

REVISE is complete replacement of the **local** candidate declarations for the exact DRAFT. It is not generic partial PATCH of the effective schema.

The public command requires explicit local property/component arrays on REVISE, including `[]` for an empty local set.

For non-root lineages, REVISE may explicitly select an exact parent version or omit it to intentionally resolve/rebind through the current parent default. Root lineages forbid parent-version input.

Publication validates and certifies the complete effective result after exact parent/dependency stabilization.

## Schema evolution vs runtime data

ObjectTemplate mutation does not silently remediate existing Object data or ownership state.

Model-plane evolution and data-plane migration are distinct:

- a new exact version may define a different valid schema within allowed evolution rules;
- existing Objects remain pinned to their current exact version until explicit `Object.SCHEMA_CHANGE`;
- publishing a version that removes a slot is allowed even when existing Objects on older versions still use that slot;
- an individual Object migration fails until its current values/attachments can be preserved under the target;
- model changes do not implicitly detach children, transform values or move Objects between lineages.

## Delete semantics

Individual version delete is allowed only for DRAFT and requires `expected_revision`.

Whole-lineage delete removes the lineage and all of its owned state atomically after semantic admission:

```text
ObjectTemplate
    -> owned ObjectTemplateVersion rows
    -> owned local Property/Component declarations
```

Outgoing references contained only in that owned state — for example exact parent pins or local property pins to DataTypeVersions — disappear with the aggregate and are not themselves blockers of deleting the consumer lineage.

Whole-lineage delete is allowed only when no **external current reference into the lineage or one of its exact versions** remains, including:

- child ObjectTemplate lineages that use it as stable parent;
- external component declarations that target it;
- RelationshipResolution endpoint references;
- runtime Objects pinned to one of its exact versions;
- other incoming cross-aggregate references protected by the persistence model.

The UoW provides bounded semantic blocker diagnostics; PostgreSQL `RESTRICT` foreign keys remain the final race authority. No external reference is removed implicitly to make deletion admissible.

## Read semantics

Current read surfaces distinguish:

```text
stable lineage read
exact local-version read
effective-schema read
relationship-capability projection
```

The exact version read exposes the local snapshot and exact parent pin. Effective schema is a separate derived projection and identifies the declaring lineage of each member.

Ordinary reads are snapshot-consistent for the request but do not promise repeatability across requests.

## Key invariants

- stable lineage identity, abstract flag and parent lineage do not change through normal mutation;
- qualified template name is unique;
- inheritance is acyclic;
- every non-root version has an exact parent pin;
- lifecycle is monotonic and PUBLISHED/DEPRECATED snapshots are immutable;
- DRAFT mutation uses `expected_revision` freshness;
- every persisted DRAFT is well-formed;
- every property uses an exact DataTypeVersion pin;
- optional properties have no migration default; required SCALAR/LIST properties always have the corresponding valid migration default;
- property and slot names are unambiguous in the effective schema;
- property/slot historical semantic identity survives remove/re-add by the same declaring lineage;
- effective schema is derived from exact parent chain plus local declarations;
- component targets are stable lineages and may be abstract/unversioned at declaration time;
- default is NULL or exact PUBLISHED same-lineage;
- PUBLISHED active-model direct exact dependencies remain PUBLISHED;
- model mutation performs no implicit runtime remediation;
- individual delete is DRAFT-only and whole-lineage delete is safe against incoming external references;
- supported concurrent interleavings preserve all invariants above.
