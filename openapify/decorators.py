from typing import (
    Any,
    Callable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from openapify.core.models import (
    Body,
    Cookie,
    Header,
    QueryParam,
    SecurityRequirement,
)
from openapify.core.openapi.models import Example, HttpCode, Parameter

__openapify__ = "__openapify__"


Handler = TypeVar("Handler")


@overload
def request_schema(
    body: Optional[Body] = None,
    *,
    query_params: Optional[Mapping[str, Union[Type, QueryParam]]] = None,
    headers: Optional[Mapping[str, Union[str, Header]]] = None,
    cookies: Optional[Mapping[str, Union[str, Cookie]]] = None,
) -> Callable[[Handler], Handler]:
    ...


@overload
def request_schema(
    body: Optional[Type] = None,
    *,
    media_type: str = "application/json",
    body_required: bool = False,
    body_description: Optional[str] = None,
    body_example: Optional[Any] = None,
    body_examples: Optional[Mapping[str, Union[Example, Any]]] = None,
    query_params: Optional[Mapping[str, Union[Type, QueryParam]]] = None,
    headers: Optional[Mapping[str, Union[str, Header]]] = None,
    cookies: Optional[Mapping[str, Union[str, Cookie]]] = None,
) -> Callable[[Handler], Handler]:
    ...


def request_schema(  # type: ignore[misc]
    body: Optional[Type] = None,
    *,
    media_type: str = "application/json",
    body_required: bool = False,
    body_description: Optional[str] = None,
    body_example: Optional[Any] = None,
    body_examples: Optional[Mapping[str, Union[Example, Any]]] = None,
    query_params: Optional[Mapping[str, Union[Type, QueryParam]]] = None,
    headers: Optional[Mapping[str, Union[str, Header]]] = None,
    cookies: Optional[Mapping[str, Union[str, Cookie]]] = None,
) -> Callable[[Handler], Handler]:
    def decorator(handler: Handler) -> Handler:
        meta = getattr(handler, __openapify__, [])
        if not meta:
            handler.__openapify__ = meta  # type: ignore[attr-defined]
        meta.append(
            (
                "request",
                {
                    "body": body,
                    "media_type": media_type,
                    "body_required": body_required,
                    "body_description": body_description,
                    "body_example": body_example,
                    "body_examples": body_examples,
                    "query_params": query_params,
                    "headers": headers,
                    "cookies": cookies,
                },
            ),
        )
        return handler

    return decorator


def response_schema(
    body: Optional[Type] = None,
    http_code: HttpCode = 200,
    media_type: str = "application/json",
    description: Optional[str] = None,
    # TODO: Generate a required description depending on http_code
    # https://spec.openapis.org/oas/v3.1.0#response-object
    headers: Optional[Mapping[str, Union[str, Header]]] = None,
    example: Optional[Any] = None,
    examples: Optional[Mapping[str, Union[Example, Any]]] = None,
) -> Callable[[Handler], Handler]:
    def decorator(handler: Handler) -> Handler:
        meta = getattr(handler, __openapify__, [])
        if not meta:
            handler.__openapify__ = meta  # type: ignore[attr-defined]
        meta.append(
            (
                "response",
                {
                    "body": body,
                    "http_code": http_code,
                    "media_type": media_type,
                    "description": description,
                    "headers": headers,
                    "example": example,
                    "examples": examples,
                },
            ),
        )
        return handler

    return decorator


def path_docs(
    summary: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    # parameters: Optional[Mapping[str, Union[str, Parameter]]] = None,
    external_docs: Optional[Union[str, Tuple[str, str]]] = None,
    deprecated: Optional[bool] = None,
) -> Callable[[Handler], Handler]:
    def decorator(handler: Handler) -> Handler:
        meta = getattr(handler, __openapify__, [])
        if not meta:
            handler.__openapify__ = meta  # type: ignore[attr-defined]
        meta.append(
            (
                "path_docs",
                {
                    "summary": summary,
                    "description": description,
                    "tags": tags,
                    # "parameters": parameters,
                    "external_docs": external_docs,
                    "deprecated": deprecated,
                },
            ),
        )
        return handler

    return decorator


def security_requirements(
    requirements: Optional[
        Union[SecurityRequirement, List[SecurityRequirement]]
    ] = None,
) -> Callable[[Handler], Handler]:
    def decorator(handler: Handler) -> Handler:
        meta = getattr(handler, __openapify__, [])
        if not meta:
            handler.__openapify__ = meta  # type: ignore[attr-defined]
        meta.append(("security_requirements", {"requirements": requirements}))
        return handler

    return decorator
