import factory
import pytest
from django.test import Client

from app.tests.factories import UserFactory


@pytest.mark.django_db
def test_login():
    # Create a user
    password = factory.Faker("word")
    user = UserFactory(
        password=factory.PostGenerationMethodCall("set_password", password)
    )

    # Create a client
    client = Client()

    # Login
    assert client.login(username=user.email, password=password)
