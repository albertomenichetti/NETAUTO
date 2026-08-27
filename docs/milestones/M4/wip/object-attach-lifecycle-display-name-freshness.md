# M4 WIP — Object ATTACH lifecycle display-name freshness

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note freezes the freshness requirement for human-readable Object names carried by `ATTACH_TO` lifecycle rows in the M4 TO-BE batch ATTACH design.

Public operation under review:

```http
POST /api/v1/core/objects/{parent_object_id}/components/{slot_name}
```

with a batch of requested `child_object_ids`.

## Decision

The ownership fact itself remains correctness-bearing and strongly protected:

```text
child_object_id
parent_object_id
slot_declaring_template_id
slot_name
```

The lifecycle row may additionally carry human-readable display metadata such as:

```text
child canonical_name
parent canonical_name
```

Those names are not part of ownership identity or admission. They are historical display metadata.

M4 therefore does **not** acquire additional row locks or perform additional fresh reads solely to guarantee that these names exactly match the names current at the instant the ownership edge commits.

The lifecycle bulk INSERT may use the names already obtained during ATTACH preparation.

## Accepted race

A concurrent `RENAME` may commit between the preparatory read and the ATTACH mutation.

For example:

```text
preparation sees child canonical_name = eth0

concurrent RENAME commits child canonical_name = uplink0

ATTACH commits the ownership edge
ATTACH_TO lifecycle row may still carry canonical_name = eth0
```

This is explicitly acceptable.

The persisted current Object row remains authoritative for the current name, while the lifecycle display name is treated as a best-effort historical label.

## Safety boundary

This relaxation applies only to descriptive name metadata in ownership lifecycle events.

It does not relax correctness of:

- parent/child Object identity;
- one-owner uniqueness;
- slot semantic identity;
- slot compatibility;
- ownership acyclicity;
- atomic edge/event commit;
- parent exact-schema coherence.

No extra query or lock is justified solely for lifecycle display-name freshness.

## Cost consequence

The ATTACH mutation can keep the lifecycle write as one bulk INSERT after the bulk ownership INSERT:

```text
Q4  one multi-row INSERT object_components
Q5  one multi-row INSERT ATTACH_TO lifecycle events
```

Names needed by Q5 are reused from preparation; no post-lock Object-name reread is added.
