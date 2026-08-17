"""Machine-checkable M2-S00 coverage of the 32 delivered mutation paths."""

import inspect
from collections.abc import Callable
from typing import cast

from netauto.application.datatypes import DataTypeService
from netauto.application.objects import ObjectService
from netauto.application.objecttemplates import ObjectTemplateService
from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import RelationshipService
from netauto.persistence.locking import AdvisoryGate

type Mutation = Callable[..., object]


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


def test_delivered_32_mutation_inventory_is_exact_and_centralized() -> None:
    assert len(DELIVERED_MUTATION_PLANS) == 32
    assert sum(name.startswith("DT.") for name in DELIVERED_MUTATION_PLANS) == 10
    assert sum(name.startswith("OT.") for name in DELIVERED_MUTATION_PLANS) == 10
    assert sum(name.startswith("OBJ.") for name in DELIVERED_MUTATION_PLANS) == 7
    assert sum(name.startswith("RD.") for name in DELIVERED_MUTATION_PLANS) == 3
    assert sum(name.startswith("REL.") for name in DELIVERED_MUTATION_PLANS) == 2

    for mutation, _ in DELIVERED_MUTATION_PLANS.values():
        source = inspect.getsource(mutation)
        assert "_acquire(" in source or "LockPlan(" in source
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
