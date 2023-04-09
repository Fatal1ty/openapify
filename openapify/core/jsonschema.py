from enum import Enum
from typing import Any, Dict, Optional, Type

from apispec import APISpec
from mashumaro.jsonschema import OPEN_API_3_1, JSONSchemaBuilder


class ComponentType(Enum):
    SCHEMA = "schema"
    HEADER = "header"
    PARAMETER = "parameter"


ComponentTypeSpecKey = {
    ComponentType.SCHEMA: "schemas",
    ComponentType.HEADER: "headers",
    ComponentType.PARAMETER: "parameters",
}


def _build_json_schema_with_mashumaro(
    instance_type: Type,
    spec: Optional[APISpec] = None,
    component_type: ComponentType = ComponentType.SCHEMA,
) -> Optional[Dict[str, Any]]:
    builder = JSONSchemaBuilder(dialect=OPEN_API_3_1)
    try:
        json_schema = builder.build(instance_type)
    except Exception:
        return None
    if spec is not None:
        scope = getattr(spec.components, ComponentTypeSpecKey[component_type])
        for name, schema in builder.context.definitions.items():
            scope[name] = schema.to_dict()
    return json_schema.to_dict()


def build_json_schema(
    instance_type: Type,
    spec: Optional[APISpec] = None,
    component_type: ComponentType = ComponentType.SCHEMA,
) -> Dict[str, Any]:
    schema = _build_json_schema_with_mashumaro(
        instance_type, spec, component_type
    )
    if schema is not None:
        return schema
    return {}
    # TODO: support apispec plugins
    # component_id = type_name(instance_type, short=True)
    # getattr(spec.components, component_type.value)(
    #     component_id, component=None, schema=instance_type
    # )
    # return {"$ref": component_id}


__all__ = ["build_json_schema", "ComponentType"]
