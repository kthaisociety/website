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


RegistrationStatus.labels = {
    RegistrationStatus.INTERESTED: "Interested",
    RegistrationStatus.REQUESTED: "Requested",
    RegistrationStatus.REGISTERED: "Registered",
    RegistrationStatus.WAIT_LISTED: "Wait-listed",
    RegistrationStatus.CANCELLED: "Cancelled",
    RegistrationStatus.JOINED: "Joined",
    RegistrationStatus.ATTENDED: "Attended",
}
RegistrationStatusDict = RegistrationStatus.labels


class SignupStatus(enum.IntEnum):
    OPEN = 0
    PAST = 1
    FULL = 2
    CLOSED = 3
    FUTURE = 4
    OTHER = 5


SignupStatus.labels = {
    SignupStatus.OPEN: "Open",
    SignupStatus.PAST: "Past event",
    SignupStatus.FULL: "Attendance limit reached",
    SignupStatus.CLOSED: "Closed",
    SignupStatus.FUTURE: "Opens soon",
    SignupStatus.OTHER: "Other",
}
SignupStatusDict = SignupStatus.labels


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


class StreamingProvider(enum.IntEnum):
    GOOGLE_MEET = 10
    YOUTUBE = 20
    ZOOM = 30


StreamingProvider.labels = {
    StreamingProvider.GOOGLE_MEET: "Google Meet",
    StreamingProvider.YOUTUBE: "Youtube",
    StreamingProvider.ZOOM: "Zoom",
}
StreamingProviderDict = StreamingProvider.labels


class SpeakerRoleType(enum.IntEnum):
    SPEAKER = 0
    MODERATOR = 1
    SPECTATOR = 2
