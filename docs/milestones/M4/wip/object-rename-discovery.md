# M4 WIP — Object.RENAME discovery

Status: WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `Object.RENAME`. Lock redesign remains deferred to the global concurrency phase.

## AS-IS flow

Current application behavior:

1. validate the requested `canonical_name` before opening the mutation UoW;
2. acquire/stabilize the Object mutation lock;
3. load the current Object;
4. call `_validate_persisted_object(...)`, which loads the exact ObjectTemplateVersion effective schema and exact DataTypeVersion dependencies and re-canonicalizes the complete persisted property map;
5. construct the after-state with only `canonical_name` changed;
6. update `objects.canonical_name`;
7. insert one intrinsic `RENAME` lifecycle event containing complete before/after snapshots;
8. commit.

## Finding: persisted semantic recertification is unnecessary

`RENAME` changes only mutable human/search metadata. It preserves:

```text
Object.id
Object.template_id
Object.template_version
Object.properties
ownership
Relationships
```

The requested name is already validated as pure CPU work before the UoW. Re-loading ObjectTemplate/DataType semantics and re-canonicalizing the persisted property map is therefore unrelated to deciding or validating the rename candidate.

Candidate M4 path:

```text
validate_canonical_name(new_name)   # before write UoW

lock/stabilize current Object
load current Object

construct after = before with canonical_name replaced

UPDATE objects.canonical_name
INSERT intrinsic RENAME event
COMMIT
```

No ObjectTemplate cache, DataType cache, effective-schema materialization, ancestry projection, component state or Relationship state is required by the normal path.

## Lifecycle

The intrinsic event needs the complete current Object before/after snapshots. The already-loaded Object supplies both snapshots; the only semantic difference is `canonical_name`.

## Same-name request remains OPEN

Current implementation performs the UPDATE and emits a RENAME event even when the requested name equals the current name.

Unlike `DATA_CHANGE`, current architecture does not explicitly define same-name RENAME as a semantic no-op. M4 must therefore decide this behavior explicitly rather than silently changing it during optimization.

## Candidate conclusion

`Object.RENAME` should not re-certify persisted Object properties against ObjectTemplate/DataType semantics. Its minimal first-phase data path is current Object state from PostgreSQL plus one name UPDATE and one lifecycle event. Same-name behavior remains an explicit open semantic decision.