import enum


class MailTag(enum.Enum):
    REGISTER = "register"
    PASSWORD = "password"
    EVENT = "event"


class SlackError(enum.Enum):
    CHECK_USERS = "check_users"
    RETRIEVE_CHANNELS = "retrieve_channels"
    SET_CHANNEL_NAME = "set_channel_name"
    SET_CHANNEL_TOPIC = "set_channel_topic"
    SET_CHANNEL_PURPOSE = "set_channel_purpose"
    INVITE_CHANNEL_USERS = "invite_channel_users"
    CREATE_CHANNEL = "create_channel"
    ADD_REACTION = "add_reaction"
    ADD_MESSAGE = "add_message"
