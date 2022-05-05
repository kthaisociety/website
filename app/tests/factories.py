import factory

from user.models import User


class UserFactory(factory.DjangoModelFactory):
    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda u: f"{u.name}.{u.surname}@not-kthack.com".lower()
    )

    class Meta:
        model = User
