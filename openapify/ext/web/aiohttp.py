import re
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    Union,
    overload,
)

from aiohttp import hdrs
from aiohttp.abc import AbstractView
from aiohttp.typedefs import Handler
from aiohttp.web_app import Application
from apispec import APISpec
from mashumaro.jsonschema import OPEN_API_3_1, build_json_schema
from mashumaro.jsonschema.annotations import Pattern
from typing_extensions import Annotated

from openapify.core.builder import build_spec as core_build_spec
from openapify.core.const import (
    DEFAULT_OPENAPI_VERSION,
    DEFAULT_SPEC_TITLE,
    DEFAULT_SPEC_VERSION,
)
from openapify.core.models import RouteDef
from openapify.core.openapi.models import (
    Parameter,
    ParameterLocation,
    SecurityScheme,
    Server,
)
from openapify.plugin import BasePlugin

PARAMETER_TEMPLATE = re.compile(r"{([^:{}]+)(?::(.+))?}")


class AioHttpRouteDef(Protocol):
    method: str
    path: str
    handler: Union[Type[AbstractView], Handler]


def _aiohttp_app_to_route_defs(app: Application) -> Iterable[RouteDef]:
    for route in app.router.routes():
        yield RouteDef(
            path=route.resource.canonical,  # type: ignore
            method=route.method,
            handler=route.handler,
        )


def _aiohttp_route_defs_to_route_defs(
    route_defs: Iterable[AioHttpRouteDef],
) -> Iterable[RouteDef]:
    for route in route_defs:
        if route.method == hdrs.METH_ANY:
            for method in map(str.lower, hdrs.METH_ALL):
                handler = getattr(route.handler, method, None)
                if handler:
                    yield RouteDef(route.path, method, handler)
        else:
            yield RouteDef(route.path, route.method, route.handler)


def _pull_out_path_parameters(path: str) -> Tuple[str, List[Parameter]]:
    parameters = []

    def _sub(match: re.Match) -> str:
        name = match.group(1)
        regex = match.group(2)
        if regex:
            instance_type = Annotated[str, Pattern(regex)]
        else:
            instance_type = str  # type: ignore[misc]
        parameters.append(
            Parameter(
                name=name,
                location=ParameterLocation.PATH,
                required=True,
                schema=build_json_schema(
                    instance_type, dialect=OPEN_API_3_1
                ).to_dict(),
            )
        )
        return f"{{{name}}}"

    return re.sub(PARAMETER_TEMPLATE, _sub, path), parameters


def _complete_routes(routes: Iterable[RouteDef]) -> Iterable[RouteDef]:
    for route in routes:
        route.path, parameters = _pull_out_path_parameters(route.path)
        if parameters:
            route.parameters = parameters
        yield route


@overload
def build_spec(
    app: Application, spec: Optional[APISpec] = None
) -> APISpec: ...


@overload
def build_spec(
    routes: Iterable[AioHttpRouteDef], spec: Optional[APISpec] = None
) -> APISpec: ...


@overload
def build_spec(
    app: Application,
    *,
    title: str = DEFAULT_SPEC_TITLE,
    version: str = DEFAULT_SPEC_VERSION,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Sequence[BasePlugin] = (),
    route_postprocessor: Optional[
        Callable[[RouteDef], Union[RouteDef, None]]
    ] = None,
    **options: Any,
) -> APISpec: ...


@overload
def build_spec(
    routes: Iterable[AioHttpRouteDef],
    *,
    title: str = DEFAULT_SPEC_TITLE,
    version: str = DEFAULT_SPEC_VERSION,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Sequence[BasePlugin] = (),
    route_postprocessor: Optional[
        Callable[[RouteDef], Union[RouteDef, None]]
    ] = None,
    **options: Any,
) -> APISpec: ...


def build_spec(  # type: ignore[misc]
    app_or_routes: Union[Application, Iterable[AioHttpRouteDef]],
    spec: Optional[APISpec] = None,
    *,
    title: str = DEFAULT_SPEC_TITLE,
    version: str = DEFAULT_SPEC_VERSION,
    openapi_version: str = DEFAULT_OPENAPI_VERSION,
    plugins: Sequence[BasePlugin] = (),
    servers: Optional[List[Union[str, Server]]] = None,
    security_schemes: Optional[Mapping[str, SecurityScheme]] = None,
    route_postprocessor: Optional[
        Callable[[RouteDef], Union[RouteDef, None]]
    ] = None,
    **options: Any,
) -> APISpec:
    if isinstance(app_or_routes, Application):
        routes = _aiohttp_app_to_route_defs(app_or_routes)
    else:
        routes = _aiohttp_route_defs_to_route_defs(app_or_routes)
    routes = _complete_routes(routes)
    if route_postprocessor:
        routes = filter(None, map(route_postprocessor, routes))
    return core_build_spec(
        routes=routes,
        spec=spec,
        title=title,
        version=version,
        openapi_version=openapi_version,
        plugins=plugins,
        servers=servers,
        security_schemes=security_schemes,
        **options,
    )


__all__ = ["build_spec"]
