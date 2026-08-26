# ObjectTemplate GET exact version discovery

Status: WIP / NON-NORMATIVE

## Scope

Operation: public GET of one exact ObjectTemplateVersion.

This note records M4 discovery findings only. It does not authorize implementation.

## Current behavior

The public application read uses `ObjectTemplateStore.project_version(template_id, version)`, which projects in one authoritative SQL statement:

- exact version header;
- local properties;
- local components.

The public DTO is the local exact snapshot, not the effective inherited schema.

Current data path is therefore already one PostgreSQL round-trip.

## M4 lifecycle split

### DRAFT

A DRAFT exact version is mutable and revisioned.

Consequences:

- PostgreSQL is the current authority;
- DRAFT payload is not worker-cacheable as immutable semantics;
- `project_version()` remains an appropriate one-statement baseline.

### PUBLISHED / DEPRECATED

The exact parent pin and local declarations are immutable semantic state after publication. They are therefore semantically cacheable.

However, the M4 ObjectTemplate cache should remain runtime-oriented rather than becoming a persistence DTO cache solely for this read operation.

Candidate runtime cache shape remains centered on the immutable effective schema and compiled runtime structures. If that cache naturally contains enough information to reconstruct the local declarations (for example through `declaring_template_id` on effective members), a cache hit may be reused opportunistically.

## Current-truth boundary

Cache presence must not prove current existence or current lifecycle status.

Therefore a cache-assisted public GET would still require a lightweight PostgreSQL read sufficient to establish current exact-version existence and current fields required by the response, such as status/revision and exact parent identity.

A possible cache-hit shape is:

1. runtime immutable cache hit for `(template_id, version)`;
2. one lightweight PostgreSQL exact-header/current-existence projection;
3. reconstruct local declarations from already-cached immutable information only if the runtime cache naturally supports it;
4. return response.

This must not increase the number of PostgreSQL round-trips relative to the current one-statement baseline.

## Cache-miss rule

On cache miss, continue to use the complete one-statement `project_version()` projection.

Do not add an additional effective-schema read only to warm the runtime cache.

In particular, avoid:

```text
GET exact cache miss
    -> project_version
    -> second effective-schema query only for cache warming
```

## Decision direction

- Keep one SQL as the baseline for DRAFT and cache-miss reads.
- Allow cache reuse for PUBLISHED/DEPRECATED only when the existing runtime cache naturally provides the necessary immutable payload.
- Do not introduce a dedicated GET-exact cache.
- Do not reshape the runtime cache solely for this model-plane read.
- Do not add extra reads for cache warming.
- Cache never substitutes for current existence/lifecycle truth.

## Deferred questions

Exact cache shape and current-state admission details remain implementation/design work for later M4 phases.
