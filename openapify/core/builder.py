from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    overload,
)

import apispec
from typing_extensions import TypeAlias

from openapify.core.const import (
    DEFAULT_OPENAPI_VERSION,
    DEFAULT_SPEC_TITLE,
    DEFAULT_SPEC_VERSION,
)
from openapify.core.document import OpenAPIDocument
from openapify.core.jsonschema import ComponentType, build_json_schema
from openapify.core.models import (
    Body,
    Cookie,
    Header,
    QueryParam,
    RouteDef,
    SecurityRequirement,
)
from openapify.core.openapi import models as openapi

ComponentID: TypeAlias = str


METHOD_ORDER = [
    "connect",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "trace",
]


def _merge_parameters(
    old_parameters: Sequence[openapi.Parameter], new_parameters: Dict[str, str]
) -> Sequence[openapi.Parameter]:
    for parameter in old_parameters or []:
        parameter_description = new_parameters.get(parameter.name)
        if parameter_description:
            parameter.description = parameter_description
    return old_parameters


class OpenAPISpecBuilder:
    def __init__(
        self,
        spec: Optional[apispec.APISpec] = None,
        title: str = DEFAULT_SPEC_TITLE,
        version: str = DEFAULT_SPEC_VERSION,
        openapi_version: str = DEFAULT_OPENAPI_VERSION,
        plugins: Sequence[apispec.BasePlugin] = (),
        servers: Optional[List[Union[str, openapi.Server]]] = None,
        security_schemes: Optional[Dict[str, openapi.SecurityScheme]] = None,
        **options: Any,
    ):
        if spec is None:
            spec = OpenAPIDocument(
                title=title,
                version=version,
                openapi_version=openapi_version,
                plugins=plugins,
                servers=servers,
                security_schemes=security_schemes,
                **options,
            )
        self.spec = spec

    def feed_routes(self, routes: Iterable[RouteDef]) -> None:
        for route in sorted(
            routes,
            key=lambda r: (r.path, METHOD_ORDER.index(r.method.lower())),
        ):
            self._process_route(route)

    def _process_route(self, route: RouteDef) -> None:
        method = route.method.lower()
        meta = getattr(route.handler, "__openapify__", [])
        code_responses = {}
        summary = route.summary
        description = route.description
        tags = route.tags.copy() if route.tags else []
        deprecated = None
        external_docs = None
        security = None
        parameters = route.parameters.copy() if route.parameters else []
        request_body: Optional[openapi.RequestBody] = None
        for args_type, args in meta:
            if args_type == "request":
                body = args.get("body")
                if isinstance(body, Body):
                    body_value_type = body.value_type
                    media_type = body.media_type
                    body_required = body.required
                    body_description = body.description
                    body_example = body.example
                    body_examples = body.examples
                else:
                    body_value_type = body
                    media_type = args.get("media_type")
                    body_required = args.get("body_required")
                    body_description = args.get("body_description")
                    body_example = args.get("body_example")
                    body_examples = args.get("body_examples")
                if body is not None:
                    request_body = self._build_request_body(
                        value_type=body_value_type,
                        media_type=media_type,
                        required=body_required,
                        description=body_description,
                        example=body_example,
                        examples=body_examples,
                    )
                query_params = args.get("query_params")
                if query_params:
                    parameters.extend(self._build_query_params(query_params))
                headers = args.get("headers")
                if headers:
                    parameters.extend(self._build_request_headers(headers))
                cookies = args.get("cookies")
                if cookies:
                    parameters.extend(self._build_cookies(cookies))

            elif args_type == "response":
                args = args.copy()
                http_code = args.pop("http_code")
                body_value_type = args.pop("body")
                if body_value_type is not None:
                    code_responses[http_code] = self._build_response(
                        body=body_value_type, **args
                    )
            elif args_type == "path_docs":
                summary = args.get("summary")
                description = args.get("description")
                tags.extend(args.get("tags") or [])
                # _merge_parameters(parameters, args.get("parameters") or {})
                external_docs = self._build_external_docs(
                    args.get("external_docs")
                )
                deprecated = args.pop("deprecated")
            elif args_type == "security_requirements":
                security = self._build_security_requirements(
                    args.get("requirements")
                )
        self.spec.path(
            route.path,
            operations={
                method: openapi.Operation(
                    summary=summary,
                    description=description,
                    requestBody=request_body,
                    responses=openapi.Responses(codes=code_responses),
                    deprecated=deprecated,
                    tags=tags or None,
                    parameters=parameters or None,
                    externalDocs=external_docs,
                    security=security,
                ).to_dict()
            },
            # https://github.com/swagger-api/swagger-ui/issues/5653
            # summary=summary,
            # description=description,
            # parameters=[param.to_dict() for param in route.parameters or []],
        )

    def _build_query_params(
        self, query_params: Dict[str, Union[Type, QueryParam]]
    ) -> Sequence[openapi.Parameter]:
        result = []
        for name, param in query_params.items():
            if not isinstance(param, QueryParam):
                param = QueryParam(param)
            parameter_schema = build_json_schema(
                param.value_type, self.spec, ComponentType.PARAMETER
            )
            if param.default is not None:
                parameter_schema["default"] = param.default
            result.append(
                openapi.Parameter(
                    name=name,
                    location=openapi.ParameterLocation.QUERY,
                    description=param.description,
                    required=param.required,
                    deprecated=param.deprecated,
                    allowEmptyValue=param.allowEmptyValue,
                    schema=parameter_schema,
                    example=param.example,
                    examples=self._build_examples(param.examples),
                )
            )
        return result

    def _build_request_headers(
        self, headers: Dict[str, Union[str, Header]]
    ) -> Sequence[openapi.Parameter]:
        result = []
        for name, header in headers.items():
            if not isinstance(header, Header):
                header = Header(description=header)
            parameter_schema = build_json_schema(
                header.value_type, self.spec, ComponentType.PARAMETER
            )
            result.append(
                openapi.Parameter(
                    name=name,
                    location=openapi.ParameterLocation.HEADER,
                    description=header.description,
                    required=header.required,
                    deprecated=header.deprecated,
                    allowEmptyValue=header.allowEmptyValue,
                    schema=parameter_schema,
                    example=header.example,
                    examples=self._build_examples(header.examples),
                )
            )
        return result

    def _build_response_headers(
        self, headers: Dict[str, Union[str, Header]]
    ) -> Sequence[openapi.Header]:
        result = []
        for name, header in headers.items():
            if not isinstance(header, Header):
                header = Header(description=header)
            header_schema = build_json_schema(
                header.value_type, self.spec, ComponentType.HEADER
            )
            result.append(
                openapi.Header(
                    schema=header_schema,
                    description=header.description,
                    required=header.required,
                    deprecated=header.deprecated,
                    allowEmptyValue=header.allowEmptyValue,
                    example=header.example,
                    examples=self._build_examples(header.examples),
                )
            )
        return result

    def _build_cookies(
        self, cookies: Dict[str, Union[str, Cookie]]
    ) -> Sequence[openapi.Parameter]:
        result = []
        for name, cookie in cookies.items():
            if not isinstance(cookie, Cookie):
                cookie = Cookie(cookie)
            parameter_schema = build_json_schema(
                cookie.value_type, self.spec, ComponentType.PARAMETER
            )
            result.append(
                openapi.Parameter(
                    name=name,
                    location=openapi.ParameterLocation.QUERY,
                    description=cookie.description,
                    required=cookie.required,
                    deprecated=cookie.deprecated,
                    allowEmptyValue=cookie.allowEmptyValue,
                    schema=parameter_schema,
                    example=cookie.example,
                    examples=self._build_examples(cookie.examples),
                )
            )
        return result

    def _build_request_body(
        self,
        value_type: Type,
        media_type: str = "application/json",
        required: Optional[bool] = None,
        description: Optional[str] = None,
        example: Optional[Any] = None,
        examples: Optional[Mapping[str, Union[openapi.Example, Any]]] = None,
    ) -> openapi.RequestBody:
        return openapi.RequestBody(
            description=description,
            content={
                media_type: openapi.MediaType(
                    schema=build_json_schema(value_type, self.spec),
                    example=example,
                    examples=self._build_examples(examples),
                )
            },
            required=required,
        )

    def _build_response(
        self,
        body: Type,
        media_type: str = "application/json",
        description: Optional[str] = None,
        headers: Optional[Dict[str, Union[str, Header]]] = None,
        example: Optional[Any] = None,
        examples: Optional[Dict[str, Union[openapi.Example, Any]]] = None,
    ) -> openapi.Response:
        header_objects = {}
        if headers:
            header_objects = self._build_response_headers(headers)
        return openapi.Response(
            description=description,
            headers=header_objects or None,
            content={
                media_type: openapi.MediaType(
                    schema=build_json_schema(body, self.spec),
                    example=example,
                    examples=self._build_examples(examples),
                ),
            },
        )

    @staticmethod
    def _build_external_docs(
        data: Union[str, Tuple[str, str]]
    ) -> Optional[openapi.ExternalDocumentation]:
        if not data:
            return None
        elif isinstance(data, tuple):
            return openapi.ExternalDocumentation(*data)
        else:
            return openapi.ExternalDocumentation(data)

    def _build_security_requirements(
        self,
        security: Optional[
            Union[SecurityRequirement, List[SecurityRequirement]]
        ] = None,
    ) -> Optional[List[Mapping[str, List[str]]]]:
        if security is None:
            return None
        result: List[Mapping[str, List[str]]] = []
        if isinstance(security, dict):
            security = [security]
        for requirement in security:
            for name, scheme in requirement.items():  # type: ignore
                if name not in self.spec.components.security_schemes:
                    self.spec.components.security_scheme(
                        name, scheme.to_dict()
                    )
                # TODO: include list of scopes for oauth2 or openIdConnect
                result.append({name: []})
        return result

    @staticmethod
    def _build_examples(
        examples: Optional[Mapping[str, Union[openapi.Example, Any]]] = None,
    ) -> Optional[Mapping[str, openapi.Example]]:
        if examples is None:
            return None
        result = {}
        for key, value in examples.items():
            if not isinstance(value, openapi.Example):
                result[key] = openapi.Example(value)
        return result


@overload
def build_spec(
    routes: Iterable[RouteDef], spec: apispec.APISpec
) -> apispec.APISpec:
    ...


@overload
def build_spec(
    routes: Iterable[RouteDef],
    *,
    title: str = DEFAULT_SPEC_TITLE,
    version: str = DEFAULT_SPEC_VERSION,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Sequence[apispec.BasePlugin] = (),
    servers: Optional[List[Union[str, openapi.Server]]] = None,
    security_schemes: Optional[Dict[str, openapi.SecurityScheme]] = None,
    **options: Any,
) -> apispec.APISpec:
    ...


def build_spec(
    routes: Iterable[RouteDef],
    spec: Optional[apispec.APISpec] = None,
    *,
    title: str = DEFAULT_SPEC_TITLE,
    version: str = DEFAULT_SPEC_VERSION,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Sequence[apispec.BasePlugin] = (),
    servers: Optional[List[Union[str, openapi.Server]]] = None,
    security_schemes: Optional[Dict[str, openapi.SecurityScheme]] = None,
    **options: Any,
) -> apispec.APISpec:
    builder = OpenAPISpecBuilder(
        spec=spec,
        title=title,
        version=version,
        openapi_version=openapi_version,
        plugins=plugins,
        servers=servers,
        security_schemes=security_schemes,
        **options,
    )
    builder.feed_routes(routes)
    return builder.spec
