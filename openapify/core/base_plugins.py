from typing import Any, ByteString, Dict, Optional, Union

from mashumaro.jsonschema import OPEN_API_3_1, JSONSchemaBuilder

from openapify.core.models import Body, Cookie, Header, QueryParam
from openapify.plugin import BasePlugin


class BodyBinaryPlugin(BasePlugin):
    def schema_helper(
        self,
        obj: Union[Body, Cookie, Header, QueryParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            if isinstance(obj, Body) and issubclass(
                obj.value_type, ByteString  # type: ignore
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


class BaseSchemaPlugin(BasePlugin):
    def schema_helper(
        self,
        obj: Union[Body, Cookie, Header, QueryParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        builder = JSONSchemaBuilder(
            dialect=OPEN_API_3_1, ref_prefix="#/components/schemas"
        )
        try:
            json_schema = builder.build(obj.value_type)
        except Exception:
            return None
        schemas = self.spec.components.schemas
        for name, schema in builder.context.definitions.items():
            schemas[name] = schema.to_dict()
        return json_schema.to_dict()
