import enum


class MailTag(enum.Enum):
    REGISTER = "register"
    PASSWORD = "password"
    EVENT = "event"
    SLACK = "slack"
    CREATED = "created"


class SlackError(enum.Enum):
    CHECK_USERS = "check_users"
    RETRIEVE_CHANNELS = "retrieve_channels"
    RETRIEVE_CHANNEL = "retrieve_channel"
    SET_CHANNEL_NAME = "set_channel_name"
    SET_CHANNEL_TOPIC = "set_channel_topic"
    SET_CHANNEL_PURPOSE = "set_channel_purpose"
    INVITE_CHANNEL_USERS = "invite_channel_users"
    CREATE_CHANNEL = "create_channel"
    ADD_REACTION = "add_reaction"
    ADD_MESSAGE = "add_message"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    AUTH_USER = "auth_user"
    SET_USER_PICTURE = "set_user_picture"
    SEND_CHANNEL_MESSAGE = "send_channel_message"
