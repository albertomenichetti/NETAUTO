# M4 WIP — Object lifecycle read discovery

Status: WIP / NON-NORMATIVE

## Scope

This note records the M4 discovery around `GET /objects/{id}/lifecycle-events` after the public `GET /objects/{id}` representation was reopened to include direct component children.

This is discovery only. It does not freeze the public contract and does not authorize implementation.

## Concrete consumer example

Consider current Object state:

```text
server-1
    hostname = srv01

    interfaces:
        eth0
        eth1
```

and a rename:

```text
server-1 -> web-01
```

The strong candidate current GET representation may include:

```json
{
  "id": "...",
  "canonical_name": "web-01",
  "template_id": "...",
  "template_version": 4,
  "properties": {
    "hostname": "srv01"
  },
  "components": {
    "interfaces": [
      {"id": "...", "canonical_name": "eth0"},
      {"id": "...", "canonical_name": "eth1"}
    ]
  }
}
```

The lifecycle RENAME event should not automatically duplicate that complete current representation in both `before` and `after`.

## Historical snapshot candidate

Current lifecycle persistence already stores intrinsic Object snapshots as:

```text
id
canonical_name
template_id
template_version
properties
```

For example:

```json
{
  "before": {
    "id": "...",
    "canonical_name": "server-1",
    "template_id": "...",
    "template_version": 4,
    "properties": {
      "hostname": "srv01"
    }
  },
  "after": {
    "id": "...",
    "canonical_name": "web-01",
    "template_id": "...",
    "template_version": 4,
    "properties": {
      "hostname": "srv01"
    }
  }
}
```

This remains the strong M4 candidate even if the current Object GET becomes richer.

Reason: ownership changes are already represented by distinct lifecycle events:

```text
ATTACH_TO
DETACH_FROM
```

which carry child/parent display metadata and the slot semantic identity. A RENAME or DATA_CHANGE should not have to reload and duplicate all direct children merely because the current GET representation includes them.

Concrete timeline:

```text
10:00 CREATED server-1
10:05 ATTACH eth0 -> server-1.interfaces
10:06 ATTACH eth1 -> server-1.interfaces
10:20 DATA_CHANGE hostname srv01 -> srv02
10:30 DETACH eth1 <- server-1.interfaces
```

The 10:20 DATA_CHANGE event does not need to repeat `eth0` and `eth1`; ownership history is represented by the ATTACH/DETACH events themselves.

## DTO consequence

Today lifecycle intrinsic event DTOs reuse `ObjectDto` for `before` / `after`.

If M4 enriches `ObjectDto` with current direct components, that DTO reuse becomes incorrect and unnecessarily expensive.

Strong candidate split:

```text
ObjectDto
    id
    canonical_name
    template_id
    template_version
    properties
    components

ObjectSnapshotDto
    id
    canonical_name
    template_id
    template_version
    properties
```

`ObjectSnapshotDto` is not an arbitrary lightweight copy. It directly matches the historical snapshot persisted by lifecycle events.

## Read data path

The current `GET /objects/{id}/lifecycle-events` projection is already close to the desired M4 shape:

```text
one statement
    -> verify target Object existence
    -> page lifecycle events involving the Object
    -> order by (occurred_at, id) DESC
    -> decode trusted historical carriers
```

Required public distinction remains:

```text
Object absent
    -> 404

Object exists + no matching events
    -> []

Object exists + matching events
    -> paged events
```

No ObjectTemplate/DataType/effective-schema lookup is needed for this read.

## Abstract architectural reading

The current public Object representation and the historical event snapshot are different projections with different responsibilities.

Current Object GET may expose direct first-level ownership for consumer usability. Lifecycle intrinsic snapshots remain bounded factual snapshots of the state changed by intrinsic Object mutations, while ownership history is modeled by explicit structural events.

This avoids making every intrinsic mutation and every historical event payload scale with the Object's current component cardinality.

## Candidate first-phase conclusion

- Keep intrinsic lifecycle `before` / `after` limited to `id`, `canonical_name`, `template_id`, `template_version`, and `properties`.
- Keep ATTACH/DETACH as the historical authority for ownership transitions.
- If `ObjectDto` becomes richer, introduce a separate historical `ObjectSnapshotDto` rather than expanding lifecycle snapshots.
- Keep the current one-statement target-rooted lifecycle read data path; no cache or new denormalization is justified for the read itself.
