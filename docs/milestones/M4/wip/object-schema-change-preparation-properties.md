# M4 WIP — Object SCHEMA_CHANGE preparation: property application

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records the first concrete preparation step after the route has obtained:

```text
S = coherent current Object aggregate snapshot
F = SHA-256(canonical_json(S))
MigrationPlan[(template_id, source_version, target_version)] READY
```

## Frozen preparation step

The property portion of the migration candidate is built entirely outside the mutation UoW:

```text
S.properties
+
MigrationPlan.property_rules
    -> target_properties
```

`S` remains immutable as the observed source snapshot associated with fingerprint `F`. The preparation step builds a separate candidate `target_properties` representation rather than mutating the source snapshot in place.

## Inputs already carried by MigrationPlan

The immutable migration plan already contains the source-to-target semantic rules required for each effective property identity, including the already-frozen cases such as:

```text
preserve
remove
add optional
add required + migration_default
optional -> required
required -> optional
SCALAR -> LIST
exact DataTypeVersion change
allowed combined deltas on one continuous property
```

Required target exact DataTypeVersion semantics / compiled validators are already available through the READY immutable plan/caching layer. Property application does not perform additional model-plane persistence traversal.

## Example

Source:

```json
{
  "hostname": "srv01",
  "description": "web",
  "port": 443
}
```

Plan effect:

```text
hostname     preserve + validate against target exact DTV
summary      source-only / absent in source example
"description" remove
port         SCALAR -> LIST
location     ADD required, migration_default = "rome"
```

Candidate result:

```json
{
  "hostname": "srv01",
  "port": [443],
  "location": "rome"
}
```

## Cost / authority boundary

This step performs:

```text
0 PostgreSQL statements
0 locks
0 additional cache fills on the normal READY path
```

It consumes only the already-observed Object properties plus immutable READY migration knowledge.

## Failure semantics

If a current source value cannot be migrated according to the target rule — for example, a preserved value fails the target exact DataTypeVersion semantics — preparation fails immediately.

```text
property migration failure
    -> terminate request
    -> no mutation UoW
    -> no Object DML
    -> no lifecycle event
```

This follows the M4 asymmetric preparation rule: conservative pre-UoW failures are acceptable; a successful candidate must later be protected by fingerprint revalidation before commit.

## Frozen boundary

After successful property preparation:

```text
target_properties READY
```

The next preparation step is to evaluate the current attached ownership edges contained in `S` against the component rules already compiled into `MigrationPlan`.
