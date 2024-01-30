from typing import Any, Dict, Optional, Union

from apispec import APISpec

from openapify.core.models import Body, Cookie, Header, QueryParam


class BasePlugin:
    spec: APISpec

    def init_spec(self, spec: APISpec) -> None:
        self.spec = spec

    def schema_helper(
        self,
        obj: Union[Body, Cookie, Header, QueryParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def media_type_helper(
        self, body: Body, schema: Dict[str, Any]
    ) -> Optional[str]:
        raise NotImplementedError
