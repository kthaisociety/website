from app.utils import get_substitutions_templates
from event.enums import RegistrationStatusDict


def variables_processor(request=None):
    c = get_substitutions_templates(request=request)
    from business.enums import OfferTypeDict
    from business.utils import get_offers, get_sponsorships
    from event.enums import StreamingProviderDict
    from event.utils import get_events
    from news.utils import get_latest_articles, get_latest_pin
    from page.utils import get_menu_pages
    from user.enums import DietTypeDict, GenderTypeColoursDict, GenderTypeDict
    from user.utils import get_board, get_histories, get_organisers

    c["pin"] = get_latest_pin()
    c["articles"] = get_latest_articles()
    c["events"] = get_events()
    c["organisers"] = get_organisers()
    c["board"] = get_board()
    c["categories"] = get_menu_pages()
    c["histories"] = get_histories()
    c["sponsorships"] = get_sponsorships()
    c["offers_featured"] = get_offers(is_featured=True)[:2]
    c["offers"] = get_offers(is_featured=False)[:2]

    c["enums"] = {
        "event": {
            "streaming_provider": StreamingProviderDict,
            "registration_status": RegistrationStatusDict,
        },
        "user": {
            "gender": GenderTypeDict,
            "gender_colours": GenderTypeColoursDict,
            "diet": DietTypeDict,
        },
        "business": {"offer_type": OfferTypeDict},
    }

    return c
