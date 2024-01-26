from typing import Any, ByteString, Dict, Optional, Union

from openapify.core.models import Body, Cookie, Header, QueryParam
from openapify.plugin import BasePlugin


class BodyBinaryPlugin(BasePlugin):
    def schema_helper(
        self,
        definition: Union[Body, Cookie, Header, QueryParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            if isinstance(definition, Body) and issubclass(
                definition.value_type, ByteString  # type: ignore
            ):
                return {}
            else:
                return None
        except TypeError:
            return None


class GuessMediaTypePlugin(BasePlugin):
    def media_type_helper(
        self, body: Body, schema: Dict[str, Any]
    ) -> Optional[str]:
        if not schema and issubclass(
            body.value_type, ByteString  # type: ignore
        ):
            return "application/octet-stream"
        else:
            return "application/json"
