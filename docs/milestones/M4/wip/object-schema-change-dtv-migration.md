# M4 WIP — Object SCHEMA_CHANGE exact DataTypeVersion migration semantics

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the agreed runtime semantics for a continuous ObjectTemplate property whose exact DataTypeVersion changes across `Object.SCHEMA_CHANGE` while retaining the same stable DataType lineage.

It complements the broader property-migration note and uses the optimistic-preparation protocol already frozen for Object mutations.

## Scope and continuity

The property keeps the same semantic identity:

```text
PropertySemanticKey = (declaring_template_id, property_name)
```

and the same stable DataType lineage:

```text
SOURCE
    datatype_id = D
    datatype_version = VS

TARGET
    datatype_id = D
    datatype_version = VT
```

Changing `datatype_id` is not normal ObjectTemplate evolution and is outside this rule.

All DataTypeVersions in one DataType lineage use the same stable PrimitiveType. Therefore this delta does not perform a cross-primitive conversion; it applies a different immutable exact constraint snapshot to the same atomic domain.

## Existing SOURCE value

Existing information is preserved if and only if it is representable under the TARGET exact DataTypeVersion after any other allowed property-shape transformation.

Frozen rule:

```text
SOURCE value present
    -> preserve existing information
    -> validate/canonicalize against TARGET exact DTV

TARGET-compatible
    -> keep resulting canonical value

TARGET-incompatible
    -> schema migration failure
```

There is no fallback to `migration_default` for an incompatible existing value.

`migration_default` fills absence only; it is not a remediation mechanism for information that exists but no longer satisfies the TARGET exact domain.

Example:

```text
SOURCE DTV
    core.string
    max_length = 20

TARGET DTV
    core.string
    max_length = 10
```

An Object value:

```json
{
  "hostname": "very-long-hostname"
}
```

cannot migrate to the TARGET exact schema and causes `SCHEMA_CHANGE` failure.

Conversely, if the TARGET domain widens and the existing value remains valid, it is preserved.

## LIST value

For a continuous LIST property, list ordering remains semantic and is preserved.

```text
SOURCE list value
    -> preserve item order
    -> validate/canonicalize every element under TARGET exact DTV

any element incompatible
    -> migration failure
```

No incompatible element is silently removed or replaced.

## SOURCE value absent

For a continuous optional property whose runtime value is absent:

```text
TARGET optional
    -> remain absent
    -> no runtime value validation is needed
```

If TARGET requiredness independently requires a value, the already-frozen requiredness rule applies:

```text
SOURCE value absent
TARGET required
    -> use canonical TARGET migration_default
```

That target migration default belongs to the immutable TARGET ObjectTemplateVersion and is already certified against the TARGET exact DTV and value mode.

## Combination with SCALAR -> LIST

If value mode widens at the same time as the exact DTV changes:

```text
SOURCE
    SCALAR + DTV VS
    value = x

TARGET
    LIST + DTV VT
```

candidate preparation performs:

```text
x
-> [x]
-> validate/canonicalize x under TARGET DTV VT
-> retain singleton ordered list if valid
```

If `x` is not valid under the TARGET exact DataTypeVersion, migration fails.

The widening does not authorize information loss or fallback to a migration default.

## Optimistic-preparation placement

Exact-DTV validation/canonicalization is performed outside the mutation UoW while applying the immutable MigrationPlan to preparatory Object aggregate snapshot `S`.

```text
outside UoW
    read snapshot S
    compute F(S)
    apply MigrationPlan(source,target)
    validate/canonicalize values under TARGET exact DTV semantics
    build complete TARGET candidate C
```

The TARGET validator/compiled semantic structures are immutable and reusable because the exact TARGET ObjectTemplateVersion and exact TARGET DataTypeVersion are immutable.

Inside the short mutation UoW:

```text
protect Object concurrency owner
recompute authoritative current fingerprint

fingerprint != F(S)
    -> discard C
    -> rollback
    -> bounded restart

fingerprint == F(S)
    -> C is still derived from the current Object generation
    -> do not repeat DTV validation merely because the UoW started
```

Final mutable TARGET admission, such as the requirement that the target ObjectTemplateVersion still be PUBLISHED through binding commit, remains a separate UoW responsibility.

## Frozen rules

```text
exact DTV change on continuous property
    -> datatype_id remains the same
    -> PrimitiveType remains the same

existing value
    -> preserve information
    -> validate/canonicalize against TARGET exact DTV
    -> incompatibility = migration failure

LIST
    -> preserve order
    -> validate every element
    -> any incompatible element = migration failure

absent optional value
    -> remains absent

absence + TARGET requiredness
    -> canonical TARGET migration_default

combined SCALAR -> LIST + DTV change
    -> x becomes [x]
    -> validate x under TARGET exact DTV

never
    -> cross-DataType-lineage conversion
    -> primitive conversion
    -> silent drop of incompatible existing information
    -> fallback to migration_default for incompatible existing information
```

This delta is now frozen as an input to the next step: define the composition/order of multiple simultaneous deltas on one continuous semantic property.