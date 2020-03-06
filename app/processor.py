from app.utils import get_substitutions_templates


def variables_processor(request=None):
    c = get_substitutions_templates(request=request)
    from news.utils import get_latest_articles
    from event.utils import get_future_events

    c["articles"] = get_latest_articles()
    c["events"] = get_future_events()
    return c
