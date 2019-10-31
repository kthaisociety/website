from app.utils import get_substitutions_templates


def variables_processor(request=None):
    c = get_substitutions_templates()
    return c
