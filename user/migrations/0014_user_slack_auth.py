# Generated by Django 2.2.13 on 2021-03-14 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("user", "0013_user_resume")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="slack_scopes",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="slack_token",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
