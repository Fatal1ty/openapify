from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from apispec import APISpec, BasePlugin

from openapify.core.const import (
    DEFAULT_OPENAPI_VERSION,
    DEFAULT_SPEC_TITLE,
    DEFAULT_SPEC_VERSION,
)
from openapify.core.openapi.models import SecurityScheme, Server


def merge_dicts(original: Dict, update: Dict) -> Dict:
    for key, value in update.items():
        if key not in original:
            original[key] = value
        elif isinstance(value, dict):
            merge_dicts(original[key], value)
    return original


class OpenAPIDocument(APISpec):
    def __init__(
        self,
        title: str = DEFAULT_SPEC_TITLE,
        version: str = DEFAULT_SPEC_VERSION,
        openapi_version: str = DEFAULT_OPENAPI_VERSION,
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

    def to_dict(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {
            "openapi": str(self.openapi_version),
            "info": {"title": self.title, "version": self.version},
        }
        servers = self.options.pop("servers", None)
        if servers:
            ret["servers"] = servers
        ret["paths"] = self._paths
        components_dict = self.components.to_dict()
        if components_dict:
            ret["components"] = components_dict
        if self._tags:
            ret["tags"] = self._tags
        ret = merge_dicts(ret, self.options)
        return ret
