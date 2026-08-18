"""Shared strict HTTP request helpers for M1 core routes."""

from collections.abc import Collection
from typing import Annotated

from fastapi import Depends, Path, Query, Request
from pydantic import BeforeValidator

from netauto.failures import ApplicationFailure, FailureClass
from netauto.transport.http.common import (
    positive_decimal_integer,
)

PathPositiveInteger = Annotated[int, BeforeValidator(positive_decimal_integer), Path()]
QueryPositiveInteger = Annotated[
    int, BeforeValidator(positive_decimal_integer), Query()
]
PageLimit = Annotated[int, BeforeValidator(positive_decimal_integer), Query(le=500)]


async def no_body(request: Request) -> None:
    if await request.body():
        raise ApplicationFailure(
            FailureClass.INVALID_REQUEST,
            "invalid_request",
            "This command does not accept a request body.",
        )


def validate_query(request: Request, allowed: Collection[str]) -> None:
    keys = set(request.query_params)
    if keys - set(allowed) or any(
        len(request.query_params.getlist(key)) != 1 for key in keys
    ):
        raise ApplicationFailure(
            FailureClass.INVALID_REQUEST,
            "invalid_request",
            "The request contains unknown or repeated query parameters.",
        )


NoBody = Annotated[None, Depends(no_body)]
