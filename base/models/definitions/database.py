from enum import StrEnum


class DatabaseTable(StrEnum):
    USER = "user"


class Locale(StrEnum):
    EN = "en"
    AR = "ar"
    OTHER = "other"


class SortingOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"
