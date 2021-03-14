from typing import List, Dict

import requests
import slack
from django.db import transaction

from app.enums import SlackError
from app.settings import SL_INURL, APP_DOMAIN, SL_CHANNEL_WEBDEV, SL_USER_TOKEN

import user.utils


def send_deploy_message(deploy_data, succedded=True):
    if SL_INURL:
        if succedded:
            text = (
                ">>> :tada: *Deploy to <https://"
                + APP_DOMAIN
                + "|"
                + APP_DOMAIN
                + "> succedded*\n"
            )

        else:
            text = (
                ">>> :warning: *Deploy to <https://"
                + APP_DOMAIN
                + "|"
                + APP_DOMAIN
                + "> failed*\n"
            )
        text += (
            "_Commit <"
            + deploy_data["head_commit"]["url"]
            + "|"
            + deploy_data["head_commit"]["id"][:7]
            + "> by "
            + deploy_data["head_commit"]["author"]["name"]
            + "_\n"
        )
        text += deploy_data["head_commit"]["message"] + "\n"
        response = requests.post(SL_INURL, json={"text": text})
        return response.content
    return False


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
        if text:
            response = requests.post(SL_INURL, json={"text": text})
            return response.content
    return False


@transaction.atomic
def check_users() -> List[Dict]:
    if SL_USER_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_USER_TOKEN)
        # TODO: Maybe add pagination, large lists could 500
        response = client.users_list()
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.CHECK_USERS)

        users_by_email = {u.email: u for u in user.utils.get_users()}
        missing_users = []
        non_confirmed_users = []
        non_finished_users = []
        for slack_user in response.data["members"]:
            user_email = slack_user.get("profile", {}).get("email")
            if user_email:
                u = users_by_email.get(user_email)
                if not u:
                    missing_users.append(slack_user)
                elif not u.email_verified:
                    non_confirmed_users.append(slack_user)
                elif not u.registration_finished:
                    non_finished_users.append(slack_user)
                # TODO: Sync other user information
                # Update user Slack ID
                if u:
                    slack_id = slack_user.get("id")
                    if slack_id and slack_id != u.slack_id:
                        u.slack_id = slack_id
                        u.save()

        if (
            missing_users is []
            and non_confirmed_users is []
            and non_finished_users is []
        ):
            text = ">>> :white_check_mark: *Check users task*\nNo issues found\n"
        else:
            text = ">>> :rotating_light: *Check users task*\n"
            if missing_users:
                text += (
                    ("_Missing users_\n")
                    + "\n".join(
                        f"\t{u.get('real_name', u.get('name', u.get('id')))} <<mailto:{u.get('profile', {}).get('email')}|{u.get('profile', {}).get('email')}>>"
                        for u in missing_users
                    )
                    + "\n"
                )
            if non_confirmed_users:
                text += (
                    ("_Non-confirmed users_\n")
                    + "\n".join(
                        f"\t{u.get('real_name', u.get('name', u.get('id')))} <<mailto:{u.get('profile', {}).get('email')}|{u.get('profile', {}).get('email')}>>"
                        for u in non_confirmed_users
                    )
                    + "\n"
                )
            if non_finished_users:
                text += (
                    ("_Non-finished users_\n")
                    + "\n".join(
                        f"\t{u.get('real_name', u.get('name', u.get('id')))} <<mailto:{u.get('profile', {}).get('email')}|{u.get('profile', {}).get('email')}>>"
                        for u in non_finished_users
                    )
                    + "\n"
                )
        response = requests.post(SL_INURL, json={"text": text})
        return response.content
