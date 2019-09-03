"""
Middleware to transform data from/to camunda.
"""
import json
import uuid
from dataclasses import dataclass
from typing import Any, Union

from bing.config.rewrites import URLRewriteMixin


def object_deserializer(value: str, value_info: dict) -> Any:
    assert value_info["serialization_data_format"] == "application/json", (
        "Unknown serialization_data_format %s" % value_info["serialization_data_format"]
    )
    _object_deserializer = OBJECT_DESERIALIZERS[value_info["object_type_name"]]
    raw = json.loads(value)
    return _object_deserializer(raw)


DESERIALIZERS = {
    "String": lambda value, value_info: str(value),
    "Json": lambda value, value_info: json.loads(value),
    "Object": object_deserializer,
}


OBJECT_DESERIALIZERS = {"java.util.UUID": uuid.UUID}


@dataclass
class Variable(URLRewriteMixin):
    data: Union[list, dict]

    serialization_data_format = "application/json"
    object_type_name = None

    def serialize(self) -> dict:
        value_info = {
            "serializationDataFormat": self.serialization_data_format,
            "objectTypeName": self.object_type_name,
        }
        self.rewrite_urls(self.data)
        return {"type": "json", "value": json.dumps(self.data), "valueInfo": value_info}

    def deserialize(self) -> Any:
        deserializer = DESERIALIZERS[self.data["type"]]
        return deserializer(self.data["value"], self.data["value_info"])


class ZaakVariable(Variable):
    object_type_name = "com.gemeenteutrecht.processplatform.domain.impl.ZaakImpl"


class DocumentListVariable(Variable):
    object_type_name = "com.gemeenteutrecht.processplatform.domain.document.request.impl.DocumentListImpl"
