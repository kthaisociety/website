import random

from django.utils import timezone

from news.api.fact.post import post_fact
from news.consts import FACT_POST_DAYS_FREQUENCY
from news.enums import FactStatus, PostType
from news.models import FactPost, Fact


def post_random_fact():
    last_fact_post_obj = FactPost.objects.order_by("-created_at").first()

    if (
        not last_fact_post_obj
        or timezone.now() - last_fact_post_obj.created_at
        >= timezone.timedelta(days=FACT_POST_DAYS_FREQUENCY)
    ):
        # Get random fact
        fact_objs = Fact.objects.filter(status=FactStatus.REVIEWED)
        if fact_objs:
            fact_obj = random.choice(fact_objs)
            post_fact(fact_id=fact_obj.id, post_type=PostType.TWITTER)
