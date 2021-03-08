import enum


class MailTag(enum.Enum):
    REGISTER = "register"
    PASSWORD = "password"
    EVENT = "event"


class SlackError(enum.Enum):
    CHECK_USERS = "check_users"
