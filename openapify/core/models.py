from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Type, Union

from typing_extensions import TypeAlias

from openapify.core.openapi.models import (
    Example,
    ParameterStyle,
    SecurityScheme,
)

SecurityRequirement: TypeAlias = Mapping[str, "SecurityScheme"]

# https://github.com/python/mypy/issues/9773
TypeAnnotation: TypeAlias = Any


@dataclass
class PathParam:
    value_type: TypeAnnotation = str
    description: Optional[str] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Union[Example, Any]]] = None


@dataclass
class RouteDef:
    path: str
    method: str
    handler: Any
    summary: Optional[str] = None
    description: Optional[str] = None
    path_params: Optional[Dict[str, PathParam]] = None
    tags: Optional[List[str]] = None


@dataclass
class Body:
    value_type: TypeAnnotation
    media_type: Optional[str] = None
    required: Optional[bool] = None
    description: Optional[str] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Union[Example, Any]]] = None


@dataclass
class Header:
    description: Optional[str] = None
    required: Optional[bool] = None
    value_type: TypeAnnotation = str
    deprecated: Optional[bool] = None
    allowEmptyValue: Optional[bool] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Union[Example, Any]]] = None


@dataclass
class Cookie:
    description: Optional[str] = None
    required: Optional[bool] = None
    value_type: Type = str
    deprecated: Optional[bool] = None
    allowEmptyValue: Optional[bool] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Union[Example, Any]]] = None


@dataclass
class QueryParam:
    value_type: TypeAnnotation = str
    default: Optional[Any] = None
    required: Optional[bool] = None
    description: Optional[str] = None
    deprecated: Optional[bool] = None
    allowEmptyValue: Optional[bool] = None
    style: Optional[ParameterStyle] = None
    explode: Optional[bool] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Union[Example, Any]]] = None
