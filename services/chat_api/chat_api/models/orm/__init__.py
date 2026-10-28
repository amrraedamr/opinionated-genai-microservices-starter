"""Declarative root for chat_api.

Owns its own `MetaData`. Nothing here inherits a declarative base from `base`,
because inheriting one would share its `MetaData` — and a shared `MetaData`
makes every service's `alembic autogenerate` emit every other service's
tables. Reusable column and serialisation behaviour comes from `base` mixins
instead.
"""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from base.models.orm import SerializableMixin, TimestampMixin


class ChatBase(MappedAsDataclass, DeclarativeBase, SerializableMixin):
    """Declarative root for every table chat_api owns."""


__all__ = ["ChatBase", "SerializableMixin", "TimestampMixin"]
