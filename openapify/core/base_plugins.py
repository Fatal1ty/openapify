from collections.abc import Sequence
from typing import Any, Dict, Optional, Union

from mashumaro.jsonschema import OPEN_API_3_1, JSONSchemaBuilder
from mashumaro.jsonschema.plugins import BasePlugin as BaseJSONSchemaPlugin

from openapify.core.models import Body, Cookie, Header, PathParam, QueryParam
from openapify.core.utils import get_value_type
from openapify.plugin import BasePlugin


class BodyBinaryPlugin(BasePlugin):
    def schema_helper(
        self,
        obj: Union[Body, Cookie, Header, QueryParam, PathParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            if isinstance(obj, Body):
                if get_value_type(obj.value_type) in (bytes, bytearray):
                    return {}

            return None
        except TypeError:
            return None


class GuessMediaTypePlugin(BasePlugin):
    def media_type_helper(
        self, body: Body, schema: Dict[str, Any]
    ) -> Optional[str]:
        if not schema and get_value_type(body.value_type) in (
            bytes,
            bytearray,
        ):
            return "application/octet-stream"
        else:
            return "application/json"


class BaseSchemaPlugin(BasePlugin):
    def __init__(self, plugins: Sequence[BaseJSONSchemaPlugin] = ()):
        self.json_schema_plugins = plugins

    def schema_helper(
        self,
        obj: Union[Body, Cookie, Header, QueryParam, PathParam],
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        builder = JSONSchemaBuilder(
            dialect=OPEN_API_3_1,
            ref_prefix="#/components/schemas",
            plugins=self.json_schema_plugins,
        )
        try:
            json_schema = builder.build(obj.value_type)
        except Exception:
            return None
        schemas = self.spec.components.schemas
        for name, schema in builder.context.definitions.items():
            schemas[name] = schema.to_dict()
        if isinstance(obj, QueryParam) and obj.default is not None:
            json_schema.default = obj.default
        return json_schema.to_dict()
