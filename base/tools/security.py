from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from base.services.common.meta import NonInitialize


class PasswordHashingService(metaclass=NonInitialize):
    _hasher: PasswordHasher = PasswordHasher()

    @classmethod
    def hash(cls, password: str) -> str:
        return cls._hasher.hash(password)

    @classmethod
    def verify(cls, plain: str, hashed: str) -> bool:
        try:
            return cls._hasher.verify(hashed, plain)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
