import enum


class UserType(enum.IntEnum):
    ORGANISER = 0
    PARTICIPANT = 1


class GenderType(enum.IntEnum):
    NONE = 0
    FEMALE = 1
    MALE = 2
    NON_BINARY = 3
