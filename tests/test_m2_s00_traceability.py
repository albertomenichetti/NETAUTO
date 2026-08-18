"""Machine-checkable M2-S00 coverage of the 32 delivered mutation paths."""

import ast
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import cast

import netauto.application.datatypes as datatype_application
import netauto.application.objects as object_application
import netauto.application.objecttemplates as object_template_application
import netauto.application.relationshipdefinitions as definition_application
from netauto.application.datatypes import DataTypeService
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import ObjectTemplateService
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import RelationshipService
from netauto.persistence.locking import AdvisoryGate

type Mutation = Callable[..., object]
type EvidenceRegistry = dict[str, dict[str, frozenset[str]]]


DELIVERED_MUTATION_PLANS: dict[str, tuple[Mutation, AdvisoryGate | None]] = {
    "DT.C": (DataTypeService.create, None),
    "DT.CN": (DataTypeService.create_next, None),
    "DT.R": (DataTypeService.revise, None),
    "DT.P": (DataTypeService.publish, None),
    "DT.SD": (DataTypeService.set_default, None),
    "DT.CD": (DataTypeService.clear_default, None),
    "DT.D": (DataTypeService.deprecate, None),
    "DT.DD": (DataTypeService.delete_draft, None),
    "DT.DL": (DataTypeService.delete_lineage, AdvisoryGate.MODEL_ROOT_DELETE_GATE),
    "DT.DESC": (DataTypeService.set_description, None),
    "OT.C": (ObjectTemplateService.create, None),
    "OT.CN": (ObjectTemplateService.create_next, None),
    "OT.R": (ObjectTemplateService.revise, None),
    "OT.P": (ObjectTemplateService.publish, None),
    "OT.SD": (ObjectTemplateService.set_default, None),
    "OT.CD": (ObjectTemplateService.clear_default, None),
    "OT.D": (ObjectTemplateService.deprecate, None),
    "OT.DD": (ObjectTemplateService.delete_draft, None),
    "OT.DL": (
        ObjectTemplateService.delete_lineage,
        AdvisoryGate.MODEL_ROOT_DELETE_GATE,
    ),
    "OT.DESC": (ObjectTemplateService.set_description, None),
    "OBJ.C": (ObjectService.create, None),
    "OBJ.RN": (ObjectService.rename, None),
    "OBJ.DC": (ObjectService.data_change, None),
    "OBJ.SC": (ObjectService.schema_change, None),
    "OBJ.A": (ObjectService.attach, AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE),
    "OBJ.DET": (ObjectService.detach, None),
    "OBJ.DEL": (ObjectService.delete, None),
    "RD.C": (
        cast(Mutation, RelationshipDefinitionService.__dict__["_create"]),
        AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
    ),
    "RD.RN": (
        cast(Mutation, RelationshipDefinitionService.__dict__["_rename"]),
        AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
    ),
    "RD.DL": (
        RelationshipDefinitionService.delete,
        AdvisoryGate.MODEL_ROOT_DELETE_GATE,
    ),
    "REL.C": (RelationshipService.create, None),
    "REL.DEL": (RelationshipService.delete, None),
}


PLAN_EVIDENCE_TARGETS: EvidenceRegistry = {
    "PLAN-01": {
        "pure_static": frozenset(
            {"tests/test_m2_locking.py::test_plan_01_lock_sql_compilation"}
        ),
        "postgresql": frozenset(
            {
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_01_real_postgresql_lock_modes_and_missing_keys"
            }
        ),
        "concurrency": frozenset(),
    },
    "PLAN-02": {
        "pure_static": frozenset(
            {
                "tests/test_m2_locking.py::"
                "test_plan_02_coalescence_and_canonical_sorting",
                "tests/test_m2_locking.py::"
                "test_plan_02_arbitrary_input_permutations_are_canonical",
                "tests/test_m2_locking.py::"
                "test_plan_02_non_template_plans_do_not_load_ancestry",
            }
        ),
        "postgresql": frozenset(
            {
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_02_targeted_ancestry_is_one_query_and_deduplicates",
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_02_missing_template_header_is_plannable",
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_02_corrupt_template_ancestry_is_rejected",
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_02_non_template_mutations_skip_planner_ancestry",
            }
        ),
        "concurrency": frozenset(),
    },
    "PLAN-03": {
        "pure_static": frozenset(
            {
                "tests/test_m2_locking.py::"
                "test_plan_03_stale_and_post_dml_expansion_are_distinct"
            }
        ),
        "postgresql": frozenset(
            {
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_03_real_application_stale_plan_uses_fresh_uow"
            }
        ),
        "concurrency": frozenset(
            {
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_03_real_application_stale_plan_uses_fresh_uow"
            }
        ),
    },
    "PLAN-04": {
        "pure_static": frozenset(
            {
                "tests/test_m2_locking.py::"
                "test_plan_04_finite_postgresql_failure_classifier"
            }
        ),
        "postgresql": frozenset(
            {
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_04_real_constraint_failures_classify_after_rollback"
            }
        ),
        "concurrency": frozenset(),
    },
    "PLAN-05": {
        "pure_static": frozenset(
            {
                "tests/test_m2_locking.py::"
                "test_plan_05_exactly_four_fresh_uow_attempts",
                "tests/test_m2_locking.py::"
                "test_plan_05_does_not_retry_unapproved_failures",
            }
        ),
        "postgresql": frozenset(
            {
                "tests/test_relationship_semantic_concurrency.py::"
                "test_arb_07b_winner_disappears_before_fresh_convergence_read",
                "tests/test_relationship_semantic_concurrency.py::"
                "test_arb_07c_delete_blocks_after_collision_owner_lifetime_lock",
            }
        ),
        "concurrency": frozenset(
            {
                "tests/test_relationship_semantic_concurrency.py::"
                "test_arb_07b_winner_disappears_before_fresh_convergence_read",
                "tests/test_relationship_semantic_concurrency.py::"
                "test_arb_07c_delete_blocks_after_collision_owner_lifetime_lock",
            }
        ),
    },
    "PLAN-06": {
        "pure_static": frozenset(
            {
                "tests/test_m2_locking.py::test_plan_06_gate_and_phase_discipline",
                "tests/test_m2_locking.py::"
                "test_plan_06_gate_precedes_every_row_statement",
            }
        ),
        "postgresql": frozenset(
            {
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_06_real_gate_waiter_holds_no_planned_row_lock"
            }
        ),
        "concurrency": frozenset(
            {
                "tests/test_m2_locking_postgresql.py::"
                "test_plan_06_real_gate_waiter_holds_no_planned_row_lock"
            }
        ),
    },
}


def test_delivered_32_mutation_inventory_is_exact_and_centralized() -> None:
    assert len(DELIVERED_MUTATION_PLANS) == 32
    assert sum(name.startswith("DT.") for name in DELIVERED_MUTATION_PLANS) == 10
    assert sum(name.startswith("OT.") for name in DELIVERED_MUTATION_PLANS) == 10
    assert sum(name.startswith("OBJ.") for name in DELIVERED_MUTATION_PLANS) == 7
    assert sum(name.startswith("RD.") for name in DELIVERED_MUTATION_PLANS) == 3
    assert sum(name.startswith("REL.") for name in DELIVERED_MUTATION_PLANS) == 2

    for mutation, _ in DELIVERED_MUTATION_PLANS.values():
        source = inspect.getsource(mutation)
        assert "_acquire(" in source or "prepare_lock_plan(" in source
        assert "begin_dml()" in source
        assert "acquire_advisory_gate" not in source
        assert ".lock_" not in source
        assert ".admit_" not in source


def test_delivered_gate_ownership_is_exact() -> None:
    gated = {
        name: gate
        for name, (_, gate) in DELIVERED_MUTATION_PLANS.items()
        if gate is not None
    }
    assert gated == {
        "DT.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
        "OT.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
        "OBJ.A": AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE,
        "RD.C": AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
        "RD.RN": AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
        "RD.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
    }


def test_generic_acquire_helpers_use_only_central_planner_preparation() -> None:
    helpers = (
        datatype_application.__dict__["_acquire"],
        object_template_application.__dict__["_acquire"],
        object_application.__dict__["_acquire"],
        definition_application.__dict__["_acquire"],
    )
    for helper in helpers:
        source = inspect.getsource(helper)
        assert "prepare_lock_plan(" in source
        assert "lineage_parents(" not in source
        assert "LockPlan(" not in source


def test_plan_evidence_registry_is_exact_and_every_target_resolves() -> None:
    assert set(PLAN_EVIDENCE_TARGETS) == {
        "PLAN-01",
        "PLAN-02",
        "PLAN-03",
        "PLAN-04",
        "PLAN-05",
        "PLAN-06",
    }
    assert all(
        set(categories) == {"pure_static", "postgresql", "concurrency"}
        for categories in PLAN_EVIDENCE_TARGETS.values()
    )
    for plan_id, categories in PLAN_EVIDENCE_TARGETS.items():
        assert categories["pure_static"], plan_id
        assert categories["postgresql"], plan_id
        for targets in categories.values():
            for target in targets:
                path_text, separator, test_name = target.partition("::")
                assert separator and test_name.startswith("test_")
                path = Path(path_text)
                assert path.is_file(), target
                tree = ast.parse(path.read_text())
                collected_names = {
                    node.name
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name.startswith("test_")
                }
                assert test_name in collected_names, target
