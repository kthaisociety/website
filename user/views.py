import datetime

from django.contrib import auth, messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from user import forms
from user.enums import GenderType
from user.models import User
from user.utils import send_verify


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
        form = {
            "first_name": name,
            "last_name": surname,
            "email": email,
            "password": password,
            "repeat_password": password2,
            "university": university,
            "programme": degree,
            "graduation_year": graduation_year,
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
        if not missing_required:
            if password != password2:
                messages.error(request, "Passwords do not match.")
            if request.user.is_authenticated:
                try:
                    request.user.finish_registration(
                        name=name,
                        surname=surname,
                        phone=phone,
                        university=university,
                        degree=degree,
                        graduation_year=graduation_year,
                        birthday=(datetime.datetime.strptime(birthday, "%Y-%m-%d").date() if birthday else None),
                        gender=(gender if gender else GenderType.NONE),
                        city=city,
                        country=country,
                    )
                    messages.success(request, "Thank-you for completing the registration.")
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
                    birthday=(datetime.datetime.strptime(birthday, "%Y-%m-%d").date() if birthday else None),
                    gender=(gender if gender else GenderType.NONE),
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
        else:
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
