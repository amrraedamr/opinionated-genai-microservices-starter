from fastapi import APIRouter

from base.models.definitions.errors import AuthErrors
from base.models.orm.user import UserDTO
from base.models.view_models import BaseResponse
from base.models.view_models.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RefreshToken,
    RegisterRequest,
)
from base.models.view_models.user import CreateUserResponse
from base.services.auth import AuthService
from base.services.store.user import UserStore
from base.tools.errors import raise_error
from base.tools.security import PasswordHashingService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=BaseResponse[CreateUserResponse])
async def register(
    request: RegisterRequest,
) -> BaseResponse[CreateUserResponse]:
    user = UserDTO(
        email=request.email,
        password_hash=PasswordHashingService.hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
    )
    created = await UserStore().aadd(user)
    return BaseResponse(data=CreateUserResponse(user_id=created.id))


@router.post("/login", response_model=BaseResponse[LoginResponse])
async def login(
    request: LoginRequest,
) -> BaseResponse[LoginResponse]:
    user = await UserStore().aget(request.email, column_name="email")
    if not user:
        raise_error(AuthErrors.USER_UNAUTHORIZED)
    if not PasswordHashingService.verify(request.password, user.password_hash):
        raise_error(AuthErrors.USER_UNAUTHORIZED)
    token_pair = AuthService().generate_token_pair(user)
    return BaseResponse(
        data=LoginResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
        )
    )


@router.post("/refresh", response_model=BaseResponse[RefreshResponse])
async def refresh(request: RefreshRequest) -> BaseResponse[RefreshResponse]:
    token_pair = await AuthService().refresh_access_token(
        RefreshToken(request.refresh_token)
    )
    return BaseResponse(
        data=RefreshResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
        )
    )
