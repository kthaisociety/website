from typing import Optional
from uuid import UUID

from django.db import transaction

from news.api.fact.twitter import post_fact_to_twitter
from news.enums import PostType, FactStatus
from news.models import FactPost, Fact


@transaction.atomic
def post_fact(fact_id: UUID, post_type: PostType) -> Optional[FactPost]:
    fact_obj = Fact.objects.filter(id=fact_id, status=FactStatus.REVIEWED).first()

    if not fact_obj:
        return

    if post_type == PostType.TWITTER:
        external_id = post_fact_to_twitter(fact_obj=fact_obj)
    else:
        return

    if not external_id:
        return

    fact_obj.status = FactStatus.PUBLISHED
    fact_obj.save()

    return FactPost.objects.create(
        fact=fact_obj, type=post_type, external_id=external_id
    )
