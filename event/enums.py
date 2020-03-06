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
