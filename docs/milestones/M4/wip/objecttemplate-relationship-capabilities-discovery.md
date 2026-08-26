# M4 WIP — ObjectTemplate relationship capabilities discovery

**Status:** WIP / NON-NORMATIVE

## Scope

Audit of the ObjectTemplate relationship-capability read path under the M4 denormalization/cache discovery.

## Current M3 shape

The current read is already a single authoritative PostgreSQL statement. It computes the requested ObjectTemplate stable ancestry with a recursive CTE, then projects applicable RelationshipResolution rows whose Definition currently has at least one PUBLISHED exact version. The projection also carries current mutable Resolution names and RelationshipDefinition.default_version while preserving the distinction between a missing ObjectTemplate target and an existing target with an empty capability page.

## M4 candidate

M4 already has a strong candidate stable lineage closure:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

The closure should include the reflexive row `(T, T, 0)` so exact-lineage applicability and ancestor applicability use the same predicate.

The capability read can therefore remain one authoritative SQL statement while replacing the recursive ancestry derivation with a join against `object_template_ancestry`:

```text
requested ObjectTemplate
    -> current existence marker

relationship_resolutions
    JOIN object_template_ancestry
      descendant_template_id = requested template
      ancestor_template_id = resolution.from_template_id

relationship_definitions
    -> current default_version

relationship_definition_versions
    -> EXISTS current PUBLISHED exact version
```

Current name filter, resolution-id keyset cursor and limit remain unchanged.

## Current state that must remain PostgreSQL-owned

The capability collection cannot be served solely from immutable/stable caches because public membership and fields depend on current mutable state:

- `RelationshipResolution.name` is mutable;
- `RelationshipDefinition.default_version` is mutable;
- capability exposure requires at least one exact `PUBLISHED` RelationshipDefinitionVersion;
- requested ObjectTemplate current existence must still be authoritative.

The `EXISTS PUBLISHED` predicate is collection membership, not redundant read-side semantic recertification, and must be preserved.

## No additional Relationship-specific applicability materialization

Do not introduce a table such as:

```text
relationship_resolution_applicability
    resolution_id
    applicable_template_id
```

That would duplicate information already represented by the stable ObjectTemplate ancestry closure and would introduce fan-out maintenance whenever a new descendant lineage is created.

Ownership should remain:

```text
ObjectTemplate.CREATE
    -> materializes ancestry rows for the new lineage

RelationshipResolution
    -> stores only stable endpoint lineage IDs

capability query
    -> joins the two
```

## Cache role

No dedicated capability cache is justified. The stable RelationshipDefinition topology cache may contain Resolution IDs and stable from/to lineage IDs, but it intentionally excludes mutable names/default state and cannot establish current PUBLISHED eligibility or target existence.

## Candidate conclusion

Keep the capability projection as a single authoritative PostgreSQL read, but replace the recursive stable-ancestry CTE with a join over `object_template_ancestry`. Preserve current PUBLISHED-membership, mutable names/defaults, pagination and missing-target semantics. No new Relationship-specific denormalization and no capability cache.
