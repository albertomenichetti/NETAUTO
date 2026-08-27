# M4 WIP — Object SCHEMA_CHANGE migration-plan amortization

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note records an important workload property of:

```http
POST /api/v1/core/objects/{object_id}/schema
```

under the M4 immutable `MigrationPlanCache` design.

## Migration-plan identity

The semantic migration plan is keyed only by the exact source/target ObjectTemplateVersion pair inside one stable template lineage:

```text
MigrationPlanCache[
    (template_id, source_version, target_version)
]
```

It does not depend on one particular Object instance.

The Object contributes only its current mutable aggregate state:

```text
properties
current attached ownership edges
canonical_name / intrinsic state used by lifecycle and fingerprinting
```

The difficult immutable semantic work is shared across all Objects performing the same exact migration:

```text
compare SOURCE vs TARGET effective schemas
classify property evolution
link exact DataTypeVersion semantics / validators
classify component evolution
resolve stable ancestry compatibility
compile reusable property/component migration rules
```

## Expected population-migration locality

A normal operational pattern is expected to be:

```text
many Objects currently bound to OTV x
+
operator introduces / selects OTV y
+
Objects are progressively migrated x -> y
```

Therefore the sequence:

```text
Object A: (T, x -> y)
Object B: (T, x -> y)
Object C: (T, x -> y)
...
```

has strong temporal locality on the same `MigrationPlanCache` key.

This is not required for correctness, but it is a first-class performance property of the design.

## First Object on a cold worker

For the first Object requiring one previously unseen migration pair on a completely cold worker, the current TO-BE full-miss shape is:

```text
1. Object binding lookup

2. bulk load SOURCE + TARGET exact effective closures
3. bulk load all missing exact DTV semantics required by SOURCE union TARGET
4. bulk load required stable ObjectTemplate ancestry

   -> compile MigrationPlan(T, x, y)
   -> cache MigrationPlan READY

5. complete Object aggregate read

6. UoW Q1 target OTV @ SHARE
7. UoW Q2 Object @ NO KEY UPDATE
8. UoW Q3 protected aggregate read / fingerprint compare
9. UoW Q4 Object UPDATE + lifecycle INSERT
```

Thus the current full-cold successful first-attempt target is:

```text
9 PostgreSQL business statements
```

excluding transaction-control commands.

The three semantic cold-fill statements are bounded bulk operations. Their round-trip count does not grow with inheritance depth, number of effective properties, or number of distinct DataType pins.

## Subsequent Objects for the same migration pair

Once:

```text
MigrationPlanCache[(T, x, y)] = READY
```

subsequent Objects on the same worker do not need to:

```text
reload SOURCE/TARGET closures
reload exact DTV semantics for plan construction
reload stable ancestry for plan construction
compare SOURCE vs TARGET again
compile property migration rules again
compile component migration rules again
```

They immediately reuse the fully resolved plan.

Their successful first-attempt path is therefore the normal warm path:

```text
1. Object binding lookup
2. complete Object aggregate read / preparation
3. Q1 target OTV @ SHARE
4. Q2 Object @ NO KEY UPDATE
5. Q3 protected aggregate read / fingerprint compare
6. Q4 mutation + lifecycle
```

or:

```text
6 PostgreSQL business statements per Object
+
application of an already-compiled MigrationPlan
```

## Amortized population cost

For `N` Objects migrated on one worker from the same `(T, x)` to the same `(T, y)`, assuming a fully cold worker for the first Object and no optimistic retry:

```text
first Object       = 9 statements
remaining N - 1    = 6 statements each

total              = 9 + 6(N - 1)
                   = 6N + 3

average per Object = 6 + 3/N
```

Example:

```text
N = 100

total = 603 statements
average = 6.03 statements/Object
```

The semantic discovery/materialization cost therefore becomes negligible as the migrated population grows.

## Correct granularity of cold cost

The important architectural interpretation is:

```text
cold semantic-plan cost
    is primarily per
    (worker, template_id, source_version, target_version)

not per Object
```

The per-Object runtime work remains focused on current mutable state, optimistic preparation, protected fingerprint verification, and the final atomic mutation.

## Worker-local scope

M4 currently assumes worker/process-local immutable caches rather than a distributed cache.

Therefore in a multi-worker deployment the same migration pair may incur its cold semantic-fill/compile cost once on each worker that first encounters it:

```text
worker A: first x -> y -> cold, then warm
worker B: first x -> y -> cold, then warm
worker C: first x -> y -> cold, then warm
```

This does not alter correctness and does not require distributed invalidation because the cached migration plan and its exact semantic inputs are immutable for their keys.

## Design consequence

`MigrationPlanCache` should be treated as more than a micro-optimization of a single Object command.

It deliberately exploits the natural population-migration workload:

```text
certify/materialize immutable model knowledge once
compile one reusable source->target migration plan
apply that plan to many mutable Object aggregates
```

This is a direct expression of the M4 model-plane/data-plane split:

```text
rare / shared semantic work
    -> amortized

frequent per-Object work
    -> simple bounded data-plane operations
```

## Frozen decision

The M4 TO-BE design must preserve the following property:

```text
MigrationPlan semantic work is reusable across all Objects sharing
(template_id, source_version, target_version).

A full cold semantic fill/compile is paid at most once per worker cache residency for that migration pair.

Subsequent Objects consume the already-resolved MigrationPlan and follow the six-statement warm path, subject only to normal eviction/process restart or a different migration pair.
```
