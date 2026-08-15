import json
import logging
from collections.abc import Callable
from datetime import datetime
from inspect import isclass
from json import JSONEncoder
from typing import Any
from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel

from base.models.orm import Base


def encode_datetime(obj: datetime) -> dict[str, Any]:
    return dict(_type="datetime", value=obj.isoformat())


def encode_dto(obj: Base) -> dict[str, Any]:
    return dict(
        _type="dto",
        _class=f"{obj.__class__.__module__}.{obj.__class__.__name__}",
        value={k: v for k, v in obj.__dict__.items() if not k.startswith("_")},
    )


def encode_base_model(obj: BaseModel) -> dict[str, Any]:
    return dict(
        _type="base_model",
        _class=f"{obj.__class__.__module__}.{obj.__class__.__name__}",
        value=obj.model_dump(mode="python"),
    )


def encode_uuid(obj: UUID) -> dict[str, Any]:
    return dict(_type="uuid", value=str(obj))


def encode_type(obj: type) -> dict[str, Any]:
    """Convert a type (class) to a string representation."""
    return dict(
        _type="type",
        value=f"{obj.__module__}.{obj.__qualname__}",
    )


def encode_upload_file(obj: UploadFile) -> dict[str, Any]:
    return dict(
        _type="UploadFile", filename=obj.filename, content_type=obj.content_type
    )


class ExpansiveEncoder(JSONEncoder):
    encoders: dict[type, Callable[[Any], dict[str, Any]]] = {
        datetime: encode_datetime,
        Base: encode_dto,
        BaseModel: encode_base_model,
        UUID: encode_uuid,
        type: encode_type,
        UploadFile: encode_upload_file,
    }

    def default(self, o: Any) -> Any:
        for cls, encoder in self.encoders.items():
            if isinstance(o, cls):
                return encoder(o)
        logging.info(
            f"Defaulting to inherent serializer for {o.__class__.__name__ if isclass(o) else type(o)}"
        )
        return super().default(o)


def serialize(obj: Any, **kwargs: Any) -> str:
    return (
        json.dumps(obj, cls=ExpansiveEncoder, **kwargs)
        if not isinstance(obj, str)
        else obj
    )
