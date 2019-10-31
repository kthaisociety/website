import factory

from user.models import User


class UserFactory(factory.DjangoModelFactory):
    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda u: "{0}.{1}@not-kthack.com".format(u.name, u.surname).lower()
    )

    class Meta:
        model = User
