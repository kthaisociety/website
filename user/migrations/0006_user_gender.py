# Generated by Django 2.2.10 on 2020-03-13 20:37

from django.db import migrations, models
import user.enums


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_user_university_details'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='sex',
        ),
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.PositiveSmallIntegerField(choices=[(0, 'NONE'), (1, 'FEMALE'), (2, 'MALE'), (3, 'NON_BINARY')], default=user.enums.GenderType(0)),
        ),
    ]
