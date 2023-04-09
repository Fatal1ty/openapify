from typing import Any, List, Mapping, Optional, Sequence, Union

from apispec import APISpec, BasePlugin

from openapify.core.openapi.models import SecurityScheme, Server


class OpenAPIDocument(APISpec):
    def __init__(
        self,
        title: str,
        version: str,
        openapi_version: str,
        plugins: Sequence[BasePlugin] = (),
        servers: Optional[List[Union[str, Server]]] = None,
        security_schemes: Optional[Mapping[str, SecurityScheme]] = None,
        **options: Any,
    ) -> None:
        kwargs = {}
        _servers = []
        for server in servers or ():
            if isinstance(server, str):
                _servers.append({"url": server})
            else:
                _servers.append(server.to_dict())
        if _servers:
            kwargs["servers"] = _servers
        super().__init__(
            title=title,
            version=version,
            openapi_version=openapi_version,
            plugins=plugins,
            **kwargs,
            **options,
        )
        if security_schemes:
            for name, scheme in security_schemes.items():
                self.components.security_scheme(name, scheme.to_dict())
