from enum import Enum

from fastapi import status


class AuthErrors(Enum):
    USER_UNAUTHORIZED = {
        "message": "Unauthorized.",
        "status_code": status.HTTP_401_UNAUTHORIZED,
    }
    USER_NOT_FOUND = {
        "message": "User not found.",
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    USER_TOKEN_EXPIRED = {
        "message": "Token expired.",
        "status_code": status.HTTP_401_UNAUTHORIZED,
    }
    USER_DECODE_FAILED = {
        "message": "Invalid token.",
        "status_code": status.HTTP_401_UNAUTHORIZED,
    }
    USER_TOKEN_INCOMPLETE = {
        "message": "Token incomplete.",
        "status_code": status.HTTP_401_UNAUTHORIZED,
    }


class DatabaseErrors(Enum):
    RECORD_NOT_FOUND = {
        "message": "Record not found.",
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    UNIQUE_CONSTRAINT_VIOLATION = {
        "message": "Record already exists.",
        "status_code": status.HTTP_409_CONFLICT,
    }


class GenericErrors(Enum):
    UNEXPECTED_ERROR = {
        "message": "Unexpected error.",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
