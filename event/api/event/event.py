import zipfile
from io import BytesIO
from uuid import UUID

from django.core.files.images import ImageFile
from django.db.models import Prefetch
from django.template.loader import render_to_string
from html2image import Html2Image

from app.utils import get_substitutions_templates
from event.models import Event, Session


def get_event_resumes_zip(event_id: UUID) -> BytesIO:
    event = Event.objects.get(id=event_id)

    mf = BytesIO()
    zf = zipfile.ZipFile(mf, mode="w", compression=zipfile.ZIP_DEFLATED)

    if event.collect_resume:
        for registration in event.registrations.all():
            if registration.user.resume:
                resume_extension = registration.user.resume.name.split(".")[-1]
                zf.writestr(
                    f"{registration.user.id}.{resume_extension}",
                    registration.user.resume.read(),
                )
    zf.close()

    return mf


def update_event_poster(event_id: UUID) -> None:
    event_obj = (
        Event.objects.published()
        .filter(id=event_id)
        .prefetch_related(
            Prefetch("sessions", Session.objects.all().order_by("starts_at"))
        )
        .first()
    )
    context = get_substitutions_templates()
    context["event"] = event_obj
    html = render_to_string(
        "poster/poster.html",
        context=context,
    )
    hti = Html2Image(output_path="files/event/poster")

    # Main social picture
    hti.screenshot(html_str=html, save_as=f"{event_id}.png", size=(1200, 630))
    img = open(f"files/event/poster/{event_id}.png", "rb")
    event_obj.social_picture = ImageFile(img, name=f"{event_id}.png")

    # Social picture (squared)
    hti.screenshot(html_str=html, save_as=f"{event_id}_sq.png", size=(750, 750))
    img = open(f"files/event/poster/{event_id}_sq.png", "rb")
    event_obj.social_picture_sq = ImageFile(img, name=f"{event_id}.png")

    event_obj.save(
        update_poster=False, update_fields=("social_picture", "social_picture_sq")
    )
