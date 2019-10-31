import requests

from app.settings import SL_INURL
from app.variables import APP_DOMAIN


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
