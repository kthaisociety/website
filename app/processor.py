from app.utils import get_substitutions_templates


def variables_processor(request=None):
    c = get_substitutions_templates(request=request)
    from news.utils import get_latest_articles
    from event.utils import get_future_events, get_events
    from user.utils import get_organisers, get_board, get_histories
    from page.utils import get_menu_pages
    from business.utils import get_sponsorships, get_offers

    from event.enums import StreamingProviderDict
    from user.enums import GenderTypeDict, GenderTypeColoursDict
    from business.enums import OfferTypeDict

    c["articles"] = get_latest_articles()
    c["events"] = get_future_events()
    if not c["events"]:
        c["events"] = get_events()
    c["organisers"] = get_organisers()
    c["board"] = get_board()
    c["categories"] = get_menu_pages()
    c["histories"] = get_histories()
    c["sponsorships"] = get_sponsorships()
    c["offers"] = get_offers()

    c["enums"] = {
        "event": {"streaming_provider": StreamingProviderDict},
        "user": {"gender": GenderTypeDict, "gender_colours": GenderTypeColoursDict},
        "business": {"offer_type": OfferTypeDict},
    }

    return c
