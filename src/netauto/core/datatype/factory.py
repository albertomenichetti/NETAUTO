"""Factory for creating custom datatype domain objects."""

from collections.abc import Iterable
from uuid import uuid4

from netauto.core.datatype.constraints import Constraint
from netauto.core.datatype.exceptions import ReservedDataTypeNamespace
from netauto.core.datatype.models import DataType, DataTypeVersion, DataTypeVersionStatus
from netauto.core.datatype.registry import PrimitiveTypeRegistry


class DataTypeFactory:
    """Create custom datatypes and their initial draft version."""

    def __init__(self) -> None:
        self._primitive_registry = PrimitiveTypeRegistry()

    def create(
        self,
        *,
        namespace: str,
        name: str,
        description: str | None,
        base_type: str,
        constraints: Iterable[Constraint] = (),
    ) -> tuple[DataType, DataTypeVersion]:
        if namespace == "core":
            raise ReservedDataTypeNamespace("The 'core' namespace is reserved.")

        datatype = DataType(
            id=uuid4(),
            namespace=namespace,
            name=name,
            description=description,
        )
        primitive_type = self._primitive_registry.get(base_type)
        version = DataTypeVersion(
            datatype_id=datatype.id,
            version=1,
            status=DataTypeVersionStatus.DRAFT,
            base_type=primitive_type,
            constraints=tuple(constraints),
        )
        return datatype, version
