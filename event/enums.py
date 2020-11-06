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


class AttachmentType(enum.IntEnum):
    SLIDES = 0
    FILE = 1
    IMAGE = 2
    VIDEO = 3


class AttachmentStatus(enum.IntEnum):
    DRAFT = 0
    PUBLISHED = 1
    DELETED = 2


class ScheduleType(enum.IntEnum):
    GENERAL = 0
    CEREMONY = 1
    TALK = 2
    TEAM_BUILDING = 3
    MEAL = 4
    DEMO = 5
    EVENT_START = 6
    EVENT_END = 7
    GAME = 8
    PRIZE = 9
