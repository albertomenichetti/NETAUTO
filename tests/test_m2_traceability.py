"""Singular machine-checkable M2 census, evidence and concurrency registry."""

import ast
import inspect
import subprocess
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import cast

from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import RelationshipService
from netauto.cli.registry import BUSINESS_OPERATION_SET, COMMAND_REGISTRY
from netauto.persistence.locking import AdvisoryGate, RowLockMode
from tests.test_m1_traceability import PGTEST_SCENARIOS
from tests.test_m2_s00_traceability import (
    DELIVERED_MUTATION_PLANS,
    PLAN_EVIDENCE_TARGETS,
    Mutation,
)

M2_OUTCOMES = frozenset(f"M2-OUT-{number:02d}" for number in range(1, 17))
M2_ACCEPTANCE_CRITERIA = frozenset(f"M2-AC-{number:02d}" for number in range(1, 33))
M2_EVIDENCE_BUNDLES = frozenset(f"M2-VER-{number:02d}" for number in range(1, 33))
M2_CONCURRENCY_SCENARIOS = frozenset(
    {
        *(f"ROW-{number:02d}" for number in range(1, 31)),
        *(f"ARB-{number:02d}" for number in range(1, 9)),
        *(f"REF-{number:02d}" for number in range(1, 12)),
        *(f"GATE-{number:02d}" for number in range(1, 8)),
        *(f"SNAP-{number:02d}" for number in range(1, 6)),
        *(f"ATOMIC-{number:02d}" for number in range(1, 8)),
        *(f"PAR-{number:02d}" for number in range(1, 10)),
        *(f"PLAN-{number:02d}" for number in range(1, 7)),
    }
)

M2_OUTCOME_TO_ACCEPTANCE = {
    "M2-OUT-01": frozenset(f"M2-AC-{number:02d}" for number in range(1, 6)),
    "M2-OUT-02": frozenset(
        {"M2-AC-02", "M2-AC-03", "M2-AC-04", "M2-AC-15", "M2-AC-16"}
    ),
    "M2-OUT-03": frozenset({"M2-AC-06", "M2-AC-08", "M2-AC-09", "M2-AC-11"}),
    "M2-OUT-04": frozenset(
        {
            *(f"M2-AC-{number:02d}" for number in range(6, 11)),
            "M2-AC-17",
            "M2-AC-18",
        }
    ),
    "M2-OUT-05": frozenset(
        {
            "M2-AC-06",
            "M2-AC-07",
            "M2-AC-09",
            "M2-AC-10",
            "M2-AC-13",
            "M2-AC-31",
        }
    ),
    "M2-OUT-06": frozenset({"M2-AC-05", "M2-AC-11", "M2-AC-12", "M2-AC-13"}),
    "M2-OUT-07": frozenset(f"M2-AC-{number:02d}" for number in range(8, 15))
    | {"M2-AC-19"},
    "M2-OUT-08": frozenset(f"M2-AC-{number:02d}" for number in range(15, 20)),
    "M2-OUT-09": frozenset({"M2-AC-20", "M2-AC-21"}),
    "M2-OUT-10": frozenset({"M2-AC-22"}),
    "M2-OUT-11": frozenset({"M2-AC-23"}),
    "M2-OUT-12": frozenset(f"M2-AC-{number:02d}" for number in range(25, 29)),
    "M2-OUT-13": frozenset({"M2-AC-24"}),
    "M2-OUT-14": frozenset({"M2-AC-29"}),
    "M2-OUT-15": frozenset({"M2-AC-30"}),
    "M2-OUT-16": frozenset({"M2-AC-31", "M2-AC-32"}),
}
M2_ACCEPTANCE_TO_EVIDENCE = {
    f"M2-AC-{number:02d}": f"M2-VER-{number:02d}" for number in range(1, 33)
}

M2_ARCHITECTURE_OWNERS = frozenset(
    f"docs/milestones/M2/architecture/{name}.md"
    for name in (
        "relationship",
        "api",
        "persistence",
        "concurrency-matrix",
        "concurrency",
        "health",
        "cli",
        "runtime-deployment",
        "verification",
    )
)
_RELATIONSHIP_OWNER = "docs/milestones/M2/architecture/relationship.md"
_API_OWNER = "docs/milestones/M2/architecture/api.md"
_PERSISTENCE_OWNER = "docs/milestones/M2/architecture/persistence.md"
_MATRIX_OWNER = "docs/milestones/M2/architecture/concurrency-matrix.md"
_CONCURRENCY_OWNER = "docs/milestones/M2/architecture/concurrency.md"
_HEALTH_OWNER = "docs/milestones/M2/architecture/health.md"
_CLI_OWNER = "docs/milestones/M2/architecture/cli.md"
_RUNTIME_OWNER = "docs/milestones/M2/architecture/runtime-deployment.md"
_VERIFICATION_OWNER = "docs/milestones/M2/architecture/verification.md"

M2_OUTCOME_TO_ARCHITECTURE_OWNERS: dict[str, frozenset[str]] = {
    "M2-OUT-01": frozenset({_RELATIONSHIP_OWNER, _API_OWNER, _PERSISTENCE_OWNER}),
    "M2-OUT-02": frozenset({_RELATIONSHIP_OWNER, _MATRIX_OWNER, _CONCURRENCY_OWNER}),
    "M2-OUT-03": frozenset({_RELATIONSHIP_OWNER, _PERSISTENCE_OWNER, _API_OWNER}),
    "M2-OUT-04": frozenset(
        {_RELATIONSHIP_OWNER, _API_OWNER, _MATRIX_OWNER, _CONCURRENCY_OWNER}
    ),
    "M2-OUT-05": frozenset({_RELATIONSHIP_OWNER, _PERSISTENCE_OWNER}),
    "M2-OUT-06": frozenset({_API_OWNER, _PERSISTENCE_OWNER}),
    "M2-OUT-07": frozenset({_RELATIONSHIP_OWNER, _API_OWNER, _PERSISTENCE_OWNER}),
    "M2-OUT-08": frozenset({_MATRIX_OWNER, _CONCURRENCY_OWNER, _PERSISTENCE_OWNER}),
    "M2-OUT-09": frozenset({_PERSISTENCE_OWNER}),
    "M2-OUT-10": frozenset({_RUNTIME_OWNER, _PERSISTENCE_OWNER}),
    "M2-OUT-11": frozenset({_HEALTH_OWNER, _API_OWNER}),
    "M2-OUT-12": frozenset({_CLI_OWNER, _API_OWNER}),
    "M2-OUT-13": frozenset({_RUNTIME_OWNER, _CLI_OWNER}),
    "M2-OUT-14": frozenset({_RUNTIME_OWNER}),
    "M2-OUT-15": frozenset({_RUNTIME_OWNER, _CLI_OWNER}),
    "M2-OUT-16": M2_ARCHITECTURE_OWNERS,
}
M2_ARCHITECTURE_OWNER_TO_OUTCOMES: dict[str, frozenset[str]] = {
    owner: frozenset(
        outcome
        for outcome, owners in M2_OUTCOME_TO_ARCHITECTURE_OWNERS.items()
        if owner in owners
    )
    for owner in M2_ARCHITECTURE_OWNERS
}

M2_AUTHORITY_COMPOSITION: dict[str, frozenset[str]] = {
    "delivered_as_is": frozenset(
        f"docs/architecture/{name}.md"
        for name in (
            "README",
            "datatype",
            "objecttemplate",
            "object",
            "relationship",
            "persistence",
            "concurrency-matrix",
            "concurrency",
            "api",
            "verification",
            "verification-concurrency-registry",
        )
    ),
    "m2_contract": frozenset({"docs/milestones/M2/contract.md"}),
    "m2_architecture": M2_ARCHITECTURE_OWNERS
    | frozenset(
        {
            "docs/milestones/M2/architecture/README.md",
            "docs/milestones/M2/architecture/provenance.md",
        }
    ),
    "technology": frozenset({"docs/general/technology_baseline.md"}),
    "operations": frozenset(
        {"docs/milestones/M2/steps.md", "docs/milestones/M2/status.md"}
    ),
    "non_authoritative_history": frozenset({"docs/milestones/M2/wip"}),
}

M2_PRIMARY_BUNDLE_OWNER: dict[str, str] = {
    **{
        f"M2-VER-{number:02d}": "M2-S01" for number in (1, 2, 3, 4, 5, 6, 7, 10, 20, 21)
    },
    **{f"M2-VER-{number:02d}": "M2-S02" for number in (8, 9, 11, 12, 13, 14)},
    **{f"M2-VER-{number:02d}": "M2-S03" for number in range(15, 20)},
    **{f"M2-VER-{number:02d}": "M2-S04" for number in (22, 23)},
    "M2-VER-27": "M2-S05",
    **{f"M2-VER-{number:02d}": "M2-S06" for number in (25, 26, 28)},
    **{f"M2-VER-{number:02d}": "M2-S07" for number in (24, 29, 30)},
    **{f"M2-VER-{number:02d}": "M2-S08" for number in (31, 32)},
}


@dataclass(frozen=True, slots=True)
class CapabilityTrace:
    objectives: frozenset[str]
    outcomes: frozenset[str]
    acceptance: frozenset[str]
    evidence: frozenset[str]
    owners: frozenset[str]


M2_CAPABILITY_PORTFOLIO: dict[str, frozenset[str]] = {
    "in_scope": frozenset(
        {
            "Versioned Relationship property model",
            "Core Health API",
            "NETAUTO CLI",
            "Runtime configuration and production deployment",
        }
    ),
    "cross_cutting_foundation": frozenset({"First durable Alembic kernel baseline"}),
    "explicitly_outside_m2": frozenset({"Logging operational review / introduction"}),
}


def _capability_trace(
    *,
    objectives: tuple[str, ...],
    outcome_numbers: tuple[int, ...],
    acceptance_numbers: tuple[int, ...],
    owners: frozenset[str],
) -> CapabilityTrace:
    acceptance = frozenset(f"M2-AC-{number:02d}" for number in acceptance_numbers)
    return CapabilityTrace(
        objectives=frozenset(objectives),
        outcomes=frozenset(f"M2-OUT-{number:02d}" for number in outcome_numbers),
        acceptance=acceptance,
        evidence=frozenset(M2_ACCEPTANCE_TO_EVIDENCE[item] for item in acceptance),
        owners=owners,
    )


_CROSS_CUTTING_OBJECTIVE = "Cross-cutting objective clause"
M2_CAPABILITY_TRACE: dict[str, CapabilityTrace] = {
    "Versioned Relationship property model": _capability_trace(
        objectives=(
            "Objective 1 — Versioned Relationship state",
            "Objective 2 — Safe Relationship evolution",
            "Objective 3 — Preserve the delivered Relationship model",
            _CROSS_CUTTING_OBJECTIVE,
        ),
        outcome_numbers=(*tuple(range(1, 9)), 16),
        acceptance_numbers=(*tuple(range(1, 20)), 31, 32),
        owners=frozenset(
            {
                _RELATIONSHIP_OWNER,
                _API_OWNER,
                _PERSISTENCE_OWNER,
                _MATRIX_OWNER,
                _CONCURRENCY_OWNER,
                _VERIFICATION_OWNER,
            }
        ),
    ),
    "Core Health API": _capability_trace(
        objectives=(
            "Objective 5 — Establish a defined operable runtime",
            _CROSS_CUTTING_OBJECTIVE,
        ),
        outcome_numbers=(11, 15, 16),
        acceptance_numbers=(23, 30, 31, 32),
        owners=frozenset(
            {_HEALTH_OWNER, _API_OWNER, _RUNTIME_OWNER, _VERIFICATION_OWNER}
        ),
    ),
    "NETAUTO CLI": _capability_trace(
        objectives=(
            "Objective 6 — Provide an official public-API client",
            _CROSS_CUTTING_OBJECTIVE,
        ),
        outcome_numbers=(12, 13, 15, 16),
        acceptance_numbers=(24, 25, 26, 27, 28, 30, 31, 32),
        owners=frozenset({_CLI_OWNER, _API_OWNER, _RUNTIME_OWNER, _VERIFICATION_OWNER}),
    ),
    "Runtime configuration and production deployment": _capability_trace(
        objectives=(
            "Objective 5 — Establish a defined operable runtime",
            _CROSS_CUTTING_OBJECTIVE,
        ),
        outcome_numbers=(9, 10, 11, 13, 14, 15, 16),
        acceptance_numbers=(20, 21, 22, 23, 24, 29, 30, 31, 32),
        owners=frozenset(
            {_RUNTIME_OWNER, _PERSISTENCE_OWNER, _HEALTH_OWNER, _VERIFICATION_OWNER}
        ),
    ),
    "First durable Alembic kernel baseline": _capability_trace(
        objectives=(
            "Objective 4 — Establish the first durable kernel baseline",
            _CROSS_CUTTING_OBJECTIVE,
        ),
        outcome_numbers=(9, 10, 13, 16),
        acceptance_numbers=(20, 21, 22, 24, 31, 32),
        owners=frozenset({_PERSISTENCE_OWNER, _RUNTIME_OWNER, _VERIFICATION_OWNER}),
    ),
}

PUBLIC_HTTP_OPERATIONS = BUSINESS_OPERATION_SET | frozenset({("GET", "/health/core")})
CLI_REMOTE_OPERATION_COVERAGE = frozenset(
    (spec.method, spec.path_template) for spec in COMMAND_REGISTRY.values()
)
HEALTH_LOCAL_COMMAND_COVERAGE = frozenset({"/connect", "/status"})

M2_AS_IS_GUARANTEE_TO_TARGETS: dict[str, frozenset[str]] = {
    "stable RelationshipDefinition topology and symmetry": frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_non_symmetric_derivation_is_order_independent_and_reciprocal",
            "tests/test_relationshipdefinition_domain.py::"
            "test_symmetric_derivation_has_frozen_same_and_different_template_shapes",
        }
    ),
    "RelationshipResolution identity, membership and endpoint lineages": frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_complete_rename_preserves_ids_endpoints_and_membership"
        }
    ),
    "mutable Resolution name as non-key metadata": frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_complete_rename_preserves_ids_endpoints_and_membership",
            "tests/test_schema_metadata.py::"
            "test_relationship_resolution_name_is_not_part_of_a_unique_key",
        }
    ),
    (
        "Definition equivalence and cross-Definition Resolution conflict semantics"
    ): frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_cross_definition_conflict_requires_name_and_both_space_overlaps",
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_strict_shapes_and_finite_failures",
        }
    ),
    "Relationship factual identity": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock"
        }
    ),
    "symmetric/non-symmetric factual uniqueness": frozenset(
        {
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_05_reciprocal_create_uses_pk_and_rejects_loser",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_05_symmetric_inverse_and_overlap_create_reject_loser",
        }
    ),
    "self-loop support": frozenset(
        {
            "tests/test_relationship_domain.py::"
            "test_symmetric_same_template_distinct_pair_and_self_loop",
            "tests/test_relationship_api.py::"
            "test_strict_operands_missing_resources_incompatibility_and_self_loop",
        }
    ),
    "exact runtime-view identity": frozenset(
        {
            "tests/test_relationship_domain.py::"
            "test_non_symmetric_closure_preserves_selected_factual_orientation"
        }
    ),
    "complete deterministic runtime-resolution closure": frozenset(
        {
            "tests/test_relationship_domain.py::"
            "test_persisted_incomplete_closure_is_rejected",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_create_event_failure_rolls_back_header_and_complete_closure",
        }
    ),
    "Object stable-lineage endpoint admission": frozenset(
        {
            "tests/test_relationship_domain.py::"
            "test_endpoint_admission_uses_stable_lineage_and_reports_operand"
        }
    ),
    "Object and RelationshipDefinition delete blockers": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_relationshipdefinition_api.py::"
            "test_definition_references_block_lineage_and_factual_rows_block_delete",
        }
    ),
    "Object-relative semantic-view deduplication": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_m2_s02_all_transition_families_use_distinct_semantic_fanout"
        }
    ),
    "/api/v1/core business namespace": frozenset(
        {"tests/test_object_scope.py::test_s08_public_route_and_error_catalog_closure"}
    ),
    "strict request bodies": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_strict_shapes_and_finite_failures",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
        }
    ),
    "failure-class boundary": frozenset(
        {"tests/test_object_scope.py::test_s08_public_route_and_error_catalog_closure"}
    ),
    "bounded error details and no SQL/internal leakage": frozenset(
        {
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_ot_property_fk_is_bounded",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_rdv_property_fk_is_bounded",
        }
    ),
    "opaque keyset pagination": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_object_relative_keyset_cursor_and_filter_identity",
            "tests/test_relationshipdefinition_api.py::"
            "test_definition_list_uses_id_keyset_cursor_and_complete_items",
        }
    ),
    "single-request coherent reads": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_relationship_snapshot_cut_commits_between_physical_reads"
        }
    ),
}

M2_DELTA_ALLOWLIST = frozenset(
    {
        "RelationshipDefinition CREATE includes v1 DRAFT",
        "capability requires one PUBLISHED RDV",
        "Relationship CREATE request/projection adds exact pin and properties",
        "duplicate Relationship CREATE becomes relationship_fact_conflict",
        "missing Relationship DELETE becomes resource_not_found",
        "Relationship lifecycle adds before/after state and new change kinds",
        "startup requires exact shipped Alembic revision",
        "one fresh durable root baseline replaces disposable development history",
        "new Health, CLI, release and Linux-runtime surfaces",
    }
)
M2_PUBLIC_WIRE_DELTA_ALLOWLIST = frozenset(
    {
        "RelationshipDefinition.CREATE response becomes {relationship_definition, "
        "version}; initial version is v1 DRAFT revision 1; optional initial "
        "properties schema added",
        "RelationshipDefinition stable DTO adds default_version",
        "RelationshipDefinitionVersion adds nested command/read routes and DTOs",
        "Relationship capability item adds default_version and is omitted without a "
        "PUBLISHED RDV",
        "Relationship.CREATE body adds optional relationship_definition_version and "
        "properties",
        "Relationship.CREATE duplicate returns 409 relationship_fact_conflict "
        "instead of successful convergence",
        "Relationship DTOs add relationship_definition_version and properties",
        "Relationship.DATA_CHANGE and SCHEMA_CHANGE add routes and request/response "
        "DTOs",
        "Relationship.DELETE absent target returns 404 instead of idempotent 204",
        "Relationship lifecycle adds before/after state to CREATED/DELETED and "
        "DATA_CHANGE/SCHEMA_CHANGE kinds",
        "GET /health/core adds one operational route",
    }
)
M2_DELIVERED_SCENARIO_DELTA_ALLOWLIST: dict[str, str] = {
    "ARB-05": "loser becomes relationship_fact_conflict with no loser mutation/event",
    "ARB-06": "same-ID delete waiter becomes resource_not_found / HTTP 404",
    "ARB-07": (
        "winner disappearance restarts and current winner conflicts, never converges "
        "successfully"
    ),
    "SNAP-01": (
        "Definition/Resolution rename variants add DATA_CHANGE and SCHEMA_CHANGE"
    ),
    "SNAP-02": "Object rename variants add DATA_CHANGE and SCHEMA_CHANGE",
    "ATOMIC-02": (
        "collision rollback keeps atomicity and classifies loser as "
        "relationship_fact_conflict"
    ),
    "ATOMIC-03": (
        "delete rollback keeps atomicity and successful waiter semantics become 204/404"
    ),
}
M2_SCHEMA_RUNTIME_DELTA_ALLOWLIST = frozenset(
    {
        "13 delivered tables become the exact 15-table M2 schema",
        "RelationshipDefinitionVersion and property declarations add exact schema "
        "state",
        "Relationship exact pin, canonical properties, runtime closure and lifecycle "
        "snapshots are persisted",
        "one root/base/head 0001_m2_kernel replaces disposable development revisions",
        "startup exact-revision guard precedes serving and never migrates",
        "Health, CLI and installed-release runtime surfaces are additive",
    }
)

M2_NEGATIVE_SURFACE_CONTRACT: dict[str, frozenset[str]] = {
    "relationship_model": frozenset(
        {
            "versioned Relationship topology or Resolution membership",
            "required Relationship properties",
            "nullable present Relationship values",
            "Relationship property create defaults or migration defaults",
            "normal LIST -> SCALAR narrowing",
            "caller remediation during SCHEMA_CHANGE",
            "automatic factual schema migration",
            "floating binding to default/latest/highest",
            "property- or version-based multi-edge factual identity",
            "runtime property EAV",
            "property-value search API",
            "effective or inherited Relationship schema",
            "standalone property-declaration CRUD",
            "standalone RelationshipResolution CRUD",
        }
    ),
    "lifecycle_history": frozenset(
        {
            "a separate Relationship timeline",
            "public event-set or transition aggregate",
            "event_set_id or transition_id",
            "a compliance-grade immutable ledger",
            "event sourcing or replay as current-state authority",
            "temporal current-state reconstruction",
            "retention or archive policy",
            "snapshot property search",
            "live history foreign keys",
            "retroactive historical metadata renaming",
        }
    ),
    "api_protocol": frozenset(
        {
            "a new business API version",
            "generic query or sorting DSL",
            "offset/page-number pagination",
            "automatic total counts",
            "bulk or batch mutation protocol",
            "generic PATCH semantics",
            "WebSocket, SSE or CDC subscription",
            "generic idempotency-key framework",
            "general ETag / If-Match protocol",
            "cross-request database snapshot tokens",
            "dynamic semantic extension through OpenAPI",
        }
    ),
    "security_network": frozenset(
        {
            "native authentication or authorization",
            "rate limiting or anti-abuse policy",
            "native server certificate management",
            "certificate rotation or reload",
            "mTLS or client certificates",
            "certificate pinning or TOFU",
            "CLI insecure TLS bypass",
            "reverse-proxy or firewall automation",
            "VPN or load-balancer configuration",
            "a separate Health listener",
        }
    ),
    "deployment_platform": frozenset(
        {
            "Docker or Kubernetes assets",
            "systemd unit or custom process manager",
            "start-at-boot or automatic restart",
            "service discovery, clustering or high availability",
            "multi-region operation",
            "rolling, blue/green, canary or zero-downtime upgrade",
            "application/schema rollback procedure",
            "artifact registry or transfer automation",
            "CI/CD deployment pipeline",
            "automatic installation or upgrade",
        }
    ),
    "data_protection": frozenset(
        {
            "backup or restore automation",
            "point-in-time recovery procedure",
            "PostgreSQL replica management",
            "data-retention policy",
            "disaster-recovery orchestration",
            "business-continuity SLA",
        }
    ),
    "observability": frozenset(
        {
            "logging redesign or structured logging contract",
            "correlation/request identifiers",
            "distributed tracing",
            "metrics endpoint or Prometheus integration",
            "dashboards or alerting",
            "central log shipping or rotation",
            "compliance audit logs",
        }
    ),
    "cli": frozenset(
        {
            "direct application-service or database access",
            "implicit/default server connection",
            "automatic instance discovery",
            "named persistent connection profiles",
            "mandatory persistence of endpoint or output mode",
            "credential storage",
            "dynamic OpenAPI command generation",
            "CLI plugin framework",
            "custom nested value DSL",
            "domain identities invented for convenience",
            "hidden post-mutation GET",
            "a cross-release compatibility protocol",
            "a granular exit-code taxonomy",
            "a full-screen TUI, macro language or offline mode",
            "persistent history across CLI process restarts",
        }
    ),
    "health": frozenset(
        {
            "generic GET /health aggregation",
            "dynamic health registry or plugin health framework",
            "health dependency graph",
            "warning/degraded/unknown state model",
            "metrics or extended diagnostics payload",
            "schema-revision validation inside Health",
            "automatic remediation",
            "readiness checks for future unincluded capabilities",
            "PostgreSQL internal diagnostics",
        }
    ),
    "alembic": frozenset(
        {
            "M1-to-M2 in-place data migration",
            "preservation or stamping of pre-baseline development databases",
            "dual-schema read/write compatibility",
            "online backfill or expand/contract rollout",
            "automatic migration at startup",
            "conditional downgrade to M1",
            "data-preserving head-to-base downgrade",
            "multiple Alembic heads",
        }
    ),
    "performance_availability": frozenset(
        {
            "quantitative throughput, latency, maximum-dataset, horizontal-scaling, "
            "benchmark, availability or zero-lock DDL SLA"
        }
    ),
    "verification_public": frozenset(
        {
            "generic PUT endpoints",
            "action DSL",
            "runtime Relationship-resolution CRUD",
            "schema migration endpoint",
            "auth/login/logout/token/account/role routes",
            "401/403 native contract",
            "JSON Schema projection",
        }
    ),
    "verification_schema": frozenset(
        {
            "Relationship property-value rows",
            "Relationship effective-schema cache",
            "compiled generic schema",
            "reverse-dependency materialization",
            "surrogate RDV/declaration/runtime-resolution IDs",
            "event-set grouping identity",
            "GIN on Object/Relationship properties",
            "GIN/expression lifecycle snapshot indexes",
            "standalone default_version indexes",
            "duplicate PUBLISHED-only indexes",
            "second factual-identity index",
            "event-set grouping index",
            "executable disposable M1 revisions",
        }
    ),
    "verification_runtime": frozenset(
        {
            "application factory migration/stamp/repair",
            "ASGI lifespan migration/stamp/repair",
            "CLI migration/stamp/repair",
            "wheel installation migration/stamp/repair",
        }
    ),
    "wip_authority": frozenset(
        {
            "production dependency on M2 WIP",
            "test dependency on an execution prompt as semantic authority",
            "unclassified historical WIP document",
        }
    ),
    "normative_placeholder": frozenset(
        {
            "unresolved normative TBD/TODO/FIXME/open question",
            "unresolved candidate or open design/contract point",
            "PARTIALLY REOPENED authority",
        }
    ),
}

_NEGATIVE_CATEGORY_TARGET = {
    "relationship_model": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_relationship_model_non_goals_and_finite_public_surface"
    ),
    "lifecycle_history": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_lifecycle_and_history_non_goals_are_absent"
    ),
    "api_protocol": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_public_http_inventory_error_catalog_and_forbidden_surface_are_exact"
    ),
    "security_network": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_security_transport_and_secret_surfaces_remain_external"
    ),
    "deployment_platform": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_runtime_deployment_data_protection_and_performance_surfaces_are_absent"
    ),
    "data_protection": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_runtime_deployment_data_protection_and_performance_surfaces_are_absent"
    ),
    "observability": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_observability_and_health_non_goals_are_absent"
    ),
    "cli": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_cli_operation_coverage_import_closure_and_negative_surface_are_exact"
    ),
    "health": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_observability_and_health_non_goals_are_absent"
    ),
    "alembic": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_schema_alembic_and_automatic_migration_surfaces_are_exact"
    ),
    "performance_availability": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_runtime_deployment_data_protection_and_performance_surfaces_are_absent"
    ),
    "verification_public": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_public_http_inventory_error_catalog_and_forbidden_surface_are_exact"
    ),
    "verification_schema": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_schema_alembic_and_automatic_migration_surfaces_are_exact"
    ),
    "verification_runtime": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_schema_alembic_and_automatic_migration_surfaces_are_exact"
    ),
    "wip_authority": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_wip_provenance_is_complete_and_never_implementation_authority"
    ),
    "normative_placeholder": (
        "tests/test_m2_s08_negative_surface.py::"
        "test_normative_corpus_has_no_unresolved_placeholder_or_reopen"
    ),
}
M2_NEGATIVE_SURFACE_TO_TARGETS: dict[str, frozenset[str]] = {
    f"{category}::{entry}": frozenset({_NEGATIVE_CATEGORY_TARGET[category]})
    for category, entries in M2_NEGATIVE_SURFACE_CONTRACT.items()
    for entry in entries
}

M2_CONTRACT_QUALITY_GATES = frozenset(f"M2-CQG-{number:02d}" for number in range(1, 11))
M2_CONTRACT_QUALITY_GATE_TO_TARGETS: dict[str, frozenset[str]] = {
    "M2-CQG-01": frozenset(
        {
            "tests/test_m2_traceability.py::test_s08_capability_portfolio_and_trace_are_exact"
        }
    ),
    "M2-CQG-02": frozenset(
        {
            "tests/test_m2_s08_negative_surface.py::test_normative_corpus_has_no_unresolved_placeholder_or_reopen"
        }
    ),
    "M2-CQG-03": frozenset(
        {
            "tests/test_m2_s08_regression.py::test_m2_delta_allowlists_are_exact_and_closed"
        }
    ),
    "M2-CQG-04": frozenset(
        {
            "tests/test_m2_traceability.py::test_s08_capability_portfolio_and_trace_are_exact"
        }
    ),
    "M2-CQG-05": frozenset(
        {
            "tests/test_m2_traceability.py::test_s08_dependency_graph_and_authority_direction_are_closed"
        }
    ),
    "M2-CQG-06": frozenset(
        {
            "tests/test_m2_s08_negative_surface.py::test_contract_non_goal_registry_matches_frozen_contract"
        }
    ),
    "M2-CQG-07": frozenset(
        {
            "tests/test_m2_s08_regression.py::test_all_preserved_guarantees_have_concrete_collected_targets"
        }
    ),
    "M2-CQG-08": frozenset(
        {
            "tests/test_m2_traceability.py::test_s08_deferred_choices_do_not_change_observable_outcomes"
        }
    ),
    "M2-CQG-09": frozenset(
        {
            "tests/test_m2_traceability.py::test_s08_frozen_vocabulary_and_identifier_hygiene_are_exact"
        }
    ),
    "M2-CQG-10": frozenset(
        {
            "tests/test_m2_traceability.py::test_s08_freeze_and_formal_reopen_rules_remain_explicit"
        }
    ),
}


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    state: str
    targets: frozenset[str]


M2_MUTATION_TO_CALLABLE: dict[str, Mutation] = {
    **{
        mutation_id: owner
        for mutation_id, (owner, _) in DELIVERED_MUTATION_PLANS.items()
    },
    "RD.CN": RelationshipDefinitionService.create_next,
    "RD.R": RelationshipDefinitionService.revise,
    "RD.P": RelationshipDefinitionService.publish,
    "RD.SD": RelationshipDefinitionService.set_default,
    "RD.CD": RelationshipDefinitionService.clear_default,
    "RD.D": RelationshipDefinitionService.deprecate,
    "RD.DD": RelationshipDefinitionService.delete_draft,
    "REL.DC": RelationshipService.data_change,
    "REL.SC": cast(Mutation, RelationshipService.__dict__["_schema_change_attempt"]),
}
M2_MUTATIONS = frozenset(M2_MUTATION_TO_CALLABLE)
M2_MUTATION_TO_GATE: dict[str, AdvisoryGate | None] = {
    mutation_id: gate for mutation_id, (_, gate) in DELIVERED_MUTATION_PLANS.items()
} | {mutation_id: None for mutation_id in M2_MUTATIONS - set(DELIVERED_MUTATION_PLANS)}

_FAMILY_EXECUTION_TARGETS = {
    "DT": frozenset(
        {
            "tests/test_datatype_api.py::test_datatype_full_public_lifecycle",
            "tests/test_datatype_api.py::"
            "test_datatype_active_consumers_and_lineage_delete_authority",
        }
    ),
    "OT": frozenset(
        {
            "tests/test_objecttemplate_api.py::test_objecttemplate_full_lifecycle_and_effective_schema",
            "tests/test_objecttemplate_api.py::"
            "test_objecttemplate_binding_clone_and_publish_recertification",
        }
    ),
    "OBJ": frozenset(
        {
            "tests/test_object_api.py::test_object_create_mutations_reads_lists_and_lifecycle",
            "tests/test_object_api.py::test_s05_ownership_schema_change_reads_and_lifecycle",
        }
    ),
    "RD": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_complete_crud_and_capability_projection",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
        }
    ),
    "REL": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
        }
    ),
}
M2_MUTATION_TO_EVIDENCE = {
    mutation_id: _FAMILY_EXECUTION_TARGETS[mutation_id.partition(".")[0]]
    for mutation_id in M2_MUTATIONS
}


_S02_SEMANTIC_PATH = "tests/test_m2_s02_semantic_concurrency.py::"
S02_ROW_29_TARGETS = frozenset(
    _S02_SEMANTIC_PATH
    + "test_row_29_mutation_delete_both_winner_orders"
    + f"[{delete_first}-{mutation}]"
    for delete_first in (False, True)
    for mutation in ("data", "schema")
)
S02_ROW_27_TARGETS = frozenset(
    _S02_SEMANTIC_PATH
    + "test_row_27_data_and_schema_change_have_serial_factual_history"
    + f"[{winner}]"
    for winner in ("data-first", "schema-first")
)
S02_ROW_28_TARGETS = frozenset(
    _S02_SEMANTIC_PATH
    + "test_row_28_schema_changes_recheck_forward_target_after_wait"
    + f"[{winner}]"
    for winner in ("lower-first", "higher-first")
)
S02_ROW_30_TARGETS = frozenset(
    {
        _S02_SEMANTIC_PATH
        + "test_row_30_schema_change_first_blocks_target_deprecation",
        _S02_SEMANTIC_PATH
        + "test_row_30_target_deprecation_first_blocks_schema_change",
        _S02_SEMANTIC_PATH + "test_row_30_definition_default_change_is_independent",
    }
)
S02_REF_10_TARGETS = frozenset(
    {
        _S02_SEMANTIC_PATH + "test_ref_10_schema_change_first_blocks_definition_delete",
        _S02_SEMANTIC_PATH
        + "test_ref_10_definition_delete_first_rolls_back_then_schema_changes",
    }
)
S02_SNAP_05_TARGETS = frozenset(
    _S02_SEMANTIC_PATH
    + "test_snap_05_each_mutation_observes_each_independent_rename_cut"
    + f"[{rename_case}-{transition}]"
    for rename_case in ("from", "to", "both", "definition")
    for transition in ("data", "schema")
)
S02_FANOUT_TARGETS = frozenset(
    {
        _S02_SEMANTIC_PATH
        + "test_m2_s02_all_transition_families_use_distinct_semantic_fanout"
        + "[symmetric_distinct-False-False-2-2]",
        _S02_SEMANTIC_PATH
        + "test_m2_s02_all_transition_families_use_distinct_semantic_fanout"
        + "[symmetric_self-True-False-1-1]",
        _S02_SEMANTIC_PATH
        + "test_m2_s02_all_transition_families_use_distinct_semantic_fanout"
        + "[inheritance_overlap-False-True-4-2]",
    }
)
S02_READ_CUT_TARGETS = frozenset(
    {
        *(
            _S02_SEMANTIC_PATH
            + "test_relationship_read_cuts_expose_only_committed_before_or_after"
            + f"[{transition}]"
            for transition in ("data", "schema", "delete")
        ),
        *(
            _S02_SEMANTIC_PATH
            + "test_relationship_snapshot_cut_commits_between_physical_reads"
            + f"[{transition}-{read_shape}]"
            for transition in ("data", "schema", "delete")
            for read_shape in ("get", "page")
        ),
    }
)


S01_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-01": frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_rdv_declaration_shape_and_complete_history_rules",
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_complete_crud_and_capability_projection",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_explicit_create_delete_first_preserves_exact_selector",
        }
    ),
    "M2-VER-02": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_18_create_next_allocates_serial_distinct_versions",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_19_create_next_rereads_max_after_draft_delete",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_20_one_exact_generation_consumer_wins",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_atomic_05_differential_failure_rolls_back_revision_and_children",
        }
    ),
    "M2-VER-03": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_21_default_change_serializes_target_deprecation",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_23_rdv_publish_recertifies_complete_history",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_25_published_rdv_blocks_dtv_deprecation_after_wait",
        }
    ),
    "M2-VER-04": frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_rdv_declaration_shape_and_complete_history_rules",
            "tests/test_relationshipdefinition_domain.py::"
            "test_rdv_declaration_rejects_duplicate_and_noncanonical_identity",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_22_object_template_publish_recertifies_member_history",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_23_rdv_publish_recertifies_complete_history",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_implicit_dtv_binding_is_stable_through_commit",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_ref_07_clone_reference_blocks_datatype_root_delete",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_ref_09_rebound_reference_blocks_target_delete",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_reports_rdv_only_and_mixed_property_blockers",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_ot_property_fk_is_bounded",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_rdv_property_fk_is_bounded",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_explicit_create_delete_first_preserves_exact_selector",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_ref_09_explicit_revise_delete_first_preserves_exact_selector",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_implicit_create_delete_first_identifies_lineage",
        }
    ),
    "M2-VER-05": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_complete_crud_and_capability_projection",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_ot_property_fk_is_bounded",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_rdv_property_fk_is_bounded",
        }
    ),
    "M2-VER-06": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_relationship_domain.py::"
            "test_factual_relationship_constructors_require_an_exact_version_pin",
            "tests/test_relationship_domain.py::"
            "test_factual_relationship_rejects_non_positive_or_boolean_exact_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_ref_03_and_ref_05_relationship_object_lifetime_arbitration",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_ref_04_create_reference_first_blocks_definition_delete",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_ref_04_definition_delete_first_rejects_relationship_create",
        }
    ),
    "M2-VER-07": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_05_reciprocal_create_uses_pk_and_rejects_loser",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_07b_winner_disappears_before_fresh_convergence_read",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_atomic_02_later_closure_pk_collision_rolls_back_candidate",
        }
    ),
    "M2-VER-10": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_06_same_id_delete_locks_and_emits_one_event_set",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_07a_late_delete_cannot_remove_recreated_fact",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_atomic_03_delete_event_failure_rolls_back_complete_fact",
        }
    ),
    "M2-VER-20": frozenset(
        {
            "tests/test_schema_metadata.py::"
            "test_metadata_contains_exactly_the_frozen_fifteen_tables",
            "tests/test_migrations.py::"
            "test_durable_root_structure_drift_repeatability_and_owned_downgrade",
        }
    ),
    "M2-VER-21": frozenset(
        {
            "tests/test_migrations.py::"
            "test_durable_root_structure_drift_repeatability_and_owned_downgrade",
            "tests/test_migrations.py::"
            "test_durable_root_failure_rolls_back_and_corrected_rerun_succeeds",
        }
    ),
}

S02_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-08": frozenset(
        {
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_data_change_complete_state_and_noop",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_unique_operation_order_is_nonsemantic",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_application_rejects_empty_and_duplicate_operations",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_row_26_data_changes_reread_fresh_state_and_waiter_can_be_noop",
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails",
        }
    ),
    "M2-VER-09": frozenset(
        {
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_scalar_to_list_migration_is_canonical",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_schema_migration_preserves_removes_and_blocks_by_member",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            *S02_ROW_27_TARGETS,
            *S02_ROW_28_TARGETS,
            *S02_ROW_30_TARGETS,
            *S02_REF_10_TARGETS,
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails",
        }
    ),
    "M2-VER-11": frozenset(
        {
            *S02_READ_CUT_TARGETS,
            "tests/test_relationship_api.py::"
            "test_db_valid_incomplete_runtime_aggregate_maps_to_internal_error",
        }
    ),
    "M2-VER-12": frozenset(
        {
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_historical_property_codec_rejects_invalid_carriers",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_historical_property_codec_accepts_exact_carriers",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_relationship_factual_state_requires_exact_shape",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_relationship_writer_rejects_invalid_transition_shapes",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            "tests/test_relationship_api.py::"
            "test_m2_s02_corrupt_relationship_transition_fails_complete_page",
        }
    ),
    "M2-VER-13": frozenset(
        {
            "tests/test_relationship_domain.py::"
            "test_symmetric_disjoint_and_inheritance_overlap_closure_shapes",
            "tests/test_relationship_api.py::"
            "test_strict_operands_missing_resources_incompatibility_and_self_loop",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            *S02_FANOUT_TARGETS,
        }
    ),
    "M2-VER-14": frozenset(
        {
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_lifecycle_store_is_the_sole_event_table_sql_owner",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_create_event_failure_rolls_back_header_and_complete_closure",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_atomic_03_delete_event_failure_rolls_back_complete_fact",
        }
    ),
}

_S01_PRIMARY_SCENARIO_TARGETS = {
    "ROW-18": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_18_create_next_allocates_serial_distinct_versions",
    "ROW-19": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_19_create_next_rereads_max_after_draft_delete",
    "ROW-20": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_20_one_exact_generation_consumer_wins",
    "ROW-21": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_21_default_change_serializes_target_deprecation",
    "ROW-22": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_22_object_template_publish_recertifies_member_history",
    "ROW-23": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_23_rdv_publish_recertifies_complete_history",
    "ROW-24": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_24_implicit_dtv_binding_is_stable_through_commit",
    "ROW-25": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_25_published_rdv_blocks_dtv_deprecation_after_wait",
    "ROW-30": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict",
    "ARB-05": "tests/test_relationship_semantic_concurrency.py::"
    "test_arb_05_reciprocal_create_uses_pk_and_rejects_loser",
    "ARB-06": "tests/test_relationship_semantic_concurrency.py::"
    "test_arb_06_same_id_delete_locks_and_emits_one_event_set",
    "ARB-07": "tests/test_relationship_semantic_concurrency.py::"
    "test_arb_07b_winner_disappears_before_fresh_convergence_read",
    "ARB-08": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict",
    "REF-03": "tests/test_relationship_semantic_concurrency.py::"
    "test_ref_03_and_ref_05_relationship_object_lifetime_arbitration",
    "REF-04": "tests/test_relationship_semantic_concurrency.py::"
    "test_ref_04_create_reference_first_blocks_definition_delete",
    "REF-07": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_ref_07_clone_reference_blocks_datatype_root_delete",
    "REF-09": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_ref_09_rebound_reference_blocks_target_delete",
    "ATOMIC-02": "tests/test_relationship_semantic_concurrency.py::"
    "test_atomic_02_later_closure_pk_collision_rolls_back_candidate",
    "ATOMIC-03": "tests/test_relationship_semantic_concurrency.py::"
    "test_atomic_03_delete_event_failure_rolls_back_complete_fact",
    "ATOMIC-05": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_atomic_05_differential_failure_rolls_back_revision_and_children",
}

S01_SCENARIO_TARGETS = {
    scenario_id: frozenset({target})
    for scenario_id, target in _S01_PRIMARY_SCENARIO_TARGETS.items()
}
S01_SCENARIO_TARGETS["ROW-24"] |= frozenset(
    {
        "tests/test_m2_s01_semantic_concurrency.py::"
        "test_row_24_explicit_create_delete_first_preserves_exact_selector",
        "tests/test_m2_s01_semantic_concurrency.py::"
        "test_row_24_implicit_create_delete_first_identifies_lineage",
    }
)
S01_SCENARIO_TARGETS["REF-09"] |= frozenset(
    {
        "tests/test_m2_s01_semantic_concurrency.py::"
        "test_ref_09_explicit_revise_delete_first_preserves_exact_selector"
    }
)

S02_SCENARIO_TARGETS = {
    "ROW-26": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_row_26_data_changes_reread_fresh_state_and_waiter_can_be_noop"
        }
    ),
    "ROW-27": S02_ROW_27_TARGETS,
    "ROW-28": S02_ROW_28_TARGETS,
    "ROW-29": frozenset(S02_ROW_29_TARGETS),
    "ROW-30": S02_ROW_30_TARGETS,
    "REF-10": S02_REF_10_TARGETS,
    "SNAP-05": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_snap_05_relationship_mutations_capture_one_metadata_statement",
            *S02_SNAP_05_TARGETS,
        }
    ),
    "ATOMIC-06": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails"
        }
    ),
    "ATOMIC-07": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails"
        }
    ),
}

DELIVERED_SCENARIO_TARGETS = {
    scenario_id: frozenset(f"{target.module}::{target.function}" for target in targets)
    for scenario_id, targets in PGTEST_SCENARIOS.items()
}

_S03_SEMANTIC_PATH = "tests/test_m2_s03_semantic_concurrency.py::"
S03_SCENARIO_TARGETS: dict[str, frozenset[str]] = {
    "ROW-03": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_03_ot_revise_same_generation_has_one_stale_loser"
        }
    ),
    "ROW-04": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_04a_ot_revise_serializes_publish_and_forces_fresh_revision",
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_04b_ot_publish_serializes_delete_draft",
        }
    ),
    "ROW-16": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_16_revise_serializes_whole_lineage_delete",
            *(
                _S03_SEMANTIC_PATH
                + "test_row_16_relationship_definition_internal_and_root_delete_"
                + "both_orders"
                + f"[{order}]"
                for order in ("internal-first", "delete-first")
            ),
        }
    ),
    "REF-08": frozenset(
        _S03_SEMANTIC_PATH
        + "test_ref_08_clone_reference_lifetimes"
        + f"[{order}-{shape}]"
        for order in ("clone-first", "delete-first")
        for shape in ("parent", "component", "property")
    ),
    "REF-09": frozenset(
        {
            *(
                _S03_SEMANTIC_PATH
                + "test_ref_09_differential_rebind_lifetimes"
                + f"[{order}-{family}]"
                for order in ("rebind-first", "delete-first")
                for family in ("object-template-component", "rdv-property")
            ),
            *(
                _S03_SEMANTIC_PATH
                + "test_ref_09_same_target_unchanged_and_removed_plan_variants"
                + f"[{family}]"
                for family in ("object-template", "rdv")
            ),
        }
    ),
    "REF-10": frozenset(
        _S03_SEMANTIC_PATH
        + "test_ref_10_direct_owner_rebinds_target_before_owner"
        + f"[{order}-{family}]"
        for order in ("rebind-first", "delete-first")
        for family in ("object-template-parent", "object-schema")
    ),
    "REF-11": frozenset(
        {
            _S03_SEMANTIC_PATH
            + "test_ref_11_mutual_roots_serialize_through_model_delete_gate"
        }
    ),
    "GATE-07": frozenset(
        {
            _S03_SEMANTIC_PATH
            + "test_gate_07_independent_root_deletes_wait_before_rows_and_reread"
        }
    ),
    "SNAP-01": frozenset(
        _S02_SEMANTIC_PATH
        + "test_snap_05_each_mutation_observes_each_independent_rename_cut"
        + f"[definition-{transition}]"
        for transition in ("data", "schema")
    ),
    "SNAP-02": frozenset(
        _S02_SEMANTIC_PATH
        + "test_snap_05_each_mutation_observes_each_independent_rename_cut"
        + f"[{rename_case}-{transition}]"
        for rename_case in ("from", "to", "both")
        for transition in ("data", "schema")
    ),
    "PAR-06": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_par_06_ot_deprecates_distinct_versions_without_lineage_contention"
        }
    ),
    "PAR-07": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_15_and_par_07_description_lock_topology"
        }
    ),
    "PAR-08": frozenset(
        _S03_SEMANTIC_PATH
        + "test_par_08_definition_rename_compatible_operations_progress"
        + f"[{operation}]"
        for operation in (
            "revise",
            "set-default",
            "deprecate",
            "relationship-create",
        )
    ),
    "PAR-09": frozenset(
        _S03_SEMANTIC_PATH
        + "test_par_09_distinct_rdv_operations_make_progress"
        + f"[{operation}]"
        for operation in ("deprecate", "revise")
    ),
}

PLAN_SCENARIO_TARGETS: dict[str, frozenset[str]] = {
    scenario_id: frozenset(
        target for targets in categories.values() for target in targets
    )
    for scenario_id, categories in PLAN_EVIDENCE_TARGETS.items()
}
M2_SCENARIO_TO_TARGETS: dict[str, frozenset[str]] = {
    scenario_id: DELIVERED_SCENARIO_TARGETS.get(scenario_id, frozenset())
    | S01_SCENARIO_TARGETS.get(scenario_id, frozenset())
    | S02_SCENARIO_TARGETS.get(scenario_id, frozenset())
    | S03_SCENARIO_TARGETS.get(scenario_id, frozenset())
    | PLAN_SCENARIO_TARGETS.get(scenario_id, frozenset())
    for scenario_id in M2_CONCURRENCY_SCENARIOS
}
M2_IMPLEMENTED_SCENARIO_TARGETS = M2_SCENARIO_TO_TARGETS


def _scenario_evidence(*scenario_ids: str) -> frozenset[str]:
    return frozenset(
        target
        for scenario_id in scenario_ids
        for target in M2_SCENARIO_TO_TARGETS[scenario_id]
    )


M2_MUTATION_TO_EVIDENCE.update(
    {
        "OT.C": M2_MUTATION_TO_EVIDENCE["OT.C"]
        | _scenario_evidence("ROW-07", "ROW-08", "REF-01"),
        "OT.CN": M2_MUTATION_TO_EVIDENCE["OT.CN"] | _scenario_evidence("REF-08"),
        "OT.R": M2_MUTATION_TO_EVIDENCE["OT.R"]
        | _scenario_evidence("REF-09", "REF-10"),
        "OT.P": M2_MUTATION_TO_EVIDENCE["OT.P"]
        | _scenario_evidence("ROW-09", "ROW-22"),
        "OBJ.C": M2_MUTATION_TO_EVIDENCE["OBJ.C"] | _scenario_evidence("ROW-24"),
        "OBJ.SC": M2_MUTATION_TO_EVIDENCE["OBJ.SC"]
        | _scenario_evidence("ROW-12", "REF-10"),
        "OBJ.A": M2_MUTATION_TO_EVIDENCE["OBJ.A"]
        | _scenario_evidence("GATE-01", "GATE-02", "GATE-03"),
        "RD.C": M2_MUTATION_TO_EVIDENCE["RD.C"]
        | _scenario_evidence("ROW-24", "GATE-04"),
        "RD.CN": M2_MUTATION_TO_EVIDENCE["RD.CN"] | _scenario_evidence("REF-07"),
        "RD.R": M2_MUTATION_TO_EVIDENCE["RD.R"]
        | _scenario_evidence("REF-09", "PAR-08", "PAR-09"),
        "RD.P": M2_MUTATION_TO_EVIDENCE["RD.P"]
        | _scenario_evidence("ROW-23", "ROW-25"),
        "REL.C": M2_MUTATION_TO_EVIDENCE["REL.C"]
        | _scenario_evidence("ROW-30", "ARB-05", "ARB-08", "PAR-08"),
        "REL.SC": M2_MUTATION_TO_EVIDENCE["REL.SC"]
        | _scenario_evidence("ROW-27", "ROW-28", "ROW-30", "REF-10"),
    }
)


@dataclass(frozen=True, slots=True)
class ScenarioRecipes:
    primary: str
    secondary: frozenset[str] = frozenset()


M2_RECIPES = frozenset(
    {
        "REC-LOCK",
        "REC-UNIQUE",
        "REC-FK",
        "REC-GATE",
        "REC-CUT",
        "REC-ROLLBACK",
        "REC-PROGRESS",
        "REC-ABA",
        "REC-PLAN",
        "REC-CLASSIFY",
        "REC-RESTART",
    }
)
DELIVERED_SCENARIO_TO_RECIPES: dict[str, ScenarioRecipes] = {
    **{
        scenario_id: ScenarioRecipes("REC-LOCK")
        for scenario_id in (
            *(f"ROW-{number:02d}" for number in range(1, 10)),
            *(f"ROW-{number:02d}" for number in range(11, 18)),
        )
    },
    "ROW-10": ScenarioRecipes("REC-CUT"),
    "ARB-01": ScenarioRecipes("REC-UNIQUE"),
    "ARB-02": ScenarioRecipes("REC-UNIQUE"),
    "ARB-03": ScenarioRecipes("REC-LOCK"),
    "ARB-04": ScenarioRecipes("REC-LOCK"),
    "ARB-05": ScenarioRecipes("REC-UNIQUE", frozenset({"REC-ABA"})),
    "ARB-06": ScenarioRecipes("REC-LOCK"),
    "ARB-07": ScenarioRecipes("REC-ABA", frozenset({"REC-UNIQUE"})),
    **{f"REF-{number:02d}": ScenarioRecipes("REC-FK") for number in range(1, 7)},
    "GATE-01": ScenarioRecipes("REC-GATE"),
    "GATE-02": ScenarioRecipes("REC-GATE", frozenset({"REC-CUT"})),
    "GATE-03": ScenarioRecipes("REC-GATE"),
    "GATE-04": ScenarioRecipes("REC-GATE"),
    "GATE-05": ScenarioRecipes("REC-GATE"),
    "GATE-06": ScenarioRecipes("REC-GATE", frozenset({"REC-CUT"})),
    **{f"SNAP-{number:02d}": ScenarioRecipes("REC-CUT") for number in range(1, 5)},
    "ATOMIC-01": ScenarioRecipes("REC-ROLLBACK"),
    "ATOMIC-02": ScenarioRecipes("REC-UNIQUE", frozenset({"REC-ROLLBACK"})),
    "ATOMIC-03": ScenarioRecipes("REC-ROLLBACK"),
    "ATOMIC-04": ScenarioRecipes("REC-ROLLBACK"),
    "PAR-01": ScenarioRecipes("REC-PROGRESS"),
    "PAR-02": ScenarioRecipes("REC-PROGRESS"),
    "PAR-03": ScenarioRecipes("REC-LOCK"),
    "PAR-04": ScenarioRecipes("REC-GATE"),
    "PAR-05": ScenarioRecipes("REC-PROGRESS"),
    "PAR-06": ScenarioRecipes("REC-PROGRESS"),
    "PAR-07": ScenarioRecipes("REC-LOCK", frozenset({"REC-PROGRESS"})),
}

M2_ADDED_SCENARIO_TO_RECIPES: dict[str, ScenarioRecipes] = {
    **{f"ROW-{number:02d}": ScenarioRecipes("REC-LOCK") for number in range(18, 31)},
    "ARB-08": ScenarioRecipes("REC-UNIQUE", frozenset({"REC-ROLLBACK"})),
    **{f"REF-{number:02d}": ScenarioRecipes("REC-FK") for number in range(7, 11)},
    "REF-11": ScenarioRecipes("REC-GATE", frozenset({"REC-FK"})),
    "GATE-07": ScenarioRecipes("REC-GATE"),
    "SNAP-05": ScenarioRecipes("REC-CUT"),
    **{
        f"ATOMIC-{number:02d}": ScenarioRecipes("REC-ROLLBACK")
        for number in range(5, 8)
    },
    "PAR-08": ScenarioRecipes("REC-PROGRESS"),
    "PAR-09": ScenarioRecipes("REC-PROGRESS"),
    "PLAN-01": ScenarioRecipes("REC-PLAN"),
    "PLAN-02": ScenarioRecipes("REC-PLAN"),
    "PLAN-03": ScenarioRecipes("REC-RESTART"),
    "PLAN-04": ScenarioRecipes("REC-CLASSIFY"),
    "PLAN-05": ScenarioRecipes("REC-RESTART"),
    "PLAN-06": ScenarioRecipes("REC-PLAN"),
}

M2_RECIPE_DELTAS: dict[str, ScenarioRecipes] = {
    "ARB-07": ScenarioRecipes("REC-ABA", frozenset({"REC-UNIQUE", "REC-RESTART"}))
}

M2_SCENARIO_TO_RECIPES: dict[str, ScenarioRecipes] = (
    DELIVERED_SCENARIO_TO_RECIPES | M2_ADDED_SCENARIO_TO_RECIPES | M2_RECIPE_DELTAS
)

M2_PREDICATE_TO_SCENARIOS: dict[str, frozenset[str]] = {
    "NU": frozenset({"ARB-01"}),
    "VS": frozenset({"ROW-01", "ROW-02", "ROW-18", "ROW-19"}),
    "DG": frozenset({"ROW-03", "ROW-04", "ROW-20", "ATOMIC-01", "ATOMIC-05"}),
    "LS": frozenset({"ROW-04", "ROW-06", "ROW-20", "ROW-21"}),
    "DV": frozenset(
        {"ROW-05", "ROW-06", "ROW-08", "ROW-21", "ROW-23", "ROW-24", "ROW-30"}
    ),
    "VH": frozenset({"ROW-22", "ROW-23"}),
    "BA": frozenset({"ROW-07", "ROW-08", "ROW-12", "ROW-24", "ROW-28", "ROW-30"}),
    "AM": frozenset({"ROW-09", "ROW-10", "ROW-25"}),
    "RL": frozenset(f"REF-{number:02d}" for number in range(1, 12)),
    "AL": frozenset({"ROW-16", "ROW-17"}),
    "ML": frozenset({"ROW-15"}),
    "OS": frozenset({"ROW-11", "ROW-12", "ATOMIC-04"}),
    "RS": frozenset({"ROW-26", "ROW-27", "ROW-28", "ROW-29", "ATOMIC-06", "ATOMIC-07"}),
    "PO": frozenset({"ROW-13", "ROW-14"}),
    "OF": frozenset({"ARB-03", "ARB-04", "ATOMIC-04"}),
    "SO": frozenset({"ARB-02"}),
    "OC": frozenset({"GATE-01", "GATE-02", "GATE-03", "PAR-04"}),
    "RC": frozenset({"GATE-04", "GATE-05", "GATE-06", "ATOMIC-04"}),
    "RF": frozenset({"ARB-05", "ARB-07", "ARB-08", "ATOMIC-02"}),
    "RA": frozenset({"ARB-06", "ARB-07", "ATOMIC-03"}),
    "ES": frozenset(
        {
            "SNAP-01",
            "SNAP-02",
            "SNAP-03",
            "SNAP-04",
            "SNAP-05",
            "PAR-01",
            "PAR-02",
            "PAR-08",
        }
    ),
}

S03_BUNDLE_SCENARIOS = {
    "M2-VER-15": frozenset({"ROW-03", "ROW-04", "ROW-20", "ATOMIC-01", "ATOMIC-05"}),
    "M2-VER-16": frozenset(
        {
            *(f"ROW-{number:02d}" for number in range(7, 11)),
            *(f"ROW-{number:02d}" for number in range(21, 26)),
            "ROW-30",
        }
    ),
    "M2-VER-17": frozenset({"ARB-05", "ARB-07", "ARB-08", "ATOMIC-02", "PLAN-05"}),
    "M2-VER-18": frozenset({"ROW-26", "ROW-27", "ROW-28", "ROW-29", "ARB-06"}),
    "M2-VER-19": frozenset(
        {
            *(f"SNAP-{number:02d}" for number in range(1, 6)),
            "PAR-01",
            "PAR-02",
            "PAR-08",
        }
    ),
}
S03_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    bundle_id: frozenset(
        target
        for scenario_id in scenario_ids
        for target in M2_SCENARIO_TO_TARGETS[scenario_id]
    )
    for bundle_id, scenario_ids in S03_BUNDLE_SCENARIOS.items()
}
S04_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-22": frozenset(
        {
            "tests/test_runtime_schema_guard.py::"
            "test_installed_graph_discovers_one_base_and_head_without_alembic_ini",
            "tests/test_runtime_schema_guard.py::"
            "test_installed_graph_rejects_non_unique_base_or_head",
            "tests/test_runtime_schema_guard.py::"
            "test_installed_graph_rejects_unreadable_package_safely",
            "tests/test_runtime_schema_guard.py::"
            "test_guard_requires_exact_singleton_revision",
            "tests/test_runtime_schema_guard.py::"
            "test_real_postgresql_exact_head_uses_runtime_engine",
            "tests/test_runtime_schema_guard.py::"
            "test_real_postgresql_rejects_every_non_exact_revision_state_and_restores",
            "tests/test_runtime_schema_guard.py::"
            "test_guard_timeout_is_one_safe_owned_failure",
            "tests/test_runtime_schema_guard.py::"
            "test_inner_guard_timeout_error_is_not_misclassified",
            "tests/test_runtime_schema_guard.py::"
            "test_current_head_inspection_translates_unreachable_database_safely",
            "tests/test_runtime_schema_guard.py::"
            "test_malformed_current_head_result_is_rejected",
            "tests/test_runtime_schema_guard.py::"
            "test_startup_guard_source_has_no_revision_constant_migration_or_repair",
            "tests/test_http_composition.py::"
            "test_guard_failure_prevents_publication_and_disposes_engine",
            "tests/test_http_composition.py::"
            "test_composition_failure_after_guard_disposes_engine",
            "tests/test_http_composition.py::"
            "test_cancelled_startup_disposes_engine_and_propagates",
            "tests/test_http_composition.py::"
            "test_every_app_lifespan_executes_its_own_guard",
            "tests/test_http_composition.py::"
            "test_fastapi_lifespan_does_not_execute_migrations",
            "tests/test_bootstrap_diagnostics.py::"
            "test_factory_settings_failure_diagnostic_sanitizes_credentials",
            "tests/test_bootstrap_diagnostics.py::"
            "test_secret_selector_and_source_diagnostics_hide_selected_path",
            "tests/test_bootstrap_diagnostics.py::"
            "test_asgi_lifespan_expected_guard_diagnostics_are_sanitized",
            "tests/test_bootstrap_diagnostics.py::"
            "test_uvicorn_lifespan_logging_sanitizes_expected_guard_failure",
            "tests/test_bootstrap_diagnostics.py::"
            "test_bootstrap_unexpected_defects_are_not_normalized",
            "tests/test_m2_s04_installed.py::test_installed_wheel_s04_runtime_smoke",
        }
    ),
    "M2-VER-23": frozenset(
        {
            "tests/test_health.py::"
            "test_health_exact_vocabulary_classification_and_one_attempt",
            "tests/test_health.py::"
            "test_health_outer_timeout_waits_for_cleanup_before_measurement",
            "tests/test_health.py::test_health_monotonic_conversion_is_exact",
            "tests/test_health.py::test_health_result_rejects_negative_execution_time",
            "tests/test_health.py::"
            "test_health_unexpected_programming_failure_propagates",
            "tests/test_health.py::test_health_inner_timeout_error_propagates_once",
            "tests/test_health.py::"
            "test_health_cancellation_propagates_after_probe_cleanup",
            "tests/test_health_probe.py::"
            "test_probe_executes_exact_select_one_and_requires_exact_integer",
            "tests/test_health_probe.py::test_probe_rejects_non_exact_scalar",
            "tests/test_health_probe.py::"
            "test_probe_translates_pool_timeout_without_raw_message",
            "tests/test_health_probe.py::"
            "test_probe_translates_expected_database_failure_after_cleanup",
            "tests/test_health_probe.py::"
            "test_probe_does_not_normalize_unexpected_failure",
            "tests/test_health_postgresql.py::"
            "test_real_health_uses_same_engine_exact_select_and_returns_connection",
            "tests/test_health_postgresql.py::"
            "test_real_pool_starvation_times_out_then_recovers_on_same_engine",
            "tests/test_health_api.py::"
            "test_health_healthy_response_is_exact_and_non_cacheable",
            "tests/test_health_api.py::"
            "test_health_unready_response_is_exact_safe_and_non_cacheable",
            "tests/test_health_api.py::"
            "test_health_invalid_request_is_canonical_400_without_probe",
            "tests/test_health_api.py::"
            "test_health_unexpected_service_failure_uses_safe_canonical_500",
            "tests/test_health_api.py::test_health_inner_timeout_is_canonical_safe_500",
            "tests/test_health_api.py::test_health_owned_probe_failures_are_exact_503",
            "tests/test_health_api.py::test_health_owned_outer_timeout_is_exact_503",
            "tests/test_health_api.py::"
            "test_health_openapi_uses_one_dto_for_200_and_503",
            "tests/test_health_api.py::test_health_is_the_only_operational_route",
            "tests/test_m2_s04_scope.py::"
            "test_s04_runtime_and_health_have_no_forbidden_parallel_mechanisms",
            "tests/test_m2_s04_scope.py::"
            "test_health_route_reads_only_precomposed_service",
            "tests/test_m2_s04_installed.py::test_installed_wheel_s04_runtime_smoke",
        }
    ),
}
S05_PRIMARY_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-27": frozenset(
        {
            "tests/test_m2_s05_registry.py::"
            "test_registry_is_exactly_the_server_business_openapi_inventory",
            "tests/test_m2_s05_registry.py::"
            "test_every_registry_spec_is_complete_and_path_metadata_is_closed",
            "tests/test_m2_s05_registry.py::"
            "test_all_registry_examples_parse_to_their_own_command_without_http",
            "tests/test_m2_s05_registry.py::"
            "test_registry_descriptions_and_help_metadata_are_bounded_and_usable",
            "tests/test_m2_s05_registry.py::"
            "test_registry_examples_preserve_exact_selector_presence_and_required_operands",
            "tests/test_m2_s05_registry.py::"
            "test_relationship_definition_examples_cover_both_discriminated_shapes",
            "tests/test_m2_s05_registry.py::"
            "test_fastapi_routes_use_the_neutral_wire_dto_identity",
            "tests/test_m2_s05_registry.py::"
            "test_cli_import_closure_has_no_server_or_database_boundary",
            "tests/test_m2_s05_registry.py::"
            "test_s05_has_no_repl_or_insecure_option_surface",
            "tests/test_m2_s05_registry.py::"
            "test_httpx_is_runtime_dependency_and_console_entrypoint_is_exact",
            "tests/test_m2_s05_parser.py::test_endpoint_root_normalization",
            "tests/test_m2_s05_parser.py::"
            "test_endpoint_root_rejects_non_root_or_credential_surface",
            "tests/test_m2_s05_parser.py::"
            "test_endpoint_root_rejects_every_malformed_explicit_port",
            "tests/test_m2_s05_parser.py::"
            "test_parser_preserves_original_typed_human_intent",
            "tests/test_m2_s05_parser.py::test_json_file_is_read_as_utf8_once",
            "tests/test_m2_s05_parser.py::test_simple_carrier_and_closed_enum_matrix",
            "tests/test_m2_s05_parser.py::"
            "test_structured_parameter_failures_are_finite",
            "tests/test_m2_s05_parser.py::test_finite_local_parse_failures",
            "tests/test_m2_s05_parser.py::"
            "test_nullable_string_distinguishes_null_from_literal_null",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_deduplication_cookie_isolation_and_primary_trace",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_lookup_zero_stops_before_primary_request",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_ambiguity_is_bounded_to_two_ids",
            "tests/test_m2_s05_http_client.py::"
            "test_nested_selector_plan_is_ordered_and_deduplicated",
            "tests/test_m2_s05_http_client.py::"
            "test_human_selector_families_cover_zero_one_many",
            "tests/test_m2_s05_http_client.py::"
            "test_uuid_only_selector_families_accept_uuid_and_reject_names",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_cache_never_survives_one_command",
            "tests/test_m2_s05_http_client.py::"
            "test_uuid_top_level_selector_has_precedence_and_no_lookup",
            "tests/test_m2_s05_http_client.py::"
            "test_remote_business_error_is_preserved_exactly",
            "tests/test_m2_s05_http_client.py::test_protocol_failures_are_not_remapped",
            "tests/test_m2_s05_http_client.py::"
            "test_created_location_is_validated_exactly",
            "tests/test_m2_s05_http_client.py::test_204_with_body_is_protocol_error",
            "tests/test_m2_s05_http_client.py::"
            "test_transport_failure_is_one_attempt_with_response_null",
            "tests/test_m2_s05_http_client.py::"
            "test_registry_uuid_only_selector_is_canonical",
            "tests/test_m2_s05_http_client.py::test_http_timeout_policy_is_exact",
            "tests/test_m2_s05_process.py::"
            "test_console_process_emits_one_json_line_and_needs_no_database_url",
            "tests/test_m2_s05_process.py::"
            "test_console_local_failure_has_exact_output_channels_and_exit",
            "tests/test_m2_s05_process.py::"
            "test_console_rejects_malformed_port_before_command_or_exchange",
            "tests/test_m2_s05_process.py::"
            "test_console_selector_sequence_has_no_health_preflight",
            "tests/test_m2_s05_process.py::"
            "test_console_remote_and_protocol_failures_use_structured_stdout",
            "tests/test_m2_s05_process.py::"
            "test_console_transport_failure_is_structured_and_single_attempt",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_before_any_attempt_has_empty_truthful_trace",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_after_selector_preserves_selector_exchange",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_after_primary_response_preserves_ordered_trace",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_during_cleanup_preserves_primary_exchange",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_exception_text_never_reaches_process_channels",
            "tests/test_m2_s05_review_fixes.py::"
            "test_base_exception_and_cancellation_are_not_normalized",
            "tests/test_m2_s05_review_fixes.py::"
            "test_recursive_snapshots_detach_every_original_constructor_input",
            "tests/test_m2_s05_review_fixes.py::"
            "test_every_public_nested_json_view_is_recursively_immutable",
            "tests/test_m2_s05_review_fixes.py::"
            "test_as_json_mutation_is_detached_and_rendering_is_byte_stable",
            "tests/test_m2_s05_model.py::"
            "test_execution_ledger_updates_one_provisional_attempt_without_duplication",
            "tests/test_m2_s05_model.py::"
            "test_execution_ledger_preserves_begin_order_and_rejects_malformed_use",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_unexpected_parse_before_safe_command_is_bounded_by_run_and_main",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_unexpected_parse_after_safe_command_preserves_exact_typed_intent",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_expected_parse_failure_preserves_its_finite_local_classification",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_parse_base_exceptions_propagate_unchanged",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_pre_send_cookie_failure_has_no_exchange_or_send",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_send_failure_is_exactly_one_response_null_attempt",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_response_trace_failure_preserves_observed_response",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_post_send_cookie_failure_preserves_observed_response",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_selector_then_primary_failure_preserves_exact_attempt_order_and_intent",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_transport_base_exceptions_propagate_unchanged",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_residual_static_boundary_is_finite_and_ledger_owned",
            "tests/test_m2_s05_tls.py::"
            "test_default_tls_verification_trust_and_hostname_matrix",
            "tests/test_m2_s05_installed.py::"
            "test_installed_candidate_wheel_exposes_working_netauto_console",
        }
    )
}
S05_SUPPORTING_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-24": frozenset(
        {
            "tests/test_m2_s05_registry.py::"
            "test_httpx_is_runtime_dependency_and_console_entrypoint_is_exact",
            "tests/test_m2_s05_process.py::"
            "test_console_process_emits_one_json_line_and_needs_no_database_url",
            "tests/test_m2_s05_process.py::"
            "test_console_local_failure_has_exact_output_channels_and_exit",
            "tests/test_m2_s05_process.py::"
            "test_console_selector_sequence_has_no_health_preflight",
            "tests/test_m2_s05_process.py::"
            "test_console_remote_and_protocol_failures_use_structured_stdout",
            "tests/test_m2_s05_process.py::"
            "test_console_transport_failure_is_structured_and_single_attempt",
            "tests/test_m2_s05_installed.py::"
            "test_installed_candidate_wheel_exposes_working_netauto_console",
        }
    ),
    "M2-VER-28": frozenset(
        {
            "tests/test_m2_s05_registry.py::"
            "test_registry_is_exactly_the_server_business_openapi_inventory",
            "tests/test_m2_s05_registry.py::"
            "test_every_registry_spec_is_complete_and_path_metadata_is_closed",
            "tests/test_m2_s05_registry.py::"
            "test_all_registry_examples_parse_to_their_own_command_without_http",
            "tests/test_m2_s05_registry.py::"
            "test_registry_descriptions_and_help_metadata_are_bounded_and_usable",
            "tests/test_m2_s05_registry.py::"
            "test_registry_examples_preserve_exact_selector_presence_and_required_operands",
            "tests/test_m2_s05_registry.py::"
            "test_relationship_definition_examples_cover_both_discriminated_shapes",
            "tests/test_m2_s05_registry.py::"
            "test_cli_import_closure_has_no_server_or_database_boundary",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_deduplication_cookie_isolation_and_primary_trace",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_lookup_zero_stops_before_primary_request",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_ambiguity_is_bounded_to_two_ids",
            "tests/test_m2_s05_http_client.py::"
            "test_nested_selector_plan_is_ordered_and_deduplicated",
            "tests/test_m2_s05_http_client.py::"
            "test_uuid_top_level_selector_has_precedence_and_no_lookup",
            "tests/test_m2_s05_http_client.py::"
            "test_human_selector_families_cover_zero_one_many",
            "tests/test_m2_s05_http_client.py::"
            "test_uuid_only_selector_families_accept_uuid_and_reject_names",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_cache_never_survives_one_command",
            "tests/test_m2_s05_review_fixes.py::"
            "test_recursive_snapshots_detach_every_original_constructor_input",
            "tests/test_m2_s05_review_fixes.py::"
            "test_every_public_nested_json_view_is_recursively_immutable",
            "tests/test_m2_s05_review_fixes.py::"
            "test_as_json_mutation_is_detached_and_rendering_is_byte_stable",
            "tests/test_m2_traceability.py::"
            "test_s05_review_fix_registry_is_exact_and_resolvable",
        }
    ),
    "M2-VER-30": frozenset(
        {
            "tests/test_m2_s05_registry.py::"
            "test_s05_has_no_repl_or_insecure_option_surface",
            "tests/test_m2_s05_parser.py::"
            "test_endpoint_root_rejects_non_root_or_credential_surface",
            "tests/test_m2_s05_parser.py::"
            "test_endpoint_root_rejects_every_malformed_explicit_port",
            "tests/test_m2_s05_process.py::"
            "test_console_rejects_malformed_port_before_command_or_exchange",
            "tests/test_m2_s05_installed.py::"
            "test_installed_candidate_wheel_exposes_working_netauto_console",
            "tests/test_m2_s05_http_client.py::"
            "test_selector_deduplication_cookie_isolation_and_primary_trace",
            "tests/test_m2_s05_tls.py::"
            "test_default_tls_verification_trust_and_hostname_matrix",
        }
    ),
}
S05_REVIEW_FIX_TARGETS = {
    "S05-RF-01": frozenset(
        {
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_before_any_attempt_has_empty_truthful_trace",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_after_selector_preserves_selector_exchange",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_after_primary_response_preserves_ordered_trace",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_during_cleanup_preserves_primary_exchange",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_exception_text_never_reaches_process_channels",
            "tests/test_m2_s05_review_fixes.py::"
            "test_base_exception_and_cancellation_are_not_normalized",
            "tests/test_m2_s05_model.py::"
            "test_execution_ledger_updates_one_provisional_attempt_without_duplication",
            "tests/test_m2_s05_model.py::"
            "test_execution_ledger_preserves_begin_order_and_rejects_malformed_use",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_unexpected_parse_before_safe_command_is_bounded_by_run_and_main",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_unexpected_parse_after_safe_command_preserves_exact_typed_intent",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_expected_parse_failure_preserves_its_finite_local_classification",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_parse_base_exceptions_propagate_unchanged",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_pre_send_cookie_failure_has_no_exchange_or_send",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_send_failure_is_exactly_one_response_null_attempt",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_response_trace_failure_preserves_observed_response",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_post_send_cookie_failure_preserves_observed_response",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_selector_then_primary_failure_preserves_exact_attempt_order_and_intent",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_transport_base_exceptions_propagate_unchanged",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_residual_static_boundary_is_finite_and_ledger_owned",
            "tests/test_m2_s05_http_client.py::"
            "test_remote_business_error_is_preserved_exactly",
            "tests/test_m2_s05_http_client.py::test_protocol_failures_are_not_remapped",
            "tests/test_m2_s05_http_client.py::"
            "test_transport_failure_is_one_attempt_with_response_null",
            "tests/test_m2_s05_installed.py::"
            "test_installed_candidate_wheel_exposes_working_netauto_console",
        }
    ),
    "S05-RF-02": frozenset(
        {
            "tests/test_m2_s05_parser.py::"
            "test_endpoint_root_rejects_every_malformed_explicit_port",
            "tests/test_m2_s05_process.py::"
            "test_console_rejects_malformed_port_before_command_or_exchange",
            "tests/test_m2_s05_installed.py::"
            "test_installed_candidate_wheel_exposes_working_netauto_console",
        }
    ),
    "S05-RF-03": frozenset(
        {
            "tests/test_m2_s05_review_fixes.py::"
            "test_recursive_snapshots_detach_every_original_constructor_input",
            "tests/test_m2_s05_review_fixes.py::"
            "test_every_public_nested_json_view_is_recursively_immutable",
            "tests/test_m2_s05_review_fixes.py::"
            "test_as_json_mutation_is_detached_and_rendering_is_byte_stable",
        }
    ),
    "S05-RF-04": frozenset(
        {
            "tests/test_m2_s05_registry.py::"
            "test_all_registry_examples_parse_to_their_own_command_without_http",
            "tests/test_m2_s05_registry.py::"
            "test_registry_descriptions_and_help_metadata_are_bounded_and_usable",
            "tests/test_m2_s05_registry.py::"
            "test_registry_examples_preserve_exact_selector_presence_and_required_operands",
            "tests/test_m2_s05_registry.py::"
            "test_relationship_definition_examples_cover_both_discriminated_shapes",
            "tests/test_m2_traceability.py::"
            "test_s05_review_fix_registry_is_exact_and_resolvable",
        }
    ),
}
S05_RESIDUAL_REVIEW_FIX_TARGETS = {
    "S05-RF-01": frozenset(
        {
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_before_any_attempt_has_empty_truthful_trace",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_after_selector_preserves_selector_exchange",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_after_primary_response_preserves_ordered_trace",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_failure_during_cleanup_preserves_primary_exchange",
            "tests/test_m2_s05_review_fixes.py::"
            "test_internal_exception_text_never_reaches_process_channels",
            "tests/test_m2_s05_review_fixes.py::"
            "test_base_exception_and_cancellation_are_not_normalized",
            "tests/test_m2_s05_model.py::"
            "test_execution_ledger_updates_one_provisional_attempt_without_duplication",
            "tests/test_m2_s05_model.py::"
            "test_execution_ledger_preserves_begin_order_and_rejects_malformed_use",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_unexpected_parse_before_safe_command_is_bounded_by_run_and_main",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_unexpected_parse_after_safe_command_preserves_exact_typed_intent",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_expected_parse_failure_preserves_its_finite_local_classification",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_parse_base_exceptions_propagate_unchanged",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_pre_send_cookie_failure_has_no_exchange_or_send",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_send_failure_is_exactly_one_response_null_attempt",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_response_trace_failure_preserves_observed_response",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_post_send_cookie_failure_preserves_observed_response",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_selector_then_primary_failure_preserves_exact_attempt_order_and_intent",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_transport_base_exceptions_propagate_unchanged",
            "tests/test_m2_s05_residual_review_fixes.py::"
            "test_residual_static_boundary_is_finite_and_ledger_owned",
            "tests/test_m2_s05_http_client.py::"
            "test_remote_business_error_is_preserved_exactly",
            "tests/test_m2_s05_http_client.py::test_protocol_failures_are_not_remapped",
            "tests/test_m2_s05_http_client.py::"
            "test_transport_failure_is_one_attempt_with_response_null",
            "tests/test_m2_s05_installed.py::"
            "test_installed_candidate_wheel_exposes_working_netauto_console",
        }
    )
}
S04_REVIEW_FIX_TARGETS = {
    "S04-RF-01": frozenset(
        {
            "tests/test_bootstrap_diagnostics.py::"
            "test_factory_settings_failure_diagnostic_sanitizes_credentials",
            "tests/test_bootstrap_diagnostics.py::"
            "test_secret_selector_and_source_diagnostics_hide_selected_path",
            "tests/test_bootstrap_diagnostics.py::"
            "test_asgi_lifespan_expected_guard_diagnostics_are_sanitized",
            "tests/test_bootstrap_diagnostics.py::"
            "test_uvicorn_lifespan_logging_sanitizes_expected_guard_failure",
            "tests/test_bootstrap_diagnostics.py::"
            "test_bootstrap_unexpected_defects_are_not_normalized",
            "tests/test_runtime_schema_guard.py::"
            "test_installed_graph_rejects_unreadable_package_safely",
            "tests/test_runtime_schema_guard.py::"
            "test_current_head_inspection_translates_unreachable_database_safely",
        }
    ),
    "S04-RF-02": frozenset(
        {
            "tests/test_health.py::test_health_inner_timeout_error_propagates_once",
            "tests/test_health.py::"
            "test_health_outer_timeout_waits_for_cleanup_before_measurement",
            "tests/test_health_api.py::test_health_inner_timeout_is_canonical_safe_500",
            "tests/test_health_api.py::test_health_owned_probe_failures_are_exact_503",
            "tests/test_health_api.py::test_health_owned_outer_timeout_is_exact_503",
            "tests/test_runtime_schema_guard.py::"
            "test_guard_timeout_is_one_safe_owned_failure",
            "tests/test_runtime_schema_guard.py::"
            "test_inner_guard_timeout_error_is_not_misclassified",
            "tests/test_health_postgresql.py::"
            "test_real_pool_starvation_times_out_then_recovers_on_same_engine",
        }
    ),
    "S04-RF-03": frozenset(
        {
            "tests/test_m2_traceability.py::"
            "test_s04_review_fix_registry_and_exact_bundle_membership",
            "tests/test_m2_s04_installed.py::test_installed_wheel_s04_runtime_smoke",
        }
    ),
}
S06_REVIEW_FIX_TARGETS: dict[str, frozenset[str]] = {
    "S06-RF-01": frozenset(
        {
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf01_human_selector_204_exposes_exact_target_without_hidden_get",
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf01_nullable_owner_exposes_selected_object_without_recovery_get",
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf01_projection_exposes_resolved_path_and_body_identities",
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf01_exact_uuid_target_is_visible_once_without_lookup_ambiguity",
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf01_json_contract_remains_primary_only_and_target_metadata_absent",
            "tests/test_m2_traceability.py::"
            "test_s06_review_fix_registry_is_exact_resolvable_and_bundle_mapped",
        }
    ),
    "S06-RF-02": frozenset(
        {
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf02_stable_get_identity_mismatch_fails_before_cache_or_use",
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf02_exact_version_identity_mismatch_fails_before_cache_or_use",
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf02_same_lineage_different_version_cycle_stops_immediately",
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf02_multi_lineage_different_version_cycle_stops_before_repeat",
            "tests/test_m2_s06_review_fixes.py::"
            "test_rf02_valid_root_lineage_and_repeated_ids_are_memoized_once",
            "tests/test_m2_traceability.py::"
            "test_s06_review_fix_registry_is_exact_resolvable_and_bundle_mapped",
        }
    ),
}
_S06_REVIEW_FIX_UNION: frozenset[str] = frozenset(
    target for targets in S06_REVIEW_FIX_TARGETS.values() for target in targets
)
S06_PRIMARY_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-25": frozenset(
        {
            f"{path.as_posix()}::{node.name}"
            for path in (
                Path("tests/test_m2_s06_state.py"),
                Path("tests/test_m2_s06_process.py"),
            )
            for node in ast.parse(path.read_text()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        }
    ),
    "M2-VER-26": frozenset(
        {
            f"{path.as_posix()}::{node.name}"
            for path in (Path("tests/test_m2_s06_connection.py"),)
            for node in ast.parse(path.read_text()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        }
    ),
    "M2-VER-28": (
        frozenset(
            {
                f"{path.as_posix()}::{node.name}"
                for path in (Path("tests/test_m2_s06_rendering.py"),)
                for node in ast.parse(path.read_text()).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test_")
            }
        )
        | _S06_REVIEW_FIX_UNION
    ),
}
S07_PRIMARY_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-24": frozenset(
        {
            "tests/test_m2_traceability.py::"
            "test_s07_review_fix_registry_and_complete_bundle_membership",
            "tests/test_m2_s07_distribution.py::"
            "test_pty_read_until_preserves_split_needle_and_exact_tail",
            "tests/test_m2_s07_distribution.py::"
            "test_installed_server_import_and_factory_are_independent_from_cli",
            "tests/test_m2_s07_distribution.py::"
            "test_candidate_wheel_has_exact_version_content_entrypoint_and_exclusions",
            "tests/test_m2_s07_distribution.py::"
            "test_committed_runtime_lock_is_exact_runtime_only_regenerated_export",
            "tests/test_m2_s07_distribution.py::"
            "test_clean_release_sync_and_no_deps_install_are_exact_and_source_isolated",
            "tests/test_m2_s07_distribution.py::"
            "test_installed_cli_import_boundary_and_user_agent_use_distribution_version",
            "tests/test_m2_s07_alembic.py::"
            "test_installed_distribution_discovers_exact_single_package_resource_graph",
            "tests/test_m2_s07_alembic.py::"
            "test_root_revision_payload_checksum_is_unchanged_from_s07_baseline",
            "tests/test_m2_s07_alembic.py::"
            "test_installed_alembic_explicitly_realizes_exact_schema_without_cli_cross_action",
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
        }
    ),
    "M2-VER-29": frozenset(
        {
            "tests/test_m2_traceability.py::"
            "test_s07_review_fix_registry_and_complete_bundle_membership",
            "tests/test_m2_s07_alembic.py::"
            "test_installed_alembic_explicitly_realizes_exact_schema_without_cli_cross_action",
            "tests/test_m2_s07_linux.py::"
            "test_linux_operator_document_is_exact_bounded_and_has_no_hidden_facility",
            "tests/test_m2_s07_linux.py::"
            "test_installed_settings_contract_matches_operator_guide_and_rejects_invalid_values",
            "tests/test_m2_s07_linux.py::"
            "test_installed_cli_local_repl_and_noninteractive_http_need_no_database",
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
            "tests/test_m2_s07_linux.py::"
            "test_installed_worker_returns_complete_503_when_real_pg_transport_is_cut",
        }
    ),
    "M2-VER-30": frozenset(
        {
            "tests/test_m2_traceability.py::"
            "test_s07_review_fix_registry_and_complete_bundle_membership",
            "tests/test_m2_s07_linux.py::"
            "test_linux_operator_document_is_exact_bounded_and_has_no_hidden_facility",
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
            "tests/test_m2_s07_linux.py::"
            "test_installed_worker_returns_complete_503_when_real_pg_transport_is_cut",
            "tests/test_m2_s07_trust.py::"
            "test_installed_cli_https_verifies_trust_and_hostname_without_bypass",
            "tests/test_m2_s07_trust.py::"
            "test_installed_cli_and_settings_expose_no_credentials_or_tls_bypass",
            "tests/test_m2_s07_trust.py::"
            "test_installed_public_contract_has_no_401_403_or_security_scheme",
            "tests/test_m2_s07_trust.py::"
            "test_secret_sentinel_is_absent_from_artifact_docs_config_and_server_argv",
        }
    ),
}
S07_INSTALLED_SUPPORT_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-22": frozenset(
        {
            "tests/test_m2_s07_alembic.py::"
            "test_installed_distribution_discovers_exact_single_package_resource_graph",
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
        }
    ),
    "M2-VER-23": frozenset(
        {
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
            "tests/test_m2_s07_linux.py::"
            "test_installed_worker_returns_complete_503_when_real_pg_transport_is_cut",
        }
    ),
    "M2-VER-25": frozenset(
        {
            "tests/test_m2_s07_linux.py::"
            "test_installed_cli_local_repl_and_noninteractive_http_need_no_database",
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
        }
    ),
    "M2-VER-26": frozenset(
        {
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
        }
    ),
    "M2-VER-27": frozenset(
        {
            "tests/test_m2_s07_distribution.py::"
            "test_installed_cli_import_boundary_and_user_agent_use_distribution_version",
            "tests/test_m2_s07_linux.py::"
            "test_installed_cli_local_repl_and_noninteractive_http_need_no_database",
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
        }
    ),
    "M2-VER-28": frozenset(
        {
            "tests/test_m2_s07_linux.py::"
            "test_installed_cli_local_repl_and_noninteractive_http_need_no_database",
            "tests/test_m2_s07_trust.py::"
            "test_installed_cli_https_verifies_trust_and_hostname_without_bypass",
            "tests/test_m2_s07_trust.py::"
            "test_installed_cli_and_settings_expose_no_credentials_or_tls_bypass",
        }
    ),
}
S07_REVIEW_FIX_TARGETS: dict[str, frozenset[str]] = {
    "S07-RF-01": frozenset(
        {
            "tests/test_m2_s07_linux.py::"
            "test_linux_operator_document_is_exact_bounded_and_has_no_hidden_facility",
            "tests/test_m2_s07_linux.py::"
            "test_installed_settings_contract_matches_operator_guide_and_rejects_invalid_values",
            "tests/test_m2_traceability.py::"
            "test_s07_review_fix_registry_and_complete_bundle_membership",
        }
    ),
    "S07-RF-02": frozenset(
        {
            "tests/test_m2_s07_alembic.py::"
            "test_installed_alembic_explicitly_realizes_exact_schema_without_cli_cross_action",
            "tests/test_m2_s07_linux.py::"
            "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch",
            "tests/test_m2_s07_linux.py::"
            "test_installed_worker_returns_complete_503_when_real_pg_transport_is_cut",
            "tests/test_m2_s07_distribution.py::"
            "test_installed_server_import_and_factory_are_independent_from_cli",
            "tests/test_m2_s07_trust.py::"
            "test_installed_public_contract_has_no_401_403_or_security_scheme",
            "tests/test_m2_traceability.py::"
            "test_s07_review_fix_registry_and_complete_bundle_membership",
        }
    ),
}
_S08_REGRESSION_TARGETS = frozenset(
    {
        "tests/test_m2_s08_regression.py::"
        "test_all_preserved_guarantees_have_concrete_collected_targets",
        "tests/test_m2_s08_regression.py::"
        "test_delivered_scenario_targets_recipes_predicates_and_deltas_are_closed",
        "tests/test_m2_s08_regression.py::test_m2_delta_allowlists_are_exact_and_closed",
        "tests/test_m2_s08_regression.py::"
        "test_public_route_error_and_schema_runtime_deltas_are_exact",
        "tests/test_object_scope.py::test_s08_public_route_and_error_catalog_closure",
        "tests/test_m2_s05_registry.py::"
        "test_registry_is_exactly_the_server_business_openapi_inventory",
        "tests/test_schema_metadata.py::"
        "test_metadata_contains_exactly_the_frozen_fifteen_tables",
        "tests/test_migrations.py::"
        "test_durable_root_structure_drift_repeatability_and_owned_downgrade",
    }
)
_S08_TRACEABILITY_TARGETS = frozenset(
    {
        "tests/test_m2_traceability.py::test_s08_primary_bundle_ownership_is_exact",
        "tests/test_m2_traceability.py::"
        "test_s08_outcome_owner_acceptance_evidence_target_chain_is_complete",
        "tests/test_m2_traceability.py::test_s08_capability_portfolio_and_trace_are_exact",
        "tests/test_m2_traceability.py::test_s08_dependency_graph_and_authority_direction_are_closed",
        "tests/test_m2_traceability.py::test_s08_deferred_choices_do_not_change_observable_outcomes",
        "tests/test_m2_traceability.py::test_s08_frozen_vocabulary_and_identifier_hygiene_are_exact",
        "tests/test_m2_traceability.py::test_s08_freeze_and_formal_reopen_rules_remain_explicit",
        "tests/test_m2_traceability.py::test_s08_all_bundles_are_implemented_nonempty_and_resolvable",
    }
)
_S08_NEGATIVE_TARGETS = frozenset(_NEGATIVE_CATEGORY_TARGET.values()) | frozenset(
    {
        "tests/test_m2_s08_negative_surface.py::"
        "test_contract_non_goal_registry_matches_frozen_contract",
        "tests/test_m2_s08_negative_surface.py::"
        "test_wip_provenance_is_complete_and_never_implementation_authority",
        "tests/test_m2_s08_negative_surface.py::"
        "test_normative_corpus_has_no_unresolved_placeholder_or_reopen",
    }
)
_S08_EVIDENCE_TARGETS = frozenset(
    {
        "tests/test_m2_s08_evidence.py::test_evidence_schema_accepts_one_complete_stable_record",
        "tests/test_m2_s08_evidence.py::test_evidence_schema_rejects_identifier_shape_and_count_drift",
        "tests/test_m2_s08_evidence.py::test_evidence_schema_rejects_secrets_and_implementer_review_decision",
        "tests/test_m2_s08_evidence.py::test_evidence_documentation_matches_validator_and_reserves_s09_record",
    }
)
S08_PRIMARY_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-31": _S08_REGRESSION_TARGETS
    | frozenset(
        target
        for targets in M2_AS_IS_GUARANTEE_TO_TARGETS.values()
        for target in targets
    ),
    "M2-VER-32": _S08_TRACEABILITY_TARGETS
    | _S08_NEGATIVE_TARGETS
    | _S08_EVIDENCE_TARGETS,
}
M2_EVIDENCE_TO_TARGETS = {
    bundle_id: EvidenceBundle(
        "IMPLEMENTED"
        if bundle_id in S01_BUNDLE_TARGETS
        or bundle_id in S02_BUNDLE_TARGETS
        or bundle_id in S03_BUNDLE_TARGETS
        or bundle_id in S04_BUNDLE_TARGETS
        or bundle_id in S05_PRIMARY_BUNDLE_TARGETS
        or bundle_id in S05_SUPPORTING_BUNDLE_TARGETS
        or bundle_id in S06_PRIMARY_BUNDLE_TARGETS
        or bundle_id in S07_PRIMARY_BUNDLE_TARGETS
        or bundle_id in S07_INSTALLED_SUPPORT_TARGETS
        or bundle_id in S08_PRIMARY_BUNDLE_TARGETS
        else "DESIGNED",
        S01_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S02_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S03_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S04_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S05_PRIMARY_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S05_SUPPORTING_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S06_PRIMARY_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S07_PRIMARY_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S07_INSTALLED_SUPPORT_TARGETS.get(bundle_id, frozenset())
        | S08_PRIMARY_BUNDLE_TARGETS.get(bundle_id, frozenset()),
    )
    for bundle_id in M2_EVIDENCE_BUNDLES
}

S01_REVIEW_FIX_TARGETS = {
    "S01-RF-01": frozenset(
        {
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_reports_rdv_only_and_mixed_property_blockers",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_ot_property_fk_is_bounded",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_rdv_property_fk_is_bounded",
            "tests/test_s08_persistence_error_mapping.py::"
            "test_datatype_delete_maps_exact_property_reference_constraints",
        }
    ),
    "S01-RF-02": frozenset(
        {
            "tests/test_relationship_domain.py::"
            "test_factual_relationship_constructors_require_an_exact_version_pin",
            "tests/test_relationship_domain.py::"
            "test_factual_relationship_rejects_non_positive_or_boolean_exact_pin",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
        }
    ),
    "S01-RF-03": frozenset(
        {
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_explicit_create_delete_first_preserves_exact_selector",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_ref_09_explicit_revise_delete_first_preserves_exact_selector",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_implicit_create_delete_first_identifies_lineage",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_implicit_dtv_binding_is_stable_through_commit",
        }
    ),
}

S02_REVIEW_FIX_TARGETS = {
    "S02-RF-01": frozenset(
        {
            *S02_SCENARIO_TARGETS["ROW-26"],
            *S02_ROW_27_TARGETS,
            *S02_ROW_28_TARGETS,
            *S02_ROW_30_TARGETS,
            *S02_REF_10_TARGETS,
        }
    ),
    "S02-RF-02": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract"
        }
    ),
    "S02-RF-03": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_object_relationship_page_batches_only_represented_definitions",
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_published_relationship_history_is_set_based_and_schema_change_uses_it",
        }
    ),
}

S03_REVIEW_FIX_TARGETS = {
    "S03-RF-01": frozenset(
        {
            "tests/test_m2_traceability.py::"
            "test_s03_scenario_registry_targets_and_recipes_are_exact"
        }
    ),
    "S03-RF-02": frozenset(
        {
            "tests/test_m2_s03_semantic_concurrency.py::"
            "test_s03_sqlstate_extraction_is_structural_nested_and_cycle_safe",
            "tests/test_m2_s03_semantic_concurrency.py::"
            "test_s03_worker_outcome_captures_semantic_and_wrapped_database_results",
            "tests/test_m2_s03_semantic_concurrency.py::"
            "test_s03_forbidden_sqlstates_fail_immediately_and_are_never_retried",
            "tests/test_m2_s03_semantic_concurrency.py::"
            "test_gate_07_independent_root_deletes_wait_before_rows_and_reread",
            "tests/test_m2_locking.py::test_plan_05_does_not_retry_unapproved_failures",
            *S03_SCENARIO_TARGETS["REF-08"],
            *S03_SCENARIO_TARGETS["PAR-08"],
            *S01_SCENARIO_TARGETS["ARB-07"],
            *PLAN_SCENARIO_TARGETS["PLAN-03"],
        }
    ),
    "S03-RF-03": S03_SCENARIO_TARGETS["REF-08"],
}

S01_PUBLIC_ROUTE_DELTA = frozenset(
    {
        (
            "POST",
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/create-next",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/set-default",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/clear-default",
        ),
        (
            "GET",
            "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions",
        ),
        (
            "GET",
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/versions/{version}",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/versions/{version}/revise",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/versions/{version}/publish",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/versions/{version}/deprecate",
        ),
        (
            "DELETE",
            "/api/v1/core/relationship-definitions/"
            "{relationship_definition_id}/versions/{version}",
        ),
    }
)

S02_PUBLIC_ROUTE_DELTA = frozenset(
    {
        ("POST", "/api/v1/core/relationships/{relationship_id}/data-change"),
        ("POST", "/api/v1/core/relationships/{relationship_id}/schema-change"),
    }
)

S04_PUBLIC_ROUTE_DELTA = frozenset({("GET", "/health/core")})


def _assert_target_exists(target: str) -> None:
    path_text, separator, test_name = target.partition("::")
    assert separator and test_name.startswith("test_"), target
    function_name = test_name.partition("[")[0]
    path = Path(path_text)
    assert path.is_file(), target
    tree = ast.parse(path.read_text())
    collected_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    assert function_name in collected_names, target
    collected = _collected_test_nodes()
    assert target in collected or any(
        node.startswith(f"{target}[") for node in collected
    ), target


def assert_target_exists(target: str) -> None:
    """Public S08 helper for validating one exact collected pytest node ID."""
    _assert_target_exists(target)


@cache
def _collected_test_nodes() -> frozenset[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return frozenset(
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith("tests/") and "::test_" in line
    )


def test_m2_frozen_identifier_census_is_exact() -> None:
    assert len(M2_OUTCOMES) == 16
    assert len(M2_ACCEPTANCE_CRITERIA) == 32
    assert len(M2_EVIDENCE_BUNDLES) == 32
    assert len(M2_CONCURRENCY_SCENARIOS) == 83
    assert {key.split("-")[0] for key in M2_CONCURRENCY_SCENARIOS} == {
        "ROW",
        "ARB",
        "REF",
        "GATE",
        "SNAP",
        "ATOMIC",
        "PAR",
        "PLAN",
    }
    assert set(M2_OUTCOME_TO_ACCEPTANCE) == M2_OUTCOMES
    assert set(M2_ACCEPTANCE_TO_EVIDENCE) == M2_ACCEPTANCE_CRITERIA
    assert set(M2_ACCEPTANCE_TO_EVIDENCE.values()) == M2_EVIDENCE_BUNDLES


def test_s02_bundle_states_and_targets_are_honest_and_resolvable() -> None:
    assert set(M2_EVIDENCE_TO_TARGETS) == M2_EVIDENCE_BUNDLES
    assert set(S01_BUNDLE_TARGETS) == {
        *(f"M2-VER-{number:02d}" for number in range(1, 8)),
        "M2-VER-10",
        "M2-VER-20",
        "M2-VER-21",
    }
    for bundle_id, evidence in M2_EVIDENCE_TO_TARGETS.items():
        assert (
            bundle_id in S01_BUNDLE_TARGETS
            or bundle_id in S02_BUNDLE_TARGETS
            or bundle_id in S03_BUNDLE_TARGETS
            or bundle_id in S04_BUNDLE_TARGETS
            or bundle_id in S05_PRIMARY_BUNDLE_TARGETS
            or bundle_id in S05_SUPPORTING_BUNDLE_TARGETS
            or bundle_id in S06_PRIMARY_BUNDLE_TARGETS
            or bundle_id in S07_PRIMARY_BUNDLE_TARGETS
            or bundle_id in S07_INSTALLED_SUPPORT_TARGETS
            or bundle_id in S08_PRIMARY_BUNDLE_TARGETS
        )
        assert evidence.state == "IMPLEMENTED"
        assert evidence.targets
        for target in evidence.targets:
            _assert_target_exists(target)


def test_s01_scenario_map_is_exact_and_every_target_resolves() -> None:
    assert set(S01_SCENARIO_TARGETS) == {
        *(f"ROW-{number:02d}" for number in range(18, 26)),
        "ROW-30",
        *(f"ARB-{number:02d}" for number in range(5, 9)),
        "REF-03",
        "REF-04",
        "REF-07",
        "REF-09",
        "ATOMIC-02",
        "ATOMIC-03",
        "ATOMIC-05",
    }
    assert set(S01_SCENARIO_TARGETS) <= M2_CONCURRENCY_SCENARIOS
    for targets in S01_SCENARIO_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)


def test_s02_scenario_map_is_exact_and_every_target_resolves() -> None:
    assert set(S02_SCENARIO_TARGETS) == {
        *(f"ROW-{number:02d}" for number in range(26, 31)),
        "REF-10",
        "SNAP-05",
        "ATOMIC-06",
        "ATOMIC-07",
    }
    assert set(S02_SCENARIO_TARGETS) <= M2_CONCURRENCY_SCENARIOS
    for targets in S02_SCENARIO_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    assert M2_IMPLEMENTED_SCENARIO_TARGETS["ROW-30"] == (
        S01_SCENARIO_TARGETS["ROW-30"] | S02_SCENARIO_TARGETS["ROW-30"]
    )
    assert len(S02_ROW_29_TARGETS) == 4
    assert len(S02_ROW_27_TARGETS) == 2
    assert len(S02_ROW_28_TARGETS) == 2
    assert len(S02_ROW_30_TARGETS) == 3
    assert len(S02_REF_10_TARGETS) == 2
    assert len(S02_SNAP_05_TARGETS) == 8


def test_s01_review_fix_registry_is_exact_resolvable_and_scenario_mapped() -> None:
    assert set(S01_REVIEW_FIX_TARGETS) == {"S01-RF-01", "S01-RF-02", "S01-RF-03"}
    for targets in S01_REVIEW_FIX_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    assert S01_REVIEW_FIX_TARGETS["S01-RF-03"] <= (
        S01_SCENARIO_TARGETS["ROW-24"] | S01_SCENARIO_TARGETS["REF-09"]
    )


def test_s02_review_fix_registry_is_exact_resolvable_and_scenario_mapped() -> None:
    assert set(S02_REVIEW_FIX_TARGETS) == {"S02-RF-01", "S02-RF-02", "S02-RF-03"}
    for targets in S02_REVIEW_FIX_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    assert S02_REVIEW_FIX_TARGETS["S02-RF-01"] == frozenset(
        {
            *S02_SCENARIO_TARGETS["ROW-26"],
            *S02_SCENARIO_TARGETS["ROW-27"],
            *S02_SCENARIO_TARGETS["ROW-28"],
            *S02_SCENARIO_TARGETS["ROW-30"],
            *S02_SCENARIO_TARGETS["REF-10"],
        }
    )


def test_s03_review_fix_registry_is_exact_and_resolvable() -> None:
    assert set(S03_REVIEW_FIX_TARGETS) == {"S03-RF-01", "S03-RF-02", "S03-RF-03"}
    for targets in S03_REVIEW_FIX_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    assert S03_REVIEW_FIX_TARGETS["S03-RF-03"] == M2_SCENARIO_TO_TARGETS["REF-08"]


def test_s02_route_delta_and_preserved_registries_remain_exact() -> None:
    assert len(S01_PUBLIC_ROUTE_DELTA) == 9
    assert all(path.startswith("/api/v1/core/") for _, path in S01_PUBLIC_ROUTE_DELTA)
    assert S02_PUBLIC_ROUTE_DELTA.isdisjoint(S01_PUBLIC_ROUTE_DELTA)
    assert len(S02_PUBLIC_ROUTE_DELTA) == 2
    assert S04_PUBLIC_ROUTE_DELTA == frozenset({("GET", "/health/core")})
    assert S04_PUBLIC_ROUTE_DELTA.isdisjoint(
        S01_PUBLIC_ROUTE_DELTA | S02_PUBLIC_ROUTE_DELTA
    )
    assert set(PLAN_EVIDENCE_TARGETS) == {
        *(f"PLAN-{number:02d}" for number in range(1, 7))
    }


def test_s04_bundle_states_and_targets_are_honest_and_resolvable() -> None:
    assert set(S04_BUNDLE_TARGETS) == {"M2-VER-22", "M2-VER-23"}
    for bundle_id, targets in S04_BUNDLE_TARGETS.items():
        evidence = M2_EVIDENCE_TO_TARGETS[bundle_id]
        assert evidence.state == "IMPLEMENTED"
        assert targets <= evidence.targets
        for target in targets:
            _assert_target_exists(target)


def test_s05_primary_and_supporting_bundle_targets_are_honest() -> None:
    assert set(S05_PRIMARY_BUNDLE_TARGETS) == {"M2-VER-27"}
    assert set(S05_SUPPORTING_BUNDLE_TARGETS) == {
        "M2-VER-24",
        "M2-VER-28",
        "M2-VER-30",
    }
    for bundle_id, targets in {
        **S05_PRIMARY_BUNDLE_TARGETS,
        **S05_SUPPORTING_BUNDLE_TARGETS,
    }.items():
        evidence = M2_EVIDENCE_TO_TARGETS[bundle_id]
        assert evidence.state == "IMPLEMENTED"
        assert targets <= evidence.targets
        for target in targets:
            _assert_target_exists(target)
    assert M2_EVIDENCE_TO_TARGETS["M2-VER-27"].targets == (
        S05_PRIMARY_BUNDLE_TARGETS["M2-VER-27"]
        | S07_INSTALLED_SUPPORT_TARGETS["M2-VER-27"]
    )
    defined_s05_targets = {
        f"{path.as_posix()}::{node.name}"
        for path in sorted(Path("tests").glob("test_m2_s05_*.py"))
        for node in ast.parse(path.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    assert S05_PRIMARY_BUNDLE_TARGETS["M2-VER-27"] == defined_s05_targets
    for s08_bundle in ("M2-VER-31", "M2-VER-32"):
        assert M2_PRIMARY_BUNDLE_OWNER[s08_bundle] == "M2-S08"
        assert M2_EVIDENCE_TO_TARGETS[s08_bundle].state == "IMPLEMENTED"
        assert M2_EVIDENCE_TO_TARGETS[s08_bundle].targets


def test_s06_primary_bundle_targets_are_honest_complete_and_resolvable() -> None:
    assert set(S06_PRIMARY_BUNDLE_TARGETS) == {
        "M2-VER-25",
        "M2-VER-26",
        "M2-VER-28",
    }
    defined_s06_targets = {
        f"{path.as_posix()}::{node.name}"
        for path in sorted(Path("tests").glob("test_m2_s06_*.py"))
        for node in ast.parse(path.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    assert set().union(*S06_PRIMARY_BUNDLE_TARGETS.values()) == (
        defined_s06_targets
        | {
            "tests/test_m2_traceability.py::"
            "test_s06_review_fix_registry_is_exact_resolvable_and_bundle_mapped"
        }
    )
    assert S06_PRIMARY_BUNDLE_TARGETS["M2-VER-28"].isdisjoint(
        S05_SUPPORTING_BUNDLE_TARGETS["M2-VER-28"]
    )
    for bundle_id, targets in S06_PRIMARY_BUNDLE_TARGETS.items():
        assert targets
        evidence = M2_EVIDENCE_TO_TARGETS[bundle_id]
        assert evidence.state == "IMPLEMENTED"
        assert targets <= evidence.targets
        for target in targets:
            _assert_target_exists(target)


def test_s06_review_fix_registry_is_exact_resolvable_and_bundle_mapped() -> None:
    assert set(S06_REVIEW_FIX_TARGETS) == {"S06-RF-01", "S06-RF-02"}
    assert len(S06_REVIEW_FIX_TARGETS["S06-RF-01"]) == 6
    assert len(S06_REVIEW_FIX_TARGETS["S06-RF-02"]) == 6
    review_union: frozenset[str] = frozenset(
        target for targets in S06_REVIEW_FIX_TARGETS.values() for target in targets
    )
    assert len(review_union) == 11
    for targets in S06_REVIEW_FIX_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    assert review_union <= frozenset().union(
        *(
            S06_PRIMARY_BUNDLE_TARGETS[bundle_id]
            for bundle_id in (
                "M2-VER-25",
                "M2-VER-26",
                "M2-VER-28",
            )
        )
    )
    assert review_union <= S06_PRIMARY_BUNDLE_TARGETS["M2-VER-28"]
    assert M2_EVIDENCE_TO_TARGETS["M2-VER-27"].targets == (
        S05_PRIMARY_BUNDLE_TARGETS["M2-VER-27"]
        | S07_INSTALLED_SUPPORT_TARGETS["M2-VER-27"]
    )
    for bundle_id in ("M2-VER-31", "M2-VER-32"):
        assert M2_PRIMARY_BUNDLE_OWNER[bundle_id] == "M2-S08"
        assert M2_EVIDENCE_TO_TARGETS[bundle_id].state == "IMPLEMENTED"
        assert M2_EVIDENCE_TO_TARGETS[bundle_id].targets


def test_s07_primary_and_installed_support_registries_are_exact_and_resolvable() -> (
    None
):
    assert set(S07_PRIMARY_BUNDLE_TARGETS) == {
        "M2-VER-24",
        "M2-VER-29",
        "M2-VER-30",
    }
    assert set(S07_INSTALLED_SUPPORT_TARGETS) == {
        "M2-VER-22",
        "M2-VER-23",
        "M2-VER-25",
        "M2-VER-26",
        "M2-VER-27",
        "M2-VER-28",
    }
    all_s07_targets = frozenset(
        target
        for targets in (
            *S07_PRIMARY_BUNDLE_TARGETS.values(),
            *S07_INSTALLED_SUPPORT_TARGETS.values(),
        )
        for target in targets
    )
    defined_s07_targets = {
        f"{path.as_posix()}::{node.name}"
        for path in sorted(Path("tests").glob("test_m2_s07_*.py"))
        for node in ast.parse(path.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    review_trace_target = (
        "tests/test_m2_traceability.py::"
        "test_s07_review_fix_registry_and_complete_bundle_membership"
    )
    assert all_s07_targets == defined_s07_targets | {review_trace_target}
    for bundle_id, targets in {
        **S07_PRIMARY_BUNDLE_TARGETS,
        **S07_INSTALLED_SUPPORT_TARGETS,
    }.items():
        assert targets
        assert targets <= M2_EVIDENCE_TO_TARGETS[bundle_id].targets
        assert M2_EVIDENCE_TO_TARGETS[bundle_id].state == "IMPLEMENTED"
        for target in targets:
            _assert_target_exists(target)
    assert S05_SUPPORTING_BUNDLE_TARGETS["M2-VER-24"] <= (
        M2_EVIDENCE_TO_TARGETS["M2-VER-24"].targets
    )
    assert S05_SUPPORTING_BUNDLE_TARGETS["M2-VER-30"] <= (
        M2_EVIDENCE_TO_TARGETS["M2-VER-30"].targets
    )
    assert (
        M2_EVIDENCE_TO_TARGETS["M2-VER-29"].targets
        == (S07_PRIMARY_BUNDLE_TARGETS["M2-VER-29"])
    )
    for bundle_id in ("M2-VER-31", "M2-VER-32"):
        assert M2_PRIMARY_BUNDLE_OWNER[bundle_id] == "M2-S08"
        assert M2_EVIDENCE_TO_TARGETS[bundle_id].state == "IMPLEMENTED"
        assert M2_EVIDENCE_TO_TARGETS[bundle_id].targets


def test_s07_review_fix_registry_and_complete_bundle_membership() -> None:
    assert set(S07_REVIEW_FIX_TARGETS) == {"S07-RF-01", "S07-RF-02"}
    assert len(S07_REVIEW_FIX_TARGETS["S07-RF-01"]) == 3
    assert len(S07_REVIEW_FIX_TARGETS["S07-RF-02"]) == 6
    for targets in S07_REVIEW_FIX_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)

    assert (
        S07_REVIEW_FIX_TARGETS["S07-RF-01"] <= (S07_PRIMARY_BUNDLE_TARGETS["M2-VER-29"])
    )
    assert S07_REVIEW_FIX_TARGETS["S07-RF-02"] <= (
        S07_PRIMARY_BUNDLE_TARGETS["M2-VER-24"]
        | S07_PRIMARY_BUNDLE_TARGETS["M2-VER-30"]
    )

    explicit_alembic = (
        "tests/test_m2_s07_alembic.py::"
        "test_installed_alembic_explicitly_realizes_exact_schema_without_cli_cross_action"
    )
    lifecycle = (
        "tests/test_m2_s07_linux.py::"
        "test_installed_server_migration_start_health_cli_stop_restart_and_mismatch"
    )
    transport_cut = (
        "tests/test_m2_s07_linux.py::"
        "test_installed_worker_returns_complete_503_when_real_pg_transport_is_cut"
    )
    server_no_cli = (
        "tests/test_m2_s07_distribution.py::"
        "test_installed_server_import_and_factory_are_independent_from_cli"
    )
    settings_contract = (
        "tests/test_m2_s07_linux.py::"
        "test_installed_settings_contract_matches_operator_guide_and_rejects_invalid_values"
    )
    no_native_security = (
        "tests/test_m2_s07_trust.py::"
        "test_installed_public_contract_has_no_401_403_or_security_scheme"
    )
    assert {explicit_alembic, lifecycle, server_no_cli} <= (
        S07_PRIMARY_BUNDLE_TARGETS["M2-VER-24"]
    )
    assert settings_contract in S07_PRIMARY_BUNDLE_TARGETS["M2-VER-29"]
    assert {no_native_security, lifecycle, transport_cut} <= (
        S07_PRIMARY_BUNDLE_TARGETS["M2-VER-30"]
    )

    for bundle_id in ("M2-VER-24", "M2-VER-30"):
        assert S05_SUPPORTING_BUNDLE_TARGETS[bundle_id]
        assert S05_SUPPORTING_BUNDLE_TARGETS[bundle_id] <= (
            M2_EVIDENCE_TO_TARGETS[bundle_id].targets
        )
    assert set(S07_INSTALLED_SUPPORT_TARGETS) == {
        "M2-VER-22",
        "M2-VER-23",
        "M2-VER-25",
        "M2-VER-26",
        "M2-VER-27",
        "M2-VER-28",
    }
    assert all(S07_INSTALLED_SUPPORT_TARGETS.values())
    for bundle_id in ("M2-VER-31", "M2-VER-32"):
        assert M2_PRIMARY_BUNDLE_OWNER[bundle_id] == "M2-S08"
        assert M2_EVIDENCE_TO_TARGETS[bundle_id].state == "IMPLEMENTED"
        assert M2_EVIDENCE_TO_TARGETS[bundle_id].targets

    defined_s07_targets = {
        f"{path.as_posix()}::{node.name}"
        for path in sorted(Path("tests").glob("test_m2_s07_*.py"))
        for node in ast.parse(path.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    mapped_s07_targets: frozenset[str] = frozenset(
        target
        for targets in (
            *S07_PRIMARY_BUNDLE_TARGETS.values(),
            *S07_INSTALLED_SUPPORT_TARGETS.values(),
        )
        for target in targets
    )
    assert defined_s07_targets <= mapped_s07_targets


def test_s05_review_fix_registry_is_exact_and_resolvable() -> None:
    assert set(S05_REVIEW_FIX_TARGETS) == {
        "S05-RF-01",
        "S05-RF-02",
        "S05-RF-03",
        "S05-RF-04",
    }
    all_review_targets: set[str] = set()
    for targets in S05_REVIEW_FIX_TARGETS.values():
        assert targets
        all_review_targets.update(targets)
        for target in targets:
            _assert_target_exists(target)
    bundle_targets: set[str] = set(S05_PRIMARY_BUNDLE_TARGETS["M2-VER-27"])
    bundle_targets.update(S05_SUPPORTING_BUNDLE_TARGETS["M2-VER-24"])
    bundle_targets.update(S05_SUPPORTING_BUNDLE_TARGETS["M2-VER-28"])
    bundle_targets.update(S05_SUPPORTING_BUNDLE_TARGETS["M2-VER-30"])
    assert all_review_targets <= bundle_targets


def test_s05_residual_review_fix_registry_is_exact_and_resolvable() -> None:
    assert set(S05_RESIDUAL_REVIEW_FIX_TARGETS) == {"S05-RF-01"}
    targets = S05_RESIDUAL_REVIEW_FIX_TARGETS["S05-RF-01"]
    assert len(targets) == 23
    for target in targets:
        _assert_target_exists(target)
    assert targets <= S05_REVIEW_FIX_TARGETS["S05-RF-01"]
    assert targets <= S05_PRIMARY_BUNDLE_TARGETS["M2-VER-27"]


def test_s05_preserves_exact_business_and_cli_operation_inventories() -> None:
    assert len(M2_MUTATIONS) == 41
    assert sum(spec.method == "GET" for spec in COMMAND_REGISTRY.values()) == 22
    assert len(BUSINESS_OPERATION_SET) == 63
    assert len(COMMAND_REGISTRY) == 63
    assert len(S04_PUBLIC_ROUTE_DELTA) == 1
    assert len(BUSINESS_OPERATION_SET | S04_PUBLIC_ROUTE_DELTA) == 64


def test_s04_review_fix_registry_and_exact_bundle_membership() -> None:
    assert S04_BUNDLE_TARGETS == {
        "M2-VER-22": frozenset(
            {
                "tests/test_runtime_schema_guard.py::"
                "test_installed_graph_discovers_one_base_and_head_without_alembic_ini",
                "tests/test_runtime_schema_guard.py::"
                "test_installed_graph_rejects_non_unique_base_or_head",
                "tests/test_runtime_schema_guard.py::"
                "test_installed_graph_rejects_unreadable_package_safely",
                "tests/test_runtime_schema_guard.py::"
                "test_guard_requires_exact_singleton_revision",
                "tests/test_runtime_schema_guard.py::"
                "test_real_postgresql_exact_head_uses_runtime_engine",
                "tests/test_runtime_schema_guard.py::"
                "test_real_postgresql_rejects_every_non_exact_revision_state_and_restores",
                "tests/test_runtime_schema_guard.py::"
                "test_guard_timeout_is_one_safe_owned_failure",
                "tests/test_runtime_schema_guard.py::"
                "test_inner_guard_timeout_error_is_not_misclassified",
                "tests/test_runtime_schema_guard.py::"
                "test_current_head_inspection_translates_unreachable_database_safely",
                "tests/test_runtime_schema_guard.py::"
                "test_malformed_current_head_result_is_rejected",
                "tests/test_runtime_schema_guard.py::"
                "test_startup_guard_source_has_no_revision_constant_migration_or_repair",
                "tests/test_http_composition.py::"
                "test_guard_failure_prevents_publication_and_disposes_engine",
                "tests/test_http_composition.py::"
                "test_composition_failure_after_guard_disposes_engine",
                "tests/test_http_composition.py::"
                "test_cancelled_startup_disposes_engine_and_propagates",
                "tests/test_http_composition.py::"
                "test_every_app_lifespan_executes_its_own_guard",
                "tests/test_http_composition.py::"
                "test_fastapi_lifespan_does_not_execute_migrations",
                "tests/test_bootstrap_diagnostics.py::"
                "test_factory_settings_failure_diagnostic_sanitizes_credentials",
                "tests/test_bootstrap_diagnostics.py::"
                "test_secret_selector_and_source_diagnostics_hide_selected_path",
                "tests/test_bootstrap_diagnostics.py::"
                "test_asgi_lifespan_expected_guard_diagnostics_are_sanitized",
                "tests/test_bootstrap_diagnostics.py::"
                "test_uvicorn_lifespan_logging_sanitizes_expected_guard_failure",
                "tests/test_bootstrap_diagnostics.py::"
                "test_bootstrap_unexpected_defects_are_not_normalized",
                "tests/test_m2_s04_installed.py::test_installed_wheel_s04_runtime_smoke",
            }
        ),
        "M2-VER-23": frozenset(
            {
                "tests/test_health.py::"
                "test_health_exact_vocabulary_classification_and_one_attempt",
                "tests/test_health.py::"
                "test_health_outer_timeout_waits_for_cleanup_before_measurement",
                "tests/test_health.py::test_health_monotonic_conversion_is_exact",
                "tests/test_health.py::"
                "test_health_result_rejects_negative_execution_time",
                "tests/test_health.py::"
                "test_health_unexpected_programming_failure_propagates",
                "tests/test_health.py::test_health_inner_timeout_error_propagates_once",
                "tests/test_health.py::"
                "test_health_cancellation_propagates_after_probe_cleanup",
                "tests/test_health_probe.py::"
                "test_probe_executes_exact_select_one_and_requires_exact_integer",
                "tests/test_health_probe.py::test_probe_rejects_non_exact_scalar",
                "tests/test_health_probe.py::"
                "test_probe_translates_pool_timeout_without_raw_message",
                "tests/test_health_probe.py::"
                "test_probe_translates_expected_database_failure_after_cleanup",
                "tests/test_health_probe.py::"
                "test_probe_does_not_normalize_unexpected_failure",
                "tests/test_health_postgresql.py::"
                "test_real_health_uses_same_engine_exact_select_and_returns_connection",
                "tests/test_health_postgresql.py::"
                "test_real_pool_starvation_times_out_then_recovers_on_same_engine",
                "tests/test_health_api.py::"
                "test_health_healthy_response_is_exact_and_non_cacheable",
                "tests/test_health_api.py::"
                "test_health_unready_response_is_exact_safe_and_non_cacheable",
                "tests/test_health_api.py::"
                "test_health_invalid_request_is_canonical_400_without_probe",
                "tests/test_health_api.py::"
                "test_health_unexpected_service_failure_uses_safe_canonical_500",
                "tests/test_health_api.py::"
                "test_health_inner_timeout_is_canonical_safe_500",
                "tests/test_health_api.py::"
                "test_health_owned_probe_failures_are_exact_503",
                "tests/test_health_api.py::"
                "test_health_owned_outer_timeout_is_exact_503",
                "tests/test_health_api.py::"
                "test_health_openapi_uses_one_dto_for_200_and_503",
                "tests/test_health_api.py::test_health_is_the_only_operational_route",
                "tests/test_m2_s04_scope.py::"
                "test_s04_runtime_and_health_have_no_forbidden_parallel_mechanisms",
                "tests/test_m2_s04_scope.py::"
                "test_health_route_reads_only_precomposed_service",
                "tests/test_m2_s04_installed.py::test_installed_wheel_s04_runtime_smoke",
            }
        ),
    }
    assert S04_REVIEW_FIX_TARGETS == {
        "S04-RF-01": frozenset(
            {
                "tests/test_bootstrap_diagnostics.py::"
                "test_factory_settings_failure_diagnostic_sanitizes_credentials",
                "tests/test_bootstrap_diagnostics.py::"
                "test_secret_selector_and_source_diagnostics_hide_selected_path",
                "tests/test_bootstrap_diagnostics.py::"
                "test_asgi_lifespan_expected_guard_diagnostics_are_sanitized",
                "tests/test_bootstrap_diagnostics.py::"
                "test_uvicorn_lifespan_logging_sanitizes_expected_guard_failure",
                "tests/test_bootstrap_diagnostics.py::"
                "test_bootstrap_unexpected_defects_are_not_normalized",
                "tests/test_runtime_schema_guard.py::"
                "test_installed_graph_rejects_unreadable_package_safely",
                "tests/test_runtime_schema_guard.py::"
                "test_current_head_inspection_translates_unreachable_database_safely",
            }
        ),
        "S04-RF-02": frozenset(
            {
                "tests/test_health.py::test_health_inner_timeout_error_propagates_once",
                "tests/test_health.py::"
                "test_health_outer_timeout_waits_for_cleanup_before_measurement",
                "tests/test_health_api.py::"
                "test_health_inner_timeout_is_canonical_safe_500",
                "tests/test_health_api.py::"
                "test_health_owned_probe_failures_are_exact_503",
                "tests/test_health_api.py::"
                "test_health_owned_outer_timeout_is_exact_503",
                "tests/test_runtime_schema_guard.py::"
                "test_guard_timeout_is_one_safe_owned_failure",
                "tests/test_runtime_schema_guard.py::"
                "test_inner_guard_timeout_error_is_not_misclassified",
                "tests/test_health_postgresql.py::"
                "test_real_pool_starvation_times_out_then_recovers_on_same_engine",
            }
        ),
        "S04-RF-03": frozenset(
            {
                "tests/test_m2_traceability.py::"
                "test_s04_review_fix_registry_and_exact_bundle_membership",
                "tests/test_m2_s04_installed.py::"
                "test_installed_wheel_s04_runtime_smoke",
            }
        ),
    }
    for targets in S04_REVIEW_FIX_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    implemented = {
        bundle_id
        for bundle_id, evidence in M2_EVIDENCE_TO_TARGETS.items()
        if evidence.state == "IMPLEMENTED"
    }
    assert implemented == M2_EVIDENCE_BUNDLES
    assert {
        bundle_id
        for bundle_id, evidence in M2_EVIDENCE_TO_TARGETS.items()
        if evidence.state == "DESIGNED"
    } == set()


def test_s03_mutation_registry_is_exact_central_and_executable() -> None:
    assert len(M2_MUTATIONS) == 41
    assert sum(item.startswith("DT.") for item in M2_MUTATIONS) == 10
    assert sum(item.startswith("OT.") for item in M2_MUTATIONS) == 10
    assert sum(item.startswith("OBJ.") for item in M2_MUTATIONS) == 7
    assert sum(item.startswith("RD.") for item in M2_MUTATIONS) == 10
    assert sum(item.startswith("REL.") for item in M2_MUTATIONS) == 4
    assert set(M2_MUTATION_TO_CALLABLE) == M2_MUTATIONS
    assert set(M2_MUTATION_TO_GATE) == M2_MUTATIONS
    assert set(M2_MUTATION_TO_EVIDENCE) == M2_MUTATIONS
    assert {
        mutation_id: gate
        for mutation_id, gate in M2_MUTATION_TO_GATE.items()
        if gate is not None
    } == {
        "OBJ.A": AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE,
        "RD.C": AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
        "RD.RN": AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
        "DT.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
        "OT.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
        "RD.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
    }
    assert len(set(AdvisoryGate)) == 3
    assert set(RowLockMode) == {
        RowLockMode.KS,
        RowLockMode.S,
        RowLockMode.NKU,
        RowLockMode.U,
    }
    for mutation_id, owner in M2_MUTATION_TO_CALLABLE.items():
        source = inspect.getsource(owner)
        assert "_acquire(" in source or "prepare_lock_plan(" in source, mutation_id
        assert "begin_dml()" in source, mutation_id
        assert M2_MUTATION_TO_EVIDENCE[mutation_id]
        for target in M2_MUTATION_TO_EVIDENCE[mutation_id]:
            _assert_target_exists(target)


def test_s03_scenario_registry_targets_and_recipes_are_exact() -> None:
    assert set(M2_SCENARIO_TO_TARGETS) == M2_CONCURRENCY_SCENARIOS
    assert set(M2_SCENARIO_TO_RECIPES) == M2_CONCURRENCY_SCENARIOS
    assert set(M2_SCENARIO_TO_RECIPES.values())
    assert M2_RECIPES == {
        "REC-LOCK",
        "REC-UNIQUE",
        "REC-FK",
        "REC-GATE",
        "REC-CUT",
        "REC-ROLLBACK",
        "REC-PROGRESS",
        "REC-ABA",
        "REC-PLAN",
        "REC-CLASSIFY",
        "REC-RESTART",
    }
    expected: dict[str, ScenarioRecipes] = {
        **{
            scenario_id: ScenarioRecipes("REC-LOCK")
            for scenario_id in (
                *(f"ROW-{number:02d}" for number in range(1, 10)),
                *(f"ROW-{number:02d}" for number in range(11, 31)),
            )
        },
        "ROW-10": ScenarioRecipes("REC-CUT"),
        "ARB-01": ScenarioRecipes("REC-UNIQUE"),
        "ARB-02": ScenarioRecipes("REC-UNIQUE"),
        "ARB-03": ScenarioRecipes("REC-LOCK"),
        "ARB-04": ScenarioRecipes("REC-LOCK"),
        "ARB-05": ScenarioRecipes("REC-UNIQUE", frozenset({"REC-ABA"})),
        "ARB-06": ScenarioRecipes("REC-LOCK"),
        "ARB-07": ScenarioRecipes("REC-ABA", frozenset({"REC-UNIQUE", "REC-RESTART"})),
        "ARB-08": ScenarioRecipes("REC-UNIQUE", frozenset({"REC-ROLLBACK"})),
        **{f"REF-{number:02d}": ScenarioRecipes("REC-FK") for number in range(1, 11)},
        "REF-11": ScenarioRecipes("REC-GATE", frozenset({"REC-FK"})),
        **{
            f"GATE-{number:02d}": ScenarioRecipes("REC-GATE")
            for number in (1, 3, 4, 5, 7)
        },
        "GATE-02": ScenarioRecipes("REC-GATE", frozenset({"REC-CUT"})),
        "GATE-06": ScenarioRecipes("REC-GATE", frozenset({"REC-CUT"})),
        **{f"SNAP-{number:02d}": ScenarioRecipes("REC-CUT") for number in range(1, 6)},
        **{
            f"ATOMIC-{number:02d}": ScenarioRecipes("REC-ROLLBACK")
            for number in (1, 3, 4, 5, 6, 7)
        },
        "ATOMIC-02": ScenarioRecipes("REC-UNIQUE", frozenset({"REC-ROLLBACK"})),
        **{
            f"PAR-{number:02d}": ScenarioRecipes("REC-PROGRESS")
            for number in (1, 2, 5, 6, 8, 9)
        },
        "PAR-03": ScenarioRecipes("REC-LOCK"),
        "PAR-04": ScenarioRecipes("REC-GATE"),
        "PAR-07": ScenarioRecipes("REC-LOCK", frozenset({"REC-PROGRESS"})),
        "PLAN-01": ScenarioRecipes("REC-PLAN"),
        "PLAN-02": ScenarioRecipes("REC-PLAN"),
        "PLAN-03": ScenarioRecipes("REC-RESTART"),
        "PLAN-04": ScenarioRecipes("REC-CLASSIFY"),
        "PLAN-05": ScenarioRecipes("REC-RESTART"),
        "PLAN-06": ScenarioRecipes("REC-PLAN"),
    }
    assert len(expected) == 83
    assert M2_SCENARIO_TO_RECIPES == expected
    assert set(DELIVERED_SCENARIO_TO_RECIPES) == {
        *(f"ROW-{number:02d}" for number in range(1, 18)),
        *(f"ARB-{number:02d}" for number in range(1, 8)),
        *(f"REF-{number:02d}" for number in range(1, 7)),
        *(f"GATE-{number:02d}" for number in range(1, 7)),
        *(f"SNAP-{number:02d}" for number in range(1, 5)),
        *(f"ATOMIC-{number:02d}" for number in range(1, 5)),
        *(f"PAR-{number:02d}" for number in range(1, 8)),
    }
    assert set(M2_ADDED_SCENARIO_TO_RECIPES).isdisjoint(DELIVERED_SCENARIO_TO_RECIPES)
    assert set(M2_RECIPE_DELTAS) == {"ARB-07"}
    for scenario_id, targets in M2_SCENARIO_TO_TARGETS.items():
        assert targets, scenario_id
        for target in targets:
            _assert_target_exists(target)
        recipes = M2_SCENARIO_TO_RECIPES[scenario_id]
        assert recipes.primary in M2_RECIPES
        assert recipes.primary not in recipes.secondary
        assert recipes.secondary <= M2_RECIPES


def test_s03_predicate_registry_is_the_exact_frozen_map() -> None:
    assert set(M2_PREDICATE_TO_SCENARIOS) == {
        "NU",
        "VS",
        "DG",
        "LS",
        "DV",
        "VH",
        "BA",
        "AM",
        "RL",
        "AL",
        "ML",
        "OS",
        "RS",
        "PO",
        "OF",
        "SO",
        "OC",
        "RC",
        "RF",
        "RA",
        "ES",
    }
    assert len(M2_PREDICATE_TO_SCENARIOS) == 21
    for predicate, scenario_ids in M2_PREDICATE_TO_SCENARIOS.items():
        assert scenario_ids, predicate
        assert scenario_ids <= M2_CONCURRENCY_SCENARIOS
        assert frozenset().union(
            *(M2_SCENARIO_TO_TARGETS[item] for item in scenario_ids)
        )


def test_s03_primary_bundles_are_implemented_with_exact_scenario_membership() -> None:
    assert set(S03_BUNDLE_SCENARIOS) == {
        "M2-VER-15",
        "M2-VER-16",
        "M2-VER-17",
        "M2-VER-18",
        "M2-VER-19",
    }
    for bundle_id, scenario_ids in S03_BUNDLE_SCENARIOS.items():
        evidence = M2_EVIDENCE_TO_TARGETS[bundle_id]
        assert evidence.state == "IMPLEMENTED"
        assert evidence.targets == frozenset().union(
            *(M2_SCENARIO_TO_TARGETS[item] for item in scenario_ids)
        )
        for target in evidence.targets:
            _assert_target_exists(target)


def test_s08_primary_bundle_ownership_is_exact() -> None:
    assert set(M2_PRIMARY_BUNDLE_OWNER) == M2_EVIDENCE_BUNDLES
    assert set(M2_PRIMARY_BUNDLE_OWNER.values()) == {
        f"M2-S{number:02d}" for number in range(1, 9)
    }
    expected_counts = {
        "M2-S01": 10,
        "M2-S02": 6,
        "M2-S03": 5,
        "M2-S04": 2,
        "M2-S05": 1,
        "M2-S06": 3,
        "M2-S07": 3,
        "M2-S08": 2,
    }
    assert {
        owner: tuple(M2_PRIMARY_BUNDLE_OWNER.values()).count(owner)
        for owner in sorted(set(M2_PRIMARY_BUNDLE_OWNER.values()))
    } == expected_counts
    assert set(S08_PRIMARY_BUNDLE_TARGETS) == {"M2-VER-31", "M2-VER-32"}
    assert all(S08_PRIMARY_BUNDLE_TARGETS.values())


def test_s08_outcome_owner_acceptance_evidence_target_chain_is_complete() -> None:
    assert set(M2_OUTCOME_TO_ARCHITECTURE_OWNERS) == M2_OUTCOMES
    assert set(M2_ARCHITECTURE_OWNER_TO_OUTCOMES) == M2_ARCHITECTURE_OWNERS
    expected_inverse = {
        owner: frozenset(
            outcome
            for outcome, owners in M2_OUTCOME_TO_ARCHITECTURE_OWNERS.items()
            if owner in owners
        )
        for owner in M2_ARCHITECTURE_OWNERS
    }
    assert M2_ARCHITECTURE_OWNER_TO_OUTCOMES == expected_inverse
    assert all(expected_inverse.values())

    for owner in M2_ARCHITECTURE_OWNERS:
        text = Path(owner).read_text()
        assert "FINAL / FROZEN" in text, owner
        assert Path(owner).is_file()
    for outcome in M2_OUTCOMES:
        owners = M2_OUTCOME_TO_ARCHITECTURE_OWNERS[outcome]
        acceptance = M2_OUTCOME_TO_ACCEPTANCE[outcome]
        assert owners and owners <= M2_ARCHITECTURE_OWNERS
        assert acceptance and acceptance <= M2_ACCEPTANCE_CRITERIA
        for criterion in acceptance:
            bundle = M2_ACCEPTANCE_TO_EVIDENCE[criterion]
            evidence = M2_EVIDENCE_TO_TARGETS[bundle]
            assert evidence.state == "IMPLEMENTED"
            assert evidence.targets
            for target in evidence.targets:
                _assert_target_exists(target)


def test_s08_capability_portfolio_and_trace_are_exact() -> None:
    assert M2_CAPABILITY_PORTFOLIO == {
        "in_scope": frozenset(
            {
                "Versioned Relationship property model",
                "Core Health API",
                "NETAUTO CLI",
                "Runtime configuration and production deployment",
            }
        ),
        "cross_cutting_foundation": frozenset(
            {"First durable Alembic kernel baseline"}
        ),
        "explicitly_outside_m2": frozenset(
            {"Logging operational review / introduction"}
        ),
    }
    traced = (
        M2_CAPABILITY_PORTFOLIO["in_scope"]
        | M2_CAPABILITY_PORTFOLIO["cross_cutting_foundation"]
    )
    assert set(M2_CAPABILITY_TRACE) == traced
    contract = Path("docs/milestones/M2/contract.md").read_text()
    for capability, trace in M2_CAPABILITY_TRACE.items():
        assert capability in contract
        assert trace.objectives
        assert trace.outcomes <= M2_OUTCOMES
        assert trace.acceptance <= M2_ACCEPTANCE_CRITERIA
        assert trace.evidence == frozenset(
            M2_ACCEPTANCE_TO_EVIDENCE[item] for item in trace.acceptance
        )
        assert trace.owners <= M2_ARCHITECTURE_OWNERS
        assert trace.outcomes and trace.acceptance and trace.evidence and trace.owners
        assert all(item in contract for item in trace.objectives)

    assert M2_CONTRACT_QUALITY_GATES == {
        f"M2-CQG-{number:02d}" for number in range(1, 11)
    }
    assert set(M2_CONTRACT_QUALITY_GATE_TO_TARGETS) == M2_CONTRACT_QUALITY_GATES
    for targets in M2_CONTRACT_QUALITY_GATE_TO_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)


def test_s08_dependency_graph_and_authority_direction_are_closed() -> None:
    graph: dict[str, frozenset[str]] = {
        "unique_alembic_head": frozenset({"startup_schema_guard", "explicit_alembic"}),
        "explicit_alembic": frozenset({"startup_schema_guard"}),
        "startup_schema_guard": frozenset({"http_serving"}),
        "http_serving": frozenset({"business_api", "health"}),
        "business_api": frozenset({"cli_remote"}),
        "health": frozenset({"cli_connection", "readiness_verification"}),
        "cli_remote": frozenset(),
        "cli_connection": frozenset(),
        "readiness_verification": frozenset(),
    }
    permanent: set[str] = set()
    temporary: set[str] = set()

    def visit(node: str) -> None:
        assert node not in temporary, node
        if node in permanent:
            return
        temporary.add(node)
        for child in graph[node]:
            visit(child)
        temporary.remove(node)
        permanent.add(node)

    for node in graph:
        visit(node)
    assert permanent == set(graph)

    contract = Path("docs/milestones/M2/contract.md").read_text()
    assert (
        "No HTTP endpoint enters serving and no migration is executed automatically."
        in contract
    )
    assert "Deployment requires explicit schema realization" in contract
    assert "The server never depends on the CLI." in contract
    assert set(M2_AUTHORITY_COMPOSITION) == {
        "delivered_as_is",
        "m2_contract",
        "m2_architecture",
        "technology",
        "operations",
        "non_authoritative_history",
    }
    assert M2_ARCHITECTURE_OWNERS <= M2_AUTHORITY_COMPOSITION["m2_architecture"]
    assert all(Path(path).is_file() for path in M2_ARCHITECTURE_OWNERS)
    assert not any("/wip/" in path for path in M2_ARCHITECTURE_OWNERS)


def test_s08_deferred_choices_do_not_change_observable_outcomes() -> None:
    contract = Path("docs/milestones/M2/contract.md").read_text()
    assert (
        "may determine how, but not whether or with what observable result" in contract
    )
    assert (
        "No other observable divergence from the delivered AS-IS is authorized"
        in contract
    )
    assert "Logging operational review / introduction" in contract
    assert "Logging remains a candidate capability for a future milestone" in contract


def test_s08_frozen_vocabulary_and_identifier_hygiene_are_exact() -> None:
    contract = Path("docs/milestones/M2/contract.md").read_text()
    verification = Path("docs/milestones/M2/architecture/verification.md").read_text()
    for identifiers, text in (
        (M2_OUTCOMES, contract),
        (M2_ACCEPTANCE_CRITERIA, contract),
        (M2_CONTRACT_QUALITY_GATES, contract),
        (M2_EVIDENCE_BUNDLES, verification),
    ):
        assert all(identifier in text for identifier in identifiers)
    for distinct_pair in (
        ("readiness", "schema compatibility"),
        ("event row", "event set"),
        ("exact version", "default policy"),
    ):
        assert all(term in contract.lower() for term in distinct_pair)


def test_s08_freeze_and_formal_reopen_rules_remain_explicit() -> None:
    contract = Path("docs/milestones/M2/contract.md").read_text()
    architecture = Path("docs/milestones/M2/architecture/README.md").read_text()
    steps = Path("docs/milestones/M2/steps.md").read_text()
    assert "This contract is `FINAL / FROZEN`." in contract
    assert "Open contract points\n\nNone." in contract
    assert "formal contract reopening" in contract.lower()
    assert architecture.startswith(
        "# M2 Architecture\n\n**Architecture set status:** FINAL / FROZEN"
    )
    assert "no relevant open, contradictory or partially reopened" in architecture
    assert "FINAL / FROZEN" in steps


def test_s08_all_bundles_are_implemented_nonempty_and_resolvable() -> None:
    assert set(M2_EVIDENCE_TO_TARGETS) == M2_EVIDENCE_BUNDLES
    assert all(
        evidence.state == "IMPLEMENTED" and evidence.targets
        for evidence in M2_EVIDENCE_TO_TARGETS.values()
    )
    assert set(M2_NEGATIVE_SURFACE_CONTRACT) == set(_NEGATIVE_CATEGORY_TARGET)
    assert len(M2_NEGATIVE_SURFACE_TO_TARGETS) == sum(
        len(entries) for entries in M2_NEGATIVE_SURFACE_CONTRACT.values()
    )
    assert all(M2_NEGATIVE_SURFACE_TO_TARGETS.values())
    for targets in (
        *S08_PRIMARY_BUNDLE_TARGETS.values(),
        *M2_NEGATIVE_SURFACE_TO_TARGETS.values(),
    ):
        for target in targets:
            _assert_target_exists(target)
