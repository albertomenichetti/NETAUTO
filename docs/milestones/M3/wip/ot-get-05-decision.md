# M3 — OT-GET-05 Consolidated Discovery Decision

**Status:** WIP / NON-NORMATIVE

**Route:** `GET /api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema`

**Application:** `ObjectTemplateService.get_effective_schema`

**Discovery status:** CONSOLIDATED

This satellite note records the consolidated OT-GET-05 decision while the main GET/read census remains the authoritative discovery register to be updated/normalized later.

## Current shape

The current read uses `coherent_read()` and composes the effective schema through multiple persistence reads:

```text
load requested exact ObjectTemplateVersion
    -> header
    -> local properties
    -> local components

then traverse exact parent pins level by level
    -> stable lineage read for current node
    -> exact parent version read
       -> header
       -> properties
       -> components
    -> repeat until root
```

The current path also re-certifies persisted semantic invariants during the GET, including:

```text
local declaration validity
inheritance acyclicity
parent exact-pair completeness
stable-lineage / exact-parent agreement
exact parent existence as an application semantic check
root validity
inherited member collision freedom
```

Some of those relationships are already structurally protected by the database, notably the exact parent pair and exact parent FK.

## Consolidated ownership decision

The GET must trust persisted semantic state.

Therefore the read path must remove semantic revalidation of already-persisted ObjectTemplate declarations and inheritance semantics. In particular, the GET path must not re-run:

```text
validate_local_declarations(...)
cycle certification
stable-lineage vs exact-parent comparison
root semantic certification
inherited-member collision certification
```

Mutation paths remain responsible for those semantic invariants, with database constraints/FKs responsible for structural invariants expressible at schema level.

The stable `object_templates` lineage is not required to compute an exact effective schema once exact parent pins are persisted. The read should follow the exact version chain directly.

## Target persistence shape

Materialize the complete exact inheritance chain and all local declarations required for the effective-schema projection in **one SQL statement**.

The preferred realization is a recursive CTE rooted at the requested exact version:

```sql
WITH RECURSIVE chain AS (
    SELECT
        v.template_id,
        v.version,
        v.parent_template_id,
        v.parent_version,
        0 AS depth
    FROM object_template_versions AS v
    WHERE v.template_id = :template_id
      AND v.version = :version

    UNION ALL

    SELECT
        parent.template_id,
        parent.version,
        parent.parent_template_id,
        parent.parent_version,
        child.depth + 1
    FROM chain AS child
    JOIN object_template_versions AS parent
      ON parent.template_id = child.parent_template_id
     AND parent.version = child.parent_version
)
...
```

The recursive step follows only persisted exact parent pins. It does not query stable lineages and does not re-certify inheritance semantics.

Above the recursive chain, use a typed `UNION ALL` projection rather than joining properties and components simultaneously, avoiding cartesian multiplication. Conceptually:

```text
row kind 0 -> existence marker for requested exact leaf
row kind 1 -> effective property source row
row kind 2 -> effective component source row
```

Each property/component row carries at least:

```text
depth
declaring_template_id
position
local declaration fields
```

Depth is assigned leaf-first (`leaf = 0`, parent = 1, ...), so `depth DESC` produces root-to-leaf order for trusted projection.

The existence marker preserves exact path semantics even when the effective schema contains zero members:

```text
no rows
    -> requested exact ObjectTemplateVersion absent
    -> 404

marker only
    -> exact version exists, effective schema empty

marker + declaration rows
    -> exact version exists, normal effective schema projection
```

## Target application/domain shape

The GET path should not call the validating mutation-oriented `resolve_effective_schema()` implementation if that function continues to certify semantic invariants.

Instead use a trusted read projector that only builds:

```text
EffectiveSchema(
    template_id,
    version,
    properties,
    components,
)
```

from already-persisted root-to-leaf declaration rows, preserving declaration order and `declaring_template_id`.

Mutation workflows may continue to use validation-aware effective-schema resolution.

## Consolidated decision

```text
persisted-state semantic revalidation   REMOVE
stable-lineage reads                    REMOVE
current coherent_read()                 JUSTIFIED by current fragmented multi-statement shape
target persistence statements          1
target coherent_read()                  REMOVE
projection strategy                     recursive exact-chain CTE + typed UNION ALL
cartesian property/component joins      AVOID
404 exact-version semantics             PRESERVE
empty effective-schema semantics        PRESERVE
```

The exact SQLAlchemy construction is an implementation detail; the consolidated discovery requirement is one statement, exact-pin traversal, trusted projection, and no read-side semantic certification.
