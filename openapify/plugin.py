from typing import Any, Dict, Optional, Union

from apispec import APISpec

from openapify.core.models import Body, Cookie, Header, QueryParam


class BasePlugin:
    def init_spec(self, spec: Optional[APISpec]) -> None:
        pass

    def schema_helper(
        self,
        definition: Union[Body, Cookie, Header, QueryParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def examples_helper(
        self,
        definition: Union[Body, Cookie, Header, QueryParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def media_type_helper(
        self, body: Body, schema: Dict[str, Any]
    ) -> Optional[str]:
        raise NotImplementedError
