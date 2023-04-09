from dataclasses import dataclass
from typing import Any, List, Mapping, NamedTuple, Optional, Type, Union

from typing_extensions import TypeAlias

from openapify.core.openapi.models import Example, Parameter, SecurityScheme

SecurityRequirement: TypeAlias = Mapping[str, "SecurityScheme"]


@dataclass
class RouteDef:
    path: str
    method: str
    handler: Any
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[List[Parameter]] = None
    tags: Optional[List[str]] = None


class Body(NamedTuple):
    value_type: Type
    media_type: str = "application/json"
    required: Optional[bool] = None
    description: Optional[str] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Union[Example, Any]]] = None


@dataclass
class Header:
    description: Optional[str] = None
    required: Optional[bool] = None
    value_type: Type = str
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
    value_type: Type = str
    default: Optional[Any] = None
    required: Optional[bool] = None
    description: Optional[str] = None
    deprecated: Optional[bool] = None
    allowEmptyValue: Optional[bool] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Union[Example, Any]]] = None
