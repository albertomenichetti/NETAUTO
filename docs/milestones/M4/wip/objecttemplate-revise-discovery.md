# ObjectTemplate.REVISE discovery — WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for `ObjectTemplate.REVISE`. This note is non-normative. Lock redesign remains deferred to the later global concurrency phase.

## AS-IS semantic shape

REVISE is complete replacement of the local declarations of one exact DRAFT version. It requires `expected_revision`, may rebind the exact parent version for non-root lineages, resolves property DataType pins/defaults, validates migration defaults, resolves component targets, validates effective-schema consistency and enforces historical evolution constraints.

The current implementation performs dependency resolution before lock acquisition and repeats the resolution under the stabilized lock plan. This duplication is part of the current lock-plan stabilization protocol and is not treated as removable in the first-phase audit.

## DRAFT loading

The current DRAFT exact version is mutable and therefore cannot be served from immutable worker cache.

AS-IS `ObjectTemplateStore.get_version()` loads:

- version header;
- local properties;
- local components;

with three separate statements.

A one-statement exact-version projection already exists for read paths. Candidate M4 direction: use an equivalent one-business-statement projection for loading the current DRAFT during REVISE.

## Avoid re-reading current declarations during persistence

After stabilization, the application already holds both:

- `current.properties` / `current.components`;
- `candidate.properties` / `candidate.components`.

AS-IS `replace_candidate()` re-queries current properties/components only to compute `declaration_delta(...)`.

Candidate direction: compute the declaration delta in memory from the already stabilized current candidate and pass the delta/persistable candidate to persistence. These two SELECTs are data-access redundancy, not a concurrency requirement.

## Immutable dependency semantics

The candidate DRAFT itself is not cacheable, but REVISE may reuse immutable knowledge of its dependencies:

- PUBLISHED/DEPRECATED DataTypeVersion semantic payload from the DataType immutable cache for migration-default validation;
- immutable ObjectTemplate parent effective schema from the ObjectTemplate immutable cache/materialization where applicable.

Current existence, default resolution and lifecycle admission remain PostgreSQL current truth.

## Historical declaration continuity

Normal evolution preserves historical semantic identity:

- property key: `(declaring_template_id, name)`;
- component-slot key: `(declaring_template_id, name)`.

Remove/re-add by the same declaring lineage cannot reset evolution rules.

AS-IS `_validate_candidate(..., history=True)` performs one historical query for each local candidate property and one for each local candidate component via latest immutable declaration lookup.

Candidate direction: replace this N+1 with set-based/bulk historical lookup, ideally one query for all property names and one for all component names (or one combined projection if cleanly representable).

Do not introduce a separate denormalized "latest semantic declaration" registry merely to accelerate rare model-plane editing. The normalized immutable version history remains adequate when queried set-wise.

## Component target widening and stable ancestry

Historical slot evolution allows target widening toward an ancestor and forbids narrowing/unrelated migration in normal evolution.

AS-IS `is_ancestor()` walks stable parent lineages one query at a time.

The proposed stable ObjectTemplate ancestry closure directly serves this rule:

```text
object_template_ancestry
    descendant_template_id
    ancestor_template_id
    depth
```

The check can become one PostgreSQL existence lookup or zero SQL when immutable ancestry is already in worker-local cache.

This is a concrete additional justification for stable lineage closure materialization.

## Inherited member collision

A child candidate may not override/hide an inherited property or component; properties and components share one effective member namespace.

This validation is exact-version-sensitive because the child pins an exact parent version. Stable lineage ancestry alone is therefore insufficient.

However, the proposed materialized immutable effective schema of the exact parent directly solves the need:

```text
InheritedNames = EffectiveSchema(parent_template_id, parent_version).member_names
LocalNames = candidate.properties.names U candidate.components.names
require InheritedNames ∩ LocalNames = empty
```

For a DRAFT child, the candidate effective schema can be built transiently as:

```text
immutable effective schema of exact parent
+
local DRAFT candidate declarations
```

This does not yet justify a separate exact-version ancestry closure.

## DML delta

Differential persistence is semantically appropriate: unchanged local declarations should not be rewritten.

AS-IS, however, executes individual DELETEs and INSERTs for each changed property/component and then updates the version header.

Candidate set-based/bulk persistence:

- one DELETE for changed/removed properties (`name IN (...)`) when needed;
- one DELETE for changed/removed components when needed;
- one bulk multi-row INSERT for changed/new properties when needed;
- one bulk multi-row INSERT for changed/new components when needed;
- one UPDATE of the exact version header/revision.

Thus DML cost should be bounded by a small constant number of statements rather than the number of changed members.

Position swaps remain compatible with delete-before-insert delta application.

As with CREATE, preserve PostgreSQL FK authority and review whether bulk DML can retain acceptable blocker/error diagnostics.

## Effective-schema materialization

REVISE keeps the exact version in DRAFT. Current preferred M4 direction remains:

- build/validate the effective candidate transiently;
- do not persist the long-lived effective-schema materialization for DRAFT;
- do not populate immutable ObjectTemplate version cache from REVISE.

Materialization/cache eligibility begins at PUBLISH.

## Working candidate flow

Conceptually, without redesigning locks yet:

```text
load current DRAFT efficiently
resolve current selectors/admission
reuse immutable dependency caches where possible
build candidate
stabilize current concurrency predicates
bulk-load historical continuity facts
validate component widening via stable ancestry
build effective candidate from immutable parent effective schema + local candidate
validate
compute local declaration delta in memory
set-based/bulk DML
commit
```

## Open items

- exact lock/UoW redesign and whether parts of semantic validation can move outside the write UoW;
- physical stable ancestry schema/cache representation;
- cold-load shape for immutable parent effective schema;
- bulk historical query design/index support;
- bulk DML failure diagnostics;
- whether any later operation independently justifies exact-version ancestry materialization.
