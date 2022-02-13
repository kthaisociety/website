from typing import List, Dict

import requests
import slack
from django.db import transaction
from django.utils import timezone

from app.enums import SlackError
from app.settings import SL_INURL, APP_DOMAIN, SL_CHANNEL_WEBDEV, SL_USER_TOKEN

import user.utils
import messaging.api.slack.log
import messaging.api.slack.user
from messaging.api.slack.message import send_error_message
from messaging.consts import WARNING_TIME_DAYS
from messaging.enums import LogType


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


@transaction.atomic
def check_users() -> List[Dict]:
    if SL_USER_TOKEN and SL_CHANNEL_WEBDEV:
        client = slack.WebClient(SL_USER_TOKEN)
        # TODO: Maybe add pagination, large lists could 500
        response = client.users_list()
        if not response.status_code == 200 or not response.data.get("ok", False):
            return send_error_message(error=SlackError.CHECK_USERS)

        users_by_email = {u.email: u for u in user.utils.get_users()}
        logs_by_email = {
            l.target.email: l
            for l in messaging.api.slack.log.find(type=LogType.WARNING)
        }
        users_to_warn = []
        for slack_user in response.data["members"]:
            user_email = slack_user.get("profile", {}).get("email")
            if user_email and not slack_user.get("deleted", False):
                u = users_by_email.get(user_email)
                if not u:
                    real_name = slack_user.get("profile", {}).get("real_name", "")
                    u = user.utils.create_user(
                        name=real_name.split(" ")[0],
                        surname=" ".join(real_name.split(" ")[1:]),
                        email=user_email,
                    )
                    user.utils.send_imported(user=u)

                # TODO: Sync other user information
                # Update user Slack ID
                slack_id = slack_user.get("id")
                if slack_id and slack_id != u.slack_id:
                    u.slack_id = slack_id
                    u.save()

                if not u.email_verified or not u.registration_finished:
                    users_to_warn.append(u)

        users_to_delete = []
        for u in users_to_warn:
            log_obj = logs_by_email.get(u.email)
            if log_obj:
                if log_obj.created_at < timezone.now() - timezone.timedelta(
                    days=WARNING_TIME_DAYS
                ):
                    users_to_delete.append(u)
            else:
                messaging.api.slack.user.warn_registration(id=u.id)

        if users_to_delete:
            text = ">>> :rotating_light: *Check users task*\n"
            text += (
                ("_Users to delete_\n")
                + "\n".join(
                    f"\t{u.full_name if u.full_name else u.slack_id} <<mailto:{u.email}|{u.email}>>"
                    for u in users_to_delete
                )
                + "\n"
            )
        else:
            text = ">>> :white_check_mark: *Check users task*\nNo issues found\n"
        response = requests.post(SL_INURL, json={"text": text})
        return response.content
