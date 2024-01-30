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

from openapify.core.base_plugins import (
    BaseSchemaPlugin,
    BodyBinaryPlugin,
    GuessMediaTypePlugin,
)
from openapify.core.const import (
    DEFAULT_OPENAPI_VERSION,
    DEFAULT_SPEC_TITLE,
    DEFAULT_SPEC_VERSION,
    RESPONSE_DESCRIPTIONS,
)
from openapify.core.document import OpenAPIDocument
from openapify.core.models import (
    Body,
    Cookie,
    Header,
    QueryParam,
    RouteDef,
    SecurityRequirement,
    TypeAnnotation,
)
from openapify.core.openapi import models as openapi
from openapify.plugin import BasePlugin

BASE_PLUGINS = (BodyBinaryPlugin(), GuessMediaTypePlugin(), BaseSchemaPlugin())


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


def default_response_description(http_code: str) -> str:
    result = RESPONSE_DESCRIPTIONS.get(http_code)
    if result:
        return result
    else:
        return RESPONSE_DESCRIPTIONS[f"{http_code[0]}XX"]


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
        plugins: Sequence[BasePlugin] = (),
        servers: Optional[List[Union[str, openapi.Server]]] = None,
        security_schemes: Optional[
            Mapping[str, openapi.SecurityScheme]
        ] = None,
        **options: Any,
    ):
        if spec is None:
            spec = OpenAPIDocument(
                title=title,
                version=version,
                openapi_version=openapi_version,
                servers=servers,
                security_schemes=security_schemes,
                **options,
            )
        self.spec = spec
        self.plugins: Sequence[BasePlugin] = (*plugins, *BASE_PLUGINS)
        for plugin in self.plugins:
            plugin.init_spec(spec)

    def feed_routes(self, routes: Iterable[RouteDef]) -> None:
        for route in sorted(
            routes,
            key=lambda r: (r.path, METHOD_ORDER.index(r.method.lower())),
        ):
            self._process_route(route)

    def _process_route(self, route: RouteDef) -> None:
        method = route.method.lower()
        meta = getattr(route.handler, "__openapify__", [])
        responses: Optional[openapi.Responses] = None
        summary = route.summary
        description = route.description
        tags = route.tags.copy() if route.tags else []
        deprecated = None
        operation_id = None
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
                if body is not None or media_type is not None:
                    request_body = self._update_request_body(
                        request_body=request_body,
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
                responses = self._update_responses(responses=responses, **args)
            elif args_type == "operation_docs":
                args = args.copy()
                summary = args.get("summary")
                description = args.get("description")
                tags.extend(args.get("tags") or [])
                # _merge_parameters(parameters, args.get("parameters") or {})
                operation_id = args.get("operation_id")
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
                    responses=responses,
                    deprecated=deprecated,
                    tags=tags or None,
                    parameters=parameters or None,
                    externalDocs=external_docs,
                    operationId=operation_id,
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
            parameter_schema = self.__build_object_schema_with_plugins(
                param, name
            )
            if parameter_schema is None:
                parameter_schema = {}
            result.append(
                openapi.Parameter(
                    name=name,
                    location=openapi.ParameterLocation.QUERY,
                    description=param.description,
                    required=param.required,
                    deprecated=param.deprecated,
                    allowEmptyValue=param.allowEmptyValue,
                    schema=parameter_schema,
                    style=param.style,
                    explode=param.explode,
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
            parameter_schema = self.__build_object_schema_with_plugins(
                header, name
            )
            if parameter_schema is None:
                parameter_schema = {}
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
    ) -> Mapping[str, openapi.Header]:
        result = {}
        for name, header in headers.items():
            if not isinstance(header, Header):
                header = Header(description=header)
            header_schema = self.__build_object_schema_with_plugins(
                header, name
            )
            if header_schema is None:
                header_schema = {}
            result[name] = openapi.Header(
                schema=header_schema,
                description=header.description,
                required=header.required,
                deprecated=header.deprecated,
                allowEmptyValue=header.allowEmptyValue,
                example=header.example,
                examples=self._build_examples(header.examples),
            )
        return result

    def _build_cookies(
        self, cookies: Dict[str, Union[str, Cookie]]
    ) -> Sequence[openapi.Parameter]:
        result = []
        for name, cookie in cookies.items():
            if not isinstance(cookie, Cookie):
                cookie = Cookie(cookie)
            parameter_schema = self.__build_object_schema_with_plugins(
                cookie, name
            )
            if parameter_schema is None:
                parameter_schema = {}
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

    def _update_request_body(
        self,
        request_body: Optional[openapi.RequestBody],
        value_type: TypeAnnotation,
        media_type: Optional[str] = None,
        required: Optional[bool] = None,
        description: Optional[str] = None,
        example: Optional[Any] = None,
        examples: Optional[Mapping[str, Union[openapi.Example, Any]]] = None,
    ) -> openapi.RequestBody:
        if request_body is None:
            request_body = openapi.RequestBody()
        if description:
            request_body.description = description
        if required is not None:
            request_body.required = required
        body_schema: Optional[Dict[str, Any]] = None
        if value_type is not None:
            body = Body(
                value_type=value_type,
                media_type=media_type,
                required=required,
                description=description,
                example=example,
                examples=examples,
            )
            body_schema = self.__build_object_schema_with_plugins(body)
            if body_schema is None:
                body_schema = {}
            if media_type is None:
                media_type = self._determine_body_media_type(body, body_schema)
        elif media_type is not None:
            body_schema = {}
        if body_schema is not None and media_type is not None:
            if request_body.content is None:
                request_body.content = {}
            request_body.content[media_type] = openapi.MediaType(
                schema=body_schema,
                example=example,
                examples=self._build_examples(examples),
            )
        return request_body

    def _update_responses(
        self,
        responses: Optional[openapi.Responses],
        http_code: openapi.HttpCode,
        body: Optional[Type] = None,
        media_type: Optional[str] = None,
        description: Optional[str] = None,
        headers: Optional[Dict[str, Union[str, Header]]] = None,
        example: Optional[Any] = None,
        examples: Optional[Dict[str, Union[openapi.Example, Any]]] = None,
    ) -> openapi.Responses:
        http_code = str(http_code)
        if responses is None:
            responses = openapi.Responses()
        if responses.codes is None:
            responses.codes = {}
        response = responses.codes.get(http_code)
        if not response:
            response = openapi.Response()
            responses.codes[http_code] = response
        if headers:
            response.headers = self._build_response_headers(headers)
        if description:
            response.description = description
        elif not response.description:
            response.description = default_response_description(http_code)
        body_schema: Optional[Dict[str, Any]] = None
        if body is not None:
            body_obj = Body(
                value_type=body,
                media_type=media_type,
                required=True,
                description=description,
                example=example,
                examples=examples,
            )
            body_schema = self.__build_object_schema_with_plugins(body_obj)
            if body_schema is None:
                body_schema = {}
            if media_type is None:
                media_type = self._determine_body_media_type(
                    body_obj, body_schema
                )
        elif media_type is not None:
            body_schema = {}
        if body_schema is not None and media_type is not None:
            if response.content is None:
                response.content = {}
            response.content[media_type] = openapi.MediaType(
                schema=body_schema,
                example=example,
                examples=self._build_examples(examples),
            )
        return responses

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

    def __build_object_schema_with_plugins(
        self,
        obj: Union[Body, Cookie, Header, QueryParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        return build_object_schema_with_plugins(obj, self.plugins, name)

    def _determine_body_media_type(
        self, body: Body, schema: Dict[str, Any]
    ) -> Optional[str]:
        for plugin in self.plugins:
            try:
                media_type = plugin.media_type_helper(body, schema)
                if media_type is not None:
                    return media_type
            except NotImplementedError:
                continue
        return None


def build_object_schema_with_plugins(
    obj: Union[Body, Cookie, Header, QueryParam],
    plugins: Sequence[BasePlugin],
    name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    for plugin in plugins:
        try:
            schema = plugin.schema_helper(obj, name)
            if schema is not None:
                return schema
        except NotImplementedError:
            continue
    return None


@overload
def build_spec(
    routes: Iterable[RouteDef], spec: apispec.APISpec
) -> apispec.APISpec: ...


@overload
def build_spec(
    routes: Iterable[RouteDef],
    *,
    title: str = DEFAULT_SPEC_TITLE,
    version: str = DEFAULT_SPEC_VERSION,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Sequence[BasePlugin] = (),
    servers: Optional[List[Union[str, openapi.Server]]] = None,
    security_schemes: Optional[Mapping[str, openapi.SecurityScheme]] = None,
    **options: Any,
) -> apispec.APISpec: ...


def build_spec(
    routes: Iterable[RouteDef],
    spec: Optional[apispec.APISpec] = None,
    *,
    title: str = DEFAULT_SPEC_TITLE,
    version: str = DEFAULT_SPEC_VERSION,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Sequence[BasePlugin] = (),
    servers: Optional[List[Union[str, openapi.Server]]] = None,
    security_schemes: Optional[Mapping[str, openapi.SecurityScheme]] = None,
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
