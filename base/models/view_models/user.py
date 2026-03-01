import uuid

from base.models.view_models import BaseModel


class CreateUserResponse(BaseModel):
    user_id: uuid.UUID


class GetUserResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None


class EditUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None


class EditUserResponse(BaseModel):
    pass


class DeleteUserResponse(BaseModel):
    pass
