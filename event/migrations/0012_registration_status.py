# Generated by Django 2.2.10 on 2020-04-21 09:01

from django.db import migrations, models
import event.enums


class Migration(migrations.Migration):

    dependencies = [("event", "0011_event_registration_available")]

    operations = [
        migrations.AlterField(
            model_name="registration",
            name="status",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "INTERESTED"),
                    (1, "REQUESTED"),
                    (2, "REGISTERED"),
                    (3, "WAIT_LISTED"),
                    (4, "CANCELLED"),
                    (5, "JOINED"),
                    (6, "ATTENDED"),
                ],
                default=event.enums.RegistrationStatus(1),
            ),
        )
    ]
