# M4 WIP — Object SCHEMA_CHANGE property migration semantics

Status: PARTIAL FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the Object runtime-property migration semantics frozen incrementally for `Object.SCHEMA_CHANGE` after the source/target effective-schema delta taxonomy was established.

The migration planner compares immutable exact effective schemas and identifies property continuity through:

```text
PropertySemanticKey = (declaring_template_id, property_name)
```

Name equality alone never establishes continuity.

The execution model used by the property rules in this note is the optimistic-preparation pattern frozen separately for Object mutations:

```text
outside mutation UoW
    read one Object aggregate snapshot S
    compute its deterministic concurrency fingerprint F(S)
    apply immutable MigrationPlan(source,target) to S
    build, validate and canonicalize the complete TARGET candidate C

inside short mutation UoW
    protect the Object concurrency owner
    recompute the authoritative current fingerprint F(S')

    F(S') != F(S)
        -> discard C
        -> rollback
        -> bounded restart from a fresh snapshot

    F(S') == F(S)
        -> C is still derived from the current Object generation
        -> no property migration/revalidation is repeated merely because the UoW has started
```

Therefore references below to a current SOURCE value mean the value read from the preparatory aggregate snapshot `S`. Correctness is established at commit time by the protected fingerprint comparison rather than by rebuilding the candidate under lock.

## ADD optional property

A property whose semantic key is absent from SOURCE and present as optional in TARGET is classified as an immutable plan operation:

```text
ADD_OPTIONAL
    semantic_key
    target_name
```

Runtime effect:

```text
resulting Object property state -> key absent
```

No placeholder is materialized. Object sparse JSONB semantics forbid inventing either JSON null or an artificial empty/default value for a newly added optional property.

Example:

```text
SOURCE effective schema
    hostname required

TARGET effective schema
    hostname required
    description optional
```

```json
before = {
  "hostname": "srv01"
}
```

migrates to:

```json
after = {
  "hostname": "srv01"
}
```

No per-Object branch decision is required for this delta class.

## ADD required property

A property whose semantic key is absent from SOURCE and present as required in TARGET is classified as an immutable plan operation:

```text
ADD_REQUIRED
    semantic_key
    target_name
    canonical_target_migration_default
```

Runtime effect:

```text
resulting Object property state
    -> add target property with TARGET migration_default
```

Example:

```text
SOURCE effective schema
    hostname required

TARGET effective schema
    hostname required
    asset_id required
        migration_default = "unknown"
```

```json
before = {
  "hostname": "srv01"
}
```

migrates to:

```json
after = {
  "hostname": "srv01",
  "asset_id": "unknown"
}
```

The `migration_default` belongs to an exact immutable TARGET ObjectTemplateVersion and was already parsed, canonicalized and certified against its exact target DataTypeVersion/value mode as part of model publication. Object migration consumes the already canonical target default; it does not re-certify that model-plane declaration for every Object.

No per-Object branch decision is required for this delta class.

## REMOVE property

A property whose semantic key is present in SOURCE and absent from TARGET is classified as an immutable plan operation:

```text
REMOVE
    semantic_key
    source_name
```

Runtime effect:

```text
TARGET Object property state
    -> property does not exist
```

The removal rule is independent of SOURCE requiredness.

### SOURCE optional

```text
value present -> drop
value absent  -> no runtime action
```

### SOURCE required

A valid SOURCE Object has the required value present. The value is dropped because requiredness constrains state only while that semantic property belongs to the governing schema.

```text
required SOURCE property
    -> drop
```

No archive, extras bucket, migration default or side-channel preservation is produced for removed properties.

Example:

```text
SOURCE effective schema
    hostname required
    description optional

TARGET effective schema
    hostname required
```

```json
before = {
  "hostname": "srv01",
  "description": "core server"
}
```

migrates to:

```json
after = {
  "hostname": "srv01"
}
```

The plan decision is deterministic from SOURCE/TARGET immutable semantics. The preparatory snapshot only determines whether an optional removed JSON key happens to be present while constructing the candidate.

## OPTIONAL -> REQUIRED

A continuous semantic property may change from optional in SOURCE to required in TARGET:

```text
SOURCE required = false
TARGET required = true
```

The immutable MigrationPlan carries the conditional rule and the canonical TARGET `migration_default`:

```text
OPTIONAL_TO_REQUIRED
    semantic_key
    target_name
    canonical_target_migration_default
    target transformation/validation semantics as applicable
```

### SOURCE snapshot value present

If preparatory snapshot `S` contains the continuous semantic property's value, existing information is preserved.

```text
value present
    -> preserve existing SOURCE information
    -> apply any other TARGET migration/validation rules for this same semantic property
    -> never replace it with migration_default merely because TARGET is required
```

Example:

```text
SOURCE
    location optional

TARGET
    location required
    migration_default = "unknown"
```

```json
before = {
  "hostname": "srv01",
  "location": "rome"
}
```

migrates, assuming all other TARGET semantics are satisfied, to:

```json
after = {
  "hostname": "srv01",
  "location": "rome"
}
```

If the existing value is incompatible with another simultaneous TARGET change such as a narrower exact DataTypeVersion, schema migration fails. The migration default is not a remediation fallback for incompatible existing information.

### SOURCE snapshot value absent

If preparatory snapshot `S` does not contain the property, TARGET requiredness needs a value and the canonical TARGET `migration_default` is used.

```text
value absent
    -> TARGET migration_default
```

Example:

```json
before = {
  "hostname": "srv01"
}
```

migrates to:

```json
after = {
  "hostname": "srv01",
  "location": "unknown"
}
```

### Optimistic-preparation placement

The concrete present/absent branch is selected **outside** the mutation UoW from preparatory snapshot `S`, and the complete TARGET candidate is finalized there.

Correctness does not rely on that unlocked observation remaining current indefinitely. The short mutation UoW protects the Object concurrency owner and compares the authoritative current fingerprint with `F(S)`:

```text
fingerprint unchanged
    -> the previously selected branch and complete candidate remain valid

fingerprint changed
    -> candidate discarded
    -> rollback
    -> bounded restart from a fresh Object snapshot
```

The information-preservation invariant remains:

```text
migration_default fills absence only
migration_default never overwrites existing incompatible information
```

## REQUIRED -> OPTIONAL

A continuous semantic property may change from required in SOURCE to optional in TARGET:

```text
SOURCE required = true
TARGET required = false
```

A valid SOURCE Object necessarily contains the property value. Making the property optional in TARGET relaxes the presence requirement; it does not authorize discarding information that already exists.

Frozen rule:

```text
required -> optional
    -> preserve existing SOURCE value
    -> apply any other TARGET migration/validation rules for the same semantic property
    -> never drop merely because TARGET permits absence
    -> no migration_default
```

Example:

```text
SOURCE
    location required

TARGET
    location optional
```

```json
before = {
  "hostname": "srv01",
  "location": "rome"
}
```

migrates, assuming all other TARGET semantics remain satisfied, to:

```json
after = {
  "hostname": "srv01",
  "location": "rome"
}
```

If another simultaneous TARGET delta changes how the continuous semantic property is represented, that rule is also applied. For example:

```text
SOURCE
    required SCALAR

TARGET
    optional LIST
```

preserves the information through the allowed widening:

```text
"rome" -> ["rome"]
```

Likewise, if the TARGET exact DataTypeVersion changes, the existing value must satisfy the TARGET contract after any allowed shape transformation. If it does not, schema migration fails.

The migration must not interpret optional TARGET cardinality as permission to repair incompatibility by dropping a present source value:

```text
existing value incompatible with TARGET
    -> migration failure
    -> NOT automatic absence
```

There is no migration default in TARGET because optional declarations do not carry one.

The concrete value transformation and validation are performed outside the UoW while constructing the complete TARGET candidate from snapshot `S`. The UoW later accepts that candidate only if the protected aggregate fingerprint still matches `F(S)`.

The information-preservation invariant is:

```text
TARGET allowing absence does not authorize loss of existing SOURCE information
```

## SCALAR -> LIST

A continuous semantic property may widen from SCALAR in SOURCE to LIST in TARGET:

```text
SOURCE value_mode = SCALAR
TARGET value_mode = LIST
```

This is the current normal monotonic value-mode evolution. `LIST -> SCALAR` is outside the normal contract.

Conceptual immutable plan operation:

```text
SCALAR_TO_LIST
    semantic_key
    target_name
    compiled TARGET exact-DTV validation/canonicalization semantics
```

### SOURCE snapshot value present

Existing scalar information is preserved as a singleton ordered list:

```text
x -> [x]
```

Example:

```json
before = {
  "hostname": "srv01",
  "tag": "core"
}
```

migrates to:

```json
after = {
  "hostname": "srv01",
  "tag": ["core"]
}
```

The singleton representation is then validated/canonicalized under the complete TARGET semantics. The widening operation alone does not prove target-value validity.

If the exact DataTypeVersion also changes:

```text
SOURCE
    SCALAR + DTV v2

TARGET
    LIST + DTV v4
```

candidate preparation performs:

```text
x
-> [x]
-> validate every element under TARGET DTV v4
-> canonicalize TARGET list representation
```

If the existing SOURCE value cannot be represented under the TARGET contract, migration fails. It is never silently dropped and never replaced with a migration default merely because a default exists.

### SOURCE snapshot value absent

For an optional SOURCE SCALAR property that is absent:

```text
optional SCALAR -> optional LIST
    absent -> absent
```

If TARGET requiredness changes independently:

```text
optional SCALAR -> required LIST
```

then the already-frozen requiredness rule applies:

```text
SOURCE value present
    -> x -> [x] -> TARGET validation/canonicalization

SOURCE value absent
    -> canonical TARGET migration_default
       which is already a non-empty valid TARGET LIST
```

For `required SCALAR -> required LIST`, valid SOURCE state guarantees one existing scalar value and therefore:

```text
x -> [x]
```

before TARGET validation/canonicalization.

### Optimistic-preparation placement

The scalar-to-list transformation, any simultaneous target-DTV validation and canonicalization, and the construction of the complete TARGET candidate all happen **outside** the mutation UoW from preparatory snapshot `S`.

Inside the short UoW:

```text
protect Object concurrency owner
recompute authoritative current fingerprint

fingerprint != F(S)
    -> discard prepared candidate
    -> rollback + bounded restart

fingerprint == F(S)
    -> prepared singleton-list transformation is still based on the current Object generation
    -> do not repeat SCALAR -> LIST conversion or target validation merely because the UoW started
```

Frozen information-preservation rule:

```text
existing SCALAR information
    -> singleton LIST containing that information
    -> TARGET validation/canonicalization

absence
    -> remains absence unless TARGET requiredness independently requires migration_default

TARGET incompatibility
    -> migration failure
    -> never silent drop/default replacement
```

## Same name without semantic continuity

If SOURCE and TARGET expose the same effective property name under different semantic keys, the value is never carried forward merely because the JSON key text is equal.

Example:

```text
SOURCE
    (Device, hostname)

TARGET
    (Server, hostname)
```

is:

```text
REMOVE (Device, hostname)
ADD    (Server, hostname)
```

not one continuous property.

Consequences:

```text
new TARGET property optional
    -> old semantic value is discarded
    -> TARGET property is absent

new TARGET property required
    -> old semantic value is discarded
    -> TARGET migration_default is used
```

For example, if SOURCE contains:

```json
{
  "hostname": "srv01"
}
```

but TARGET replaces `(Device, hostname)` with required `(Server, hostname)` whose migration default is `"unknown"`, the result is:

```json
{
  "hostname": "unknown"
}
```

not `"srv01"`.

This rule prevents accidental preservation across semantic-identity replacement.

## Target-state construction rule

The migration is not modeled as an unsafe sequence of JSON-key edits where textual name collisions can accidentally transfer values across semantic identities.

The target property state is derived from TARGET semantic properties. For each TARGET semantic key, the MigrationPlan and preparatory SOURCE snapshot determine whether the target candidate must:

```text
preserve/transform a value from the continuous SOURCE semantic property
use the canonical TARGET migration_default
remain absent
```

SOURCE-only semantic properties are not selected into the target state.

This target-oriented construction rule makes semantic identity authoritative even when a removed SOURCE property and an added TARGET property use the same JSON field name.

## MigrationPlan and optimistic-preparation consequence

All SOURCE/TARGET schema knowledge used by these rules is immutable and can therefore be compiled into the reusable migration plan:

```text
ObjectTemplateMigrationPlanCache[
    (template_id, source_version, target_version)
]
```

The plan itself is Object-independent. One Object's complete candidate is produced by applying that immutable plan to preparatory aggregate snapshot `S` outside the UoW.

The short mutation UoW does not rebuild that candidate. It only accepts it if the protected Object aggregate still matches the concurrency fingerprint associated with `S`, in addition to any final mutable admission predicates owned by the schema-change command.

## Frozen in this increment

```text
ADD optional
    -> resulting key absent

ADD required
    -> resulting value = canonical TARGET migration_default

REMOVE optional
    -> present value dropped; absent remains absent

REMOVE required
    -> value dropped

OPTIONAL -> REQUIRED
    source snapshot value present
        -> preserve existing information
        -> apply simultaneous TARGET transformations/validation
        -> never fallback to migration_default if incompatible

    source snapshot value absent
        -> canonical TARGET migration_default

REQUIRED -> OPTIONAL
    -> preserve existing SOURCE information
    -> apply simultaneous TARGET transformation/validation rules
    -> never drop merely because TARGET permits absence
    -> incompatibility causes migration failure
    -> no migration_default

SCALAR -> LIST
    source value present
        -> x becomes singleton [x]
        -> validate/canonicalize against TARGET semantics

    source optional value absent
        -> remains absent unless TARGET requiredness independently supplies migration_default

    target incompatibility
        -> migration failure
        -> no silent drop/default replacement

optimistic preparation
    -> concrete Object property branches/transforms/validation occur outside UoW on snapshot S
    -> UoW accepts prepared candidate only if protected fingerprint still equals F(S)
    -> fingerprint mismatch discards candidate and causes bounded restart

removed property
    -> no archive/extras/default/remediation behavior

same name but different PropertySemanticKey
    -> no carry-forward by name coincidence

target-state construction
    -> build from TARGET semantic properties, not naive JSON-key mutation order
```

Still to define incrementally:

```text
exact DataTypeVersion change
combined deltas on one continuous semantic property
```
