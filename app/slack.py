from typing import List, Dict

import requests
import slack

from app.enums import SlackError
from app.settings import (
    SL_INURL,
    APP_DOMAIN,
    SL_TOKEN,
    SL_CHANNEL_WEBDEV,
    SL_ID,
    SL_SECRET,
)

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
            text = ">>> :siren: *Check users task failed*\n"
        if text:
            response = requests.post(SL_INURL, json={"text": text})
            return response.content
    return False


def check_users() -> List[Dict]:
    if SL_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_TOKEN)
        response = client.users_list(limit=20)
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

        if (
            missing_users is []
            and non_confirmed_users is []
            and non_finished_users is []
        ):
            text = ">>> :white_check_mark: *Check users task*\nNo issues found\n"
        else:
            text = ">>> :siren: *Check users task*\n"
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
