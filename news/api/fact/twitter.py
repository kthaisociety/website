from typing import Optional

import tweepy

from news.models import Fact

from django.conf import settings


def post_fact_to_twitter(fact_obj: Fact) -> Optional[str]:
    if (
        not settings.TWITTER_API_KEY
        or not settings.TWITTER_API_KEY_SECRET
        or not settings.TWITTER_ACCESS_TOKEN
        or not settings.TWITTER_ACCESS_TOKEN_SECRET
    ):
        return

    auth = tweepy.OAuthHandler(
        settings.TWITTER_API_KEY,
        settings.TWITTER_API_KEY_SECRET,
    )
    auth.set_access_token(
        settings.TWITTER_ACCESS_TOKEN,
        settings.TWITTER_ACCESS_TOKEN_SECRET,
    )

    api = tweepy.API(auth)

    media_ids = []
    if fact_obj.picture:
        res = api.media_upload("files/" + fact_obj.picture.crop["1200x675"].name)
        media_ids.append(res.media_id)

    tweet = api.update_status(status=fact_obj.content, media_ids=media_ids)
    return tweet.id
