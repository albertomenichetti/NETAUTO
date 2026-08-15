"""Shared strict HTTP request helpers for M1 core routes."""

import re
from collections.abc import Collection
from typing import Annotated

from fastapi import Depends, Path, Query, Request
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from netauto.failures import ApplicationFailure, FailureClass

PositiveInteger = Annotated[int, Field(strict=True, gt=0)]


def positive_decimal_integer(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]*", value) is None:
        raise ValueError("positive_decimal_integer_required")
    return int(value)


PathPositiveInteger = Annotated[int, BeforeValidator(positive_decimal_integer), Path()]
QueryPositiveInteger = Annotated[
    int, BeforeValidator(positive_decimal_integer), Query()
]
PageLimit = Annotated[int, BeforeValidator(positive_decimal_integer), Query(le=500)]


class StrictBody(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


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
