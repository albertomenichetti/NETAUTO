# RelationshipDefinitionVersion GET exact — M4 discovery

Status: WIP / NON-NORMATIVE

## Scope

Audit the current exact RelationshipDefinitionVersion GET read path for M4 data-access, denormalization, and cache opportunities. Lock/concurrency redesign is out of scope for this phase.

## Current AS-IS

The application uses `RelationshipDefinitionVersionStore.project_version(definition_id, version)`, which performs one authoritative statement and preserves the distinction between:

- missing RelationshipDefinition lineage;
- existing RelationshipDefinition with missing exact version;
- existing exact version.

When present, the projection returns the complete exact version header and ordered property declaration set.

## Lifecycle/cache split

### DRAFT

A DRAFT exact version remains mutable in both revision and property declarations. It must therefore be read from PostgreSQL and is not eligible for immutable worker cache storage.

The current one-statement `project_version()` is already an appropriate baseline for DRAFT and cold reads.

### PUBLISHED / DEPRECATED

PUBLISHED and DEPRECATED exact versions have immutable semantic property snapshots. Unlike ObjectTemplate, the exact RelationshipDefinitionVersion property set is already the complete schema; there is no local-vs-effective split.

A candidate runtime cache therefore naturally contains the same immutable declarations needed by the public exact-version DTO:

```text
ImmutableRelationshipDefinitionVersionCache[(definition_id, version)]
    properties, ordered:
        name
        position
        datatype_id
        datatype_version
        value_mode

    compiled runtime structures / validator linkage
```

The cache must not be authoritative for current existence or lifecycle status.

## Candidate read paths

### Cache miss / DRAFT

Keep the current one-statement `project_version()` path.

If the returned exact version is PUBLISHED or DEPRECATED, the immutable declarations may opportunistically contribute to cache population.

### Cache hit for immutable exact version

Use a lightweight authoritative PostgreSQL projection for:

- RelationshipDefinition current existence;
- exact version current existence;
- revision;
- current status.

Then reconstruct the DTO from:

```text
current header from PostgreSQL
+
immutable property declarations from worker cache
```

This preserves current `PUBLISHED -> DEPRECATED` visibility and exact deletion semantics while avoiding rereading `relationship_definition_properties`.

The lightweight projection must preserve the existing distinction between missing Definition and missing exact version.

## Cache warming constraint

Do not add DataType queries solely to warm the RelationshipDefinitionVersion runtime cache during a public GET.

The compiled runtime cache also needs semantic DataType information. If the required immutable DataType entries are already locally available, the cache entry can be completed opportunistically; otherwise the first true data-plane consumer may perform the cold compilation.

PUBLISH remains the ideal warming boundary because it already resolves and certifies the direct DataType dependencies.

## Candidate M4 finding

- Keep `project_version()` as the cold/DRAFT one-statement authoritative read.
- For PUBLISHED/DEPRECATED cache hits, use a lightweight current-header projection plus immutable cached declarations.
- Cache presence never proves current existence or current lifecycle state.
- Do not execute extra DataType reads solely for cache warming.
- No new relational denormalization is required for this read.
