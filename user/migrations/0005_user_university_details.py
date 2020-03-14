# Generated by Django 2.2.10 on 2020-03-13 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_googleuser'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='degree',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='graduation_year',
            field=models.PositiveIntegerField(blank=True, default=2020, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='university',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]