from io import StringIO
from uuid import UUID
import csv

from event.enums import RegistrationStatus
from event.models import Registration


def get_event_data_csv(event_id: UUID) -> StringIO:
    registrations_csv = StringIO()
    csvwriter = csv.writer(
        registrations_csv, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
    )
    csvwriter.writerow(
        [
            "ID",
            "Name",
            "Surname",
            "Email",
            "Status",
            "Diet",
            "Diet other",
            "Created at",
            "Updated at",
        ]
    )

    for registration in Registration.objects.filter(
        event_id=event_id,
        status__in=[
            RegistrationStatus.REGISTERED,
            RegistrationStatus.JOINED,
            RegistrationStatus.ATTENDED,
        ],
    ):
        csvwriter.writerow(
            [
                registration.id,
                registration.user.name,
                registration.user.surname,
                registration.user.email,
                RegistrationStatus(registration.status).name,
                " / ".join([d.name for d in registration.dietary_restrictions]),
                registration.diet_other,
                registration.created_at,
                registration.updated_at,
            ]
        )

    return registrations_csv
