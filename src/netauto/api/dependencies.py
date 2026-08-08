"""FastAPI dependencies."""

from fastapi import Request

from netauto.application.datatype import DataTypeApplicationService


def get_datatype_service(request: Request) -> DataTypeApplicationService:
    return request.app.state.datatype_service
