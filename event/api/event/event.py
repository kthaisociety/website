import zipfile
from io import BytesIO
from uuid import UUID

from event.models import Event


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
