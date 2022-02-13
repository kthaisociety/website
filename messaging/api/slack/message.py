import requests

from app.enums import SlackError
from app.settings import SL_INURL


def send_error_message(error: SlackError):
    if SL_INURL:
        text = None
        if error == SlackError.CHECK_USERS:
            text = ">>> :rotating_light: *Check users task failed*\n"
        elif error == SlackError.RETRIEVE_CHANNELS:
            text = ">>> :rotating_light: *Retrieve channels task failed*\n"
        elif error == SlackError.RETRIEVE_CHANNEL:
            text = ">>> :rotating_light: *Retrieve channel task failed*\n"
        elif error == SlackError.SET_CHANNEL_NAME:
            text = ">>> :rotating_light: *Set channel name failed*\n"
        elif error == SlackError.SET_CHANNEL_TOPIC:
            text = ">>> :rotating_light: *Set channel topic failed*\n"
        elif error == SlackError.SET_CHANNEL_PURPOSE:
            text = ">>> :rotating_light: *Set channel purpose failed*\n"
        elif error == SlackError.INVITE_CHANNEL_USERS:
            text = ">>> :rotating_light: *Invite users to channel task failed*\n"
        elif error == SlackError.CREATE_CHANNEL:
            text = ">>> :rotating_light: *Create channel failed*\n"
        elif error == SlackError.ADD_REACTION:
            text = ">>> :rotating_light: *Add reaction failed*\n"
        elif error == SlackError.ADD_MESSAGE:
            text = ">>> :rotating_light: *Add message failed*\n"
        elif error == SlackError.UPDATE_USER:
            text = ">>> :rotating_light: *Update user task failed*\n"
        elif error == SlackError.AUTH_USER:
            text = ">>> :rotating_light: *Auth user failed*\n"
        elif error == SlackError.SET_USER_PICTURE:
            text = ">>> :rotating_light: *Set user picture failed*\n"
        elif error == SlackError.SEND_CHANNEL_MESSAGE:
            text = ">>> :rotating_light: *Send channel message failed*\n"
        if text:
            response = requests.post(SL_INURL, json={"text": text})
            return response.content
    return False