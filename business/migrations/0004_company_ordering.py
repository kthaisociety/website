# Generated by Django 3.1.13 on 2021-09-23 13:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0003_offer_email'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'ordering': ['name'], 'verbose_name_plural': 'companies'},
        ),
    ]