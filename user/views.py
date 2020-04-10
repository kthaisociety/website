import datetime

from django.contrib import auth, messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from geopy import Nominatim

from app.consts import UNIVERSITIES, PROGRAMMES
from user import forms
from user.enums import GenderType
from user.models import User
from user.utils import send_verify, send_password


def user_login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("app_home"))

    if request.method == "POST":
        form = forms.LoginForm(request.POST)
        next_page = request.POST.get("next", "/")
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = auth.authenticate(email=email, password=password)
            if user:
                auth.login(request, user)
                if next_page == "/":
                    return HttpResponseRedirect(reverse("app_home"))
                return HttpResponseRedirect(next_page)
            else:
                messages.error(
                    request, "Login failed, the email or password are invalid."
                )
        else:
            messages.error(
                request, "You need to provide both email and password to login."
            )
    else:
        form = forms.LoginForm()

    return render(request, "login.html", {"form": form})


def user_logout(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("app_home"))

    logout(request)

    return HttpResponseRedirect(reverse("app_home"))


def user_password(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("app_home"))

    form = {}

    if request.method == "POST":
        email = request.POST.get("email", None)
        form["email"] = email

        if not email:
            messages.error(request, "Email is a required field.")
        else:
            user = User.objects.filter(email=email).first()
            if user:
                send_password(user)
            messages.success(request, "If an account exists with the email a link will be sent, please check your inbox and spam folders.")
            return HttpResponseRedirect(reverse("user_login"))

    return render(request, "password.html", {"form": form})


def verify_password(request, email, verification_key):
    user = User.objects.filter(email=email, verify_key=verification_key, verify_expiration__gte=timezone.now()).first()

    if user:
        if request.method == "POST":
            password = request.POST.get("password", None)
            password2 = request.POST.get("password2", None)

            if password and password2:
                if password != password2:
                    messages.error(request, "Passwords do not match.")
                else:
                    user.backend = "django.contrib.auth.backends.ModelBackend"
                    user.set_password(password)
                    user.delete_verify_key()
                    user.save()
                    messages.success(request, "Your password has been successfully updated.")
                    auth.login(request, user)
                    return HttpResponseRedirect(reverse("app_home"))
            else:
                messages.error(request, "Passwords are required fields.")

        return render(request, "verify_password.html", {"user": user})

    return HttpResponseRedirect(reverse("app_home"))


def user_register(request):
    if (
        request.user.is_authenticated
        and request.user.email_verified
        and request.user.registration_finished
    ):
        return HttpResponseRedirect(reverse("app_home"))
    form = dict()

    if request.method == "POST":
        next_page = request.POST.get("next", "/")
        name = request.POST.get("name", None)
        surname = request.POST.get("surname", None)
        email = request.POST.get("email", None)
        password = request.POST.get("password", None)
        password2 = request.POST.get("password2", None)
        phone = request.POST.get("phone", None)
        university = request.POST.get("university", None)
        degree = request.POST.get("degree", None)
        graduation_year = request.POST.get("graduation", None)
        birthday = request.POST.get("birthday", None)
        gender = request.POST.get("gender", None)
        city = request.POST.get("city", None)
        country = request.POST.get("country", None)
        error_location = False
        if city and country:
            try:
                geolocator = Nominatim()
                location = geolocator.geocode(
                    f"{city}, {country}", language="en", addressdetails=True
                )
                try:
                    city = location.raw["address"]["city"]
                except KeyError:
                    try:
                        city = location.raw["address"]["village"]
                    except KeyError:
                        city = location.raw["address"]["suburb"]
                country = location.raw["address"]["country"]
            except (AttributeError, KeyError):
                error_location = True
                messages.error(
                    request,
                    f"We haven't been able to locate {city} ({country}), please, check this place exists!",
                )
        form = {
            "first_name": name,
            "last_name": surname,
            "email": email,
            "password": password,
            "repeat_password": password2,
            "university": university,
            "programme": degree,
            "graduation_year": graduation_year,
            "city": city,
            "country": country,
        }
        missing_required = [
            field_name for field_name, field in form.items() if not field
        ]
        if request.user.is_authenticated:
            missing_required = [
                field
                for field in missing_required
                if field not in ["email", "password", "repeat_password"]
            ]
        form = {
            **form,
            "phone": phone,
            "birthday": birthday,
            "gender": gender,
            "city": city,
            "country": country,
        }
        if not missing_required and not error_location:
            if password != password2:
                messages.error(request, "Passwords do not match.")
            else:
                university = UNIVERSITIES[int(university)]
                degree = PROGRAMMES[int(degree)]
                if gender:
                    gender = GenderType(int(gender))
                else:
                    gender = GenderType.NONE
                if request.user.is_authenticated:
                    try:
                        request.user.finish_registration(
                            name=name,
                            surname=surname,
                            phone=phone,
                            university=university,
                            degree=degree,
                            graduation_year=graduation_year,
                            birthday=(
                                datetime.datetime.strptime(birthday, "%Y-%m-%d").date()
                                if birthday
                                else None
                            ),
                            gender=gender,
                            city=city,
                            country=country,
                        )
                        messages.success(
                            request, "Thank-you for completing the registration."
                        )
                    except ValidationError as e:
                        for errors in e.error_dict.values():
                            for msgs in errors:
                                for msg in msgs:
                                    messages.error(request, msg + ".")
                else:
                    User.objects.create_participant(
                        email=email,
                        password=password,
                        name=name,
                        surname=surname,
                        phone=phone,
                        birthday=(
                            datetime.datetime.strptime(birthday, "%Y-%m-%d").date()
                            if birthday
                            else None
                        ),
                        gender=gender,
                        city=city,
                        country=country,
                        university=university,
                        degree=degree,
                        graduation_year=graduation_year,
                    )
                    user = auth.authenticate(email=email, password=password)
                    send_verify(user)
                    auth.login(request, user)
                    messages.success(
                        request,
                        "Thank-you for registering, remember to confirm your email.",
                    )
                return HttpResponseRedirect(reverse("app_home"))
        elif missing_required:
            messages.error(
                request,
                ", ".join(missing_required[:-1]).replace("_", " ").capitalize()
                + (
                    " and " + missing_required[-1].replace("_", " ")
                    if len(missing_required) >= 2
                    else ""
                )
                + (
                    " are required fields."
                    if len(missing_required) > 1
                    else missing_required[0].replace("_", " ").capitalize()
                    + " is a required field."
                ),
            )
    return render(request, "register.html", {"form": form})


@login_required
def verify(request, verification_key):
    if request.user.email_verified:
        return HttpResponseRedirect(reverse("app_home"))
    request.user.verify(verify_key=verification_key)
    if request.user.email_verified:
        messages.success(request, "Thank-you, your email has been verified.")
    else:
        messages.error(
            request, "We couldn't verify your email as the verification key expired."
        )
    return HttpResponseRedirect(reverse("app_home"))


@login_required
def send_verification(request):
    send_verify(request.user)
    messages.success(request, "The verification email has been sent again.")
    return HttpResponseRedirect(reverse("app_home"))
