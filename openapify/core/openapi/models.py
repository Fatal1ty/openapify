from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Union

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig
from typing_extensions import Literal, TypeAlias

HttpCode: TypeAlias = Union[str, int]
Schema: TypeAlias = Mapping[str, Any]


@dataclass
class Object(DataClassDictMixin):
    class Config(BaseConfig):
        omit_none = True


@dataclass
class ServerVariable(Object):
    default: str
    enum: Optional[List[str]] = None
    description: Optional[str] = None


@dataclass
class Server(Object):
    url: str
    description: Optional[str] = None
    variables: Optional[Mapping[str, ServerVariable]] = None


@dataclass
class Example(Object):
    value: Optional[Any] = None
    summary: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Header(Object):
    schema: Schema
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    allowEmptyValue: Optional[bool] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Example]] = None


@dataclass
class MediaType(Object):
    schema: Optional[Schema] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Example]] = None
    encoding: Optional[str] = None


@dataclass
class RequestBody(Object):
    description: Optional[str] = None
    content: Optional[Dict[str, MediaType]] = None
    required: Optional[bool] = None


@dataclass
class Response(Object):
    description: Optional[str] = None
    headers: Optional[Mapping[str, Header]] = None
    content: Optional[Dict[str, MediaType]] = None


@dataclass
class Responses(Object):
    default: Optional[Response] = None
    codes: Optional[Dict[HttpCode, Response]] = None

    def __post_serialize__(self, d: Dict[Any, Any]) -> Dict[Any, Any]:
        codes = d.pop("codes", None)
        if codes:
            d.update(codes)
        return d


class ParameterLocation(Enum):
    QUERY = "query"
    HEADER = "header"
    PATH = "path"
    COOKIE = "cookie"


class ParameterStyle(Enum):
    SIMPLE = "simple"
    FORM = "form"


@dataclass
class Parameter(Object):
    name: str
    location: ParameterLocation
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    allowEmptyValue: Optional[bool] = None
    style: Optional[ParameterStyle] = None
    explode: Optional[bool] = None
    schema: Optional[Schema] = None
    example: Optional[Any] = None
    examples: Optional[Mapping[str, Example]] = None
    content: Optional[Mapping[str, MediaType]] = None

    class Config(Object.Config):
        serialize_by_alias = True
        aliases = {"location": "in"}


@dataclass
class ExternalDocumentation(Object):
    url: str
    description: Optional[str] = None


class SecuritySchemeType(Enum):
    API_KEY = "apiKey"
    HTTP = "http"
    MUTUAL_TLS = "mutualTLS"
    OAUTH2 = "oauth2"
    OPEN_ID_CONNECT = "openIdConnect"


class SecuritySchemeAPIKeyLocation(Enum):
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


@dataclass(unsafe_hash=True)
class SecurityScheme(Object):
    type: SecuritySchemeType


@dataclass
class APIKeySecurityScheme(SecurityScheme):
    name: Optional[str] = None
    location: SecuritySchemeAPIKeyLocation = SecuritySchemeAPIKeyLocation.QUERY
    type: Literal[SecuritySchemeType.API_KEY] = SecuritySchemeType.API_KEY
    description: Optional[str] = None

    class Config(Object.Config):
        serialize_by_alias = True
        aliases = {"location": "in"}


@dataclass
class HTTPSecurityScheme(SecurityScheme):
    scheme: str = "basic"
    type: Literal[SecuritySchemeType.HTTP] = SecuritySchemeType.HTTP
    bearerFormat: Optional[str] = None
    description: Optional[str] = None


@dataclass
class OAuthFlows(Object):
    pass


@dataclass
class OAuth2SecurityScheme(SecurityScheme):
    flows: Optional[OAuthFlows] = None
    type: Literal[SecuritySchemeType.OAUTH2] = SecuritySchemeType.OAUTH2
    description: Optional[str] = None


@dataclass
class OpenIDConnectSecurityScheme(SecurityScheme):
    openIdConnectUrl: str = ""
    type: Literal[SecuritySchemeType.OPEN_ID_CONNECT] = (
        SecuritySchemeType.OPEN_ID_CONNECT
    )
    description: Optional[str] = None


@dataclass
class Operation(Object):
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None
    operationId: Optional[str] = None
    parameters: Optional[List[Parameter]] = None
    requestBody: Optional[RequestBody] = None
    responses: Optional[Responses] = None
    deprecated: Optional[bool] = None
    security: Optional[List[Mapping[str, List[str]]]] = None


@dataclass
class PathItem(Object):
    # TODO: Do we need this class?
    ref: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    get: Optional[Operation] = None
    put: Optional[Operation] = None
    post: Optional[Operation] = None
    delete: Optional[Operation] = None
    options: Optional[Operation] = None
    head: Optional[Operation] = None
    patch: Optional[Operation] = None
    trace: Optional[Operation] = None
    parameters: Optional[List[Parameter]] = None
