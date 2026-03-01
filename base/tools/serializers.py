import json
import logging
from datetime import datetime
from inspect import isclass
from json import JSONEncoder
from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel

from base.models.orm import Base


def encode_datetime(obj):
    return dict(_type="datetime", value=obj.isoformat())


def encode_dto(obj):
    return dict(
        _type="dto",
        _class=f"{obj.__class__.__module__}.{obj.__class__.__name__}",
        value={k: v for k, v in obj.__dict__.items() if not k.startswith("_")},
    )


def encode_app_model(obj):
    return dict(
        _type="app_model",
        _class=f"{obj.__class__.__module__}.{obj.__class__.__name__}",
        value={k: v for k, v in obj.__dict__.items() if not k.startswith("_")},
    )


def encode_uuid(obj):
    return dict(_type="uuid", value=str(obj))


def encode_execution_context(obj):
    return dict(
        _type="execution_context",
        value={
            field_name: field_value
            for field_name, field_value in obj.__dict__.items()
            if not field_name.startswith("_")
            and field_name != "transient_instances"
            and field_name != "user"
        },
    )


def encode_abstract_message(obj):
    return dict(
        _type="abstract_message",
        _class=f"{obj.__class__.__module__}.{obj.__class__.__name__}",
        value={
            field_name: field_value
            for field_name, field_value in obj.__dict__.items()
            if not field_name.startswith("_")
        },
    )


def encode_type(obj):
    """Convert a type (class) to a string representation."""
    return dict(
        _type="type",
        value=f"{obj.__module__}.{obj.__qualname__}",
    )


class ExpansiveEncoder(JSONEncoder):
    encoders: dict = {
        datetime: encode_datetime,
        Base: encode_dto,
        BaseModel: encode_app_model,
        UUID: encode_uuid,
        type: encode_type,
        UploadFile: lambda obj: dict(
            _type="UploadFile", filename=obj.filename, content_type=obj.content_type
        ),
    }

    def default(self, o):
        for cls, encoder in self.encoders.items():
            if isinstance(o, cls):
                return encoder(o)
        logging.info(
            f"Defaulting to inherent serializer for {o.__class__.__name__ if isclass(o) else type(o)}"
        )
        return super().default(o)


def serialize(obj, **kwargs) -> str:
    return (
        json.dumps(obj, cls=ExpansiveEncoder, **kwargs)
        if not isinstance(obj, str)
        else obj
    )
