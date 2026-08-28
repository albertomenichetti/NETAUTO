# M4 WIP — Object ATTACH bulk child read

Status: RECONCILED DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

## Scope

This note supersedes the earlier candidate that joined current ownership facts into the preliminary child read for batch Object ATTACH.

The final route-local authority is `to-be-api-object-attach-batch.md`.

## Final decision

After the parent binding is read and the requested slot is resolved from the READY `component_schema` facet, ATTACH performs one bulk PostgreSQL read over all requested child ids.

That read contains only current Object facts needed for normal semantic preparation:

```text
id
template_id
canonical_name
```

It does **not** join or otherwise pre-read `object_components`.

The exact child `template_version` and `properties` are also unnecessary for ATTACH compatibility.

## Why current owner was removed from preparation

The earlier candidate combined child existence/lineage facts and current owner facts in one query. M4 later chose a simpler concurrency model:

```text
preparation
    -> no owner observation

protected Q3 under OWNERSHIP_GRAPH_WRITE_GATE
    -> certify whether any requested child is currently owned
    -> certify root-only cycle predicate

Q4 bulk INSERT
    -> PK(child_object_id) remains final single-owner persistence authority
```

A preliminary owner observation would therefore be staleable and redundant. Removing it keeps mutable ownership admission inside the protected mutation state where it matters.

## Child preparation responsibilities

The one bulk child read answers only:

```text
does every requested child exist?
which stable template_id does each child have?
which DISTINCT source lineages require ancestry compatibility checks?
what canonical_name is already available for lifecycle display metadata?
```

Self-reference is a request semantic check using the known parent id and requested child ids; it does not require ownership data.

## Compatibility handoff

After the read:

```text
collect DISTINCT child.template_id
    -> resolve cache[source][slot.target_template_id]
    -> TRUE / FALSE / MISS
```

Missing ancestry sources are loaded in one bounded bulk statement and then marked READY.

Different stable child template lineages may coexist in the same batch.

## Frozen conclusion

```text
preliminary child DB read
    = Object existence + stable lineage + lifecycle display name only

current ownership
    = not read in preparation
    = certified by protected Q3
    = finally enforced by Q4 PK arbitration
```

There is no N+1 child read and no current-owner preparatory query/join.
