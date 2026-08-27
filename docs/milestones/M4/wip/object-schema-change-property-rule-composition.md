# M4 WIP — Object SCHEMA_CHANGE property rule composition

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note freezes how multiple allowed deltas on one continuous ObjectTemplate property are composed by the reusable `Object.SCHEMA_CHANGE` migration planner.

## Scope

Property continuity is identified by:

```text
PropertySemanticKey = (declaring_template_id, property_name)
```

For one continuous semantic property, SOURCE and TARGET may differ simultaneously in:

```text
requiredness
value_mode
exact DataTypeVersion
migration_default
position
```

The planner must not model those differences as an ordered script of independent mutations such as:

```text
1. optional -> required
2. SCALAR -> LIST
3. DTV v2 -> v4
```

Such an ordering is artificial and creates unnecessary combination cases.

## Frozen model: one target-oriented rule per semantic property

For every semantic property present in both SOURCE and TARGET, the immutable MigrationPlan compiles one rule:

```text
ContinuousPropertyMigrationRule
    semantic_key
    source semantics
    target semantics
    compiled target validation/canonicalization
    canonical target migration_default when applicable
```

The rule is derived once from immutable SOURCE/TARGET exact effective schemas and is reusable for every Object migrating through the same `(template_id, source_version, target_version)` pair.

## Application to one Object snapshot

Given preparatory Object aggregate snapshot `S`, application follows this logical order:

```text
1. establish semantic continuity
2. inspect SOURCE value presence in S
3. preserve existing information when present
4. apply allowed information-preserving shape transformation
5. validate/canonicalize under complete TARGET exact-DTV semantics
6. materialize canonical sparse TARGET state
```

### SOURCE value absent

```text
TARGET optional
    -> remain absent

TARGET required
    -> use canonical TARGET migration_default
```

The target migration default belongs to the complete TARGET declaration. It is already canonical and certified for TARGET requiredness, value mode and exact DataTypeVersion.

Therefore an absent value does not pass through an artificial chain such as:

```text
scalar default
-> wrap as list
-> revalidate
```

If TARGET is a required LIST, its migration default is already a canonical non-empty TARGET LIST.

### SOURCE value present

Existing information must be preserved if TARGET can represent it.

```text
SOURCE SCALAR -> TARGET SCALAR
    x -> x

SOURCE SCALAR -> TARGET LIST
    x -> [x]

SOURCE LIST -> TARGET LIST
    preserve ordered list
```

`LIST -> SCALAR` is not a normal admitted ObjectTemplate evolution and therefore does not belong to this rule family.

After any allowed shape transformation, the resulting value is validated/canonicalized against the TARGET exact DataTypeVersion.

```text
TARGET compatible
    -> keep canonical target representation

TARGET incompatible
    -> schema migration failure
```

A target migration default is never used as remediation for incompatible existing information.

## Example: simultaneous requiredness, value-mode and DTV change

```text
SOURCE
    semantic key = (Server, location)
    optional
    SCALAR
    DTV v2

TARGET
    same semantic key
    required
    LIST
    DTV v4
    migration_default = ["unknown"]
```

Object with current value:

```json
{
  "location": "rome"
}
```

Candidate derivation:

```text
value present
-> preserve "rome"
-> SCALAR -> LIST
-> ["rome"]
-> validate/canonicalize each element under TARGET DTV v4
```

The migration default is not considered.

Object with absent value:

```json
{}
```

Candidate derivation:

```text
value absent
-> TARGET required
-> use ["unknown"] directly
```

## Target-oriented state construction

The complete Object target-property map is built from TARGET semantic properties, not by replaying textual JSON-key edits over SOURCE state.

For each TARGET semantic property, the compiled rule yields one of:

```text
preserved/transformed SOURCE value
canonical TARGET migration_default
absence
```

SOURCE-only semantic properties are not selected into the target state.

This prevents same-name/different-semantic-key values from being accidentally carried forward.

## Optimistic preparation

The concrete application of `ContinuousPropertyMigrationRule` happens outside the mutation UoW on preparatory aggregate snapshot `S`.

The complete TARGET candidate is finalized and validated before entering the short mutation UoW.

Inside the UoW:

```text
protect Object concurrency owner
recompute authoritative aggregate fingerprint F(S')

F(S') != F(S)
    -> discard prepared candidate
    -> rollback
    -> bounded restart from a fresh snapshot

F(S') == F(S)
    -> prepared candidate is still based on the current Object generation
    -> no property transformation/revalidation is repeated merely because commit has begun
```

Final mutable target-version admission remains a separate UoW responsibility.

## Frozen rule

```text
one continuous PropertySemanticKey
    -> one compiled target-oriented migration rule

absence
    -> optional: absent
    -> required: canonical TARGET migration_default

existing information
    -> preserve
    -> apply allowed SCALAR -> LIST widening when required
    -> validate/canonicalize against TARGET exact DTV
    -> incompatibility = migration failure

migration_default
    -> absence only
    -> never remediation for incompatible existing information

candidate construction
    -> outside UoW on snapshot S

commit
    -> protected fingerprint match + final mutable admissions
```
