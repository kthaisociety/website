import enum


class EventType(enum.IntEnum):
    GENERAL = 1
    LECTURE = 2
    LUNCH = 3
    EXTERNAL = 4
    WEBINAR = 5
    OTHER = 6


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
    JOINED = 5
    ATTENDED = 6
