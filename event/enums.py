import enum


class EventType(enum.IntEnum):
    GENERAL = 1
    LECTURE = 2
    LUNCH = 3
    EXTERNAL = 4
    OTHER = 5


class EventStatus(enum.IntEnum):
    DRAFT = 0
    PUBLISHED = 1
    DELETED = 2


class RegistrationStatus(enum.IntEnum):
    INTERESTED = 0
    REQUESTED = 1
    REGISTERED = 2
    WAIT_LISTED = 3
    CANCELLED = 4
