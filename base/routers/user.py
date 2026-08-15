from fastapi import APIRouter, Depends

from base.models.orm.user import UserDTO
from base.models.view_models import BaseResponse
from base.models.view_models.user import (
    DeleteUserResponse,
    EditUserRequest,
    EditUserResponse,
    GetUserResponse,
)
from base.services.auth.dependencies import validate_user
from base.services.store.user import UserStore

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=BaseResponse[GetUserResponse])
async def get_user(
    current_user: UserDTO = Depends(validate_user),
) -> BaseResponse[GetUserResponse]:
    return BaseResponse(
        data=GetUserResponse(
            user_id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
        )
    )


@router.patch("/me", response_model=BaseResponse[EditUserResponse])
async def edit_user(
    request: EditUserRequest,
    current_user: UserDTO = Depends(validate_user),
) -> BaseResponse[EditUserResponse]:
    current_user.update_from_dict(
        request.serialize(exclude_unset=True, exclude_none=True, by_alias=False)
    )
    await UserStore().aedit(current_user.id, current_user)
    return BaseResponse(data=EditUserResponse())


@router.delete("/me", response_model=BaseResponse[DeleteUserResponse])
async def delete_user(
    current_user: UserDTO = Depends(validate_user),
) -> BaseResponse[DeleteUserResponse]:
    await UserStore().adelete(current_user.id)
    return BaseResponse(data=DeleteUserResponse())
