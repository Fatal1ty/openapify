from mashumaro.core.meta.helpers import get_type_origin

from openapify.core.models import TypeAnnotation


def get_value_type(value_type: TypeAnnotation) -> TypeAnnotation:
    super_type = getattr(value_type, "__supertype__", None)
    if super_type is not None:
        return get_value_type(super_type)
    origin_type = get_type_origin(value_type)
    if origin_type is not value_type:
        return get_value_type(origin_type)
    return value_type
