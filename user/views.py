import datetime
from typing import Optional, Tuple

from django.contrib import auth, messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files import File
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from geopy import Nominatim

from app import settings
from app.consts import UNIVERSITIES, PROGRAMMES
from app.variables import APP_NAME
from user import forms
from user.enums import GenderType
from user.models import User, validate_orcid
from user.utils import send_verify, send_password, get_user_data_zip, delete_user_account


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
                    return HttpResponseRedirect(reverse("user_dashboard"))
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
            messages.success(
                request,
                "If an account exists with the email a link will be sent, please check your inbox and spam folders.",
            )
            return HttpResponseRedirect(reverse("user_login"))

    return render(request, "password.html", {"form": form})


def verify_password(request, email, verification_key):
    user = User.objects.filter(
        email=email, verify_key=verification_key, verify_expiration__gte=timezone.now()
    ).first()

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
                    user.email_verified = True
                    user.delete_verify_key()
                    user.save()
                    messages.success(
                        request, "Your password has been successfully updated."
                    )
                    auth.login(request, user)
                    return HttpResponseRedirect(reverse("app_home"))
            else:
                messages.error(request, "Passwords are required fields.")

        return render(request, "verify_password.html", {"user": user})

    return HttpResponseRedirect(reverse("app_home"))


def get_city_and_country(city: str, country: str) -> Optional[Tuple[str, str]]:
    new_country = country
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
        new_country = location.raw["address"]["country"]
        # Wink, wink
        if new_country.lower() == "spain" and country.lower().strip().startswith("cat"):
            new_country = "Catalonia"
    except (AttributeError, KeyError):
        return None
    return city, new_country


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
        other_university = request.POST.get("other_university", None)
        degree = request.POST.get("degree", None)
        graduation_year = request.POST.get("graduation", None)
        birthday = request.POST.get("birthday", None)
        gender = request.POST.get("gender", None)
        city = request.POST.get("city", None)
        country = request.POST.get("country", None)
        error_location = False
        if city and country:
            city_and_country = get_city_and_country(city=city, country=country)
            if not city_and_country:
                error_location = True
                messages.error(
                    request,
                    f"We haven't been able to locate {city} ({country}), please, check this place exists!",
                )
            else:
                city, country = city_and_country
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
        # 2 other selections at the end of UNIVERSITIES
        if university and int(university) >= len(UNIVERSITIES) - 2:
            university_str = other_university
            form["university_name"] = university_str
        else:
            university_str = UNIVERSITIES[int(university)]
        missing_required = [
            field_name for field_name, field in form.items() if not field
        ]
        if request.user.is_authenticated:
            missing_required = [
                field
                for field in missing_required
                if field not in ["email", "password", "repeat_password"]
            ]
        form = {**form, "phone": phone, "birthday": birthday, "gender": gender}
        if not missing_required and not error_location:
            if password != password2:
                messages.error(request, "Passwords do not match.")
            else:
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
                            university=university_str,
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
                        university=university_str,
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


@login_required
def dashboard(request):
    form = {}
    if request.method == "POST":
        name = request.POST.get("name", None)
        surname = request.POST.get("surname", None)
        phone = request.POST.get("phone", None)
        university = request.POST.get("university", None)
        other_university = request.POST.get("other_university", None)
        degree = request.POST.get("degree", None)
        graduation_year = request.POST.get("graduation", None)
        birthday = request.POST.get("birthday", None)
        gender = request.POST.get("gender", None)
        city = request.POST.get("city", None)
        country = request.POST.get("country", None)
        website = request.POST.get("website", None)
        linkedin_url = request.POST.get("linkedin_url", None)
        twitter_url = request.POST.get("twitter_url", None)
        github_url = request.POST.get("github_url", None)
        scholar_url = request.POST.get("scholar_url", None)
        researchgate_url = request.POST.get("researchgate_url", None)
        orcid = request.POST.get("orcid", None)
        error_location = False
        if city and country:
            city_and_country = get_city_and_country(city=city, country=country)
            if not city_and_country:
                error_location = True
                messages.error(
                    request,
                    f"We haven't been able to locate {city} ({country}), please, check this place exists!",
                )
            else:
                city, country = city_and_country
        form = {
            "first_name": name,
            "last_name": surname,
            "university": university,
            "programme": degree,
            "graduation_year": graduation_year,
            "city": city,
            "country": country,
        }
        # 2 other selections at the end of UNIVERSITIES
        if university and int(university) >= len(UNIVERSITIES) - 2:
            university_str = other_university
            form["university_name"] = university_str
        else:
            university_str = UNIVERSITIES[int(university)]
        missing_required = [
            field_name for field_name, field in form.items() if not field
        ]
        form = {
            **form,
            "phone": phone,
            "birthday": birthday,
            "gender": gender,
            "website": website,
            "linkedin_url": linkedin_url,
            "twitter_url": twitter_url,
            "scholar_url": scholar_url,
            "orcid": orcid,
        }
        if not missing_required and not error_location:
            degree = PROGRAMMES[int(degree)]
            if gender:
                gender = GenderType(int(gender))
            else:
                gender = GenderType.NONE
            request.user.name = name
            request.user.surname = surname
            request.user.phone = phone
            request.user.university = university_str
            request.user.degree = degree
            request.user.graduation_year = graduation_year
            request.user.city = city
            request.user.country = country
            if birthday:
                request.user.birthday = datetime.datetime.strptime(
                    birthday, "%Y-%m-%d"
                ).date()
            else:
                request.user.birthday = None
            request.user.gender = gender
            request.user.website = website
            request.user.linkedin_url = linkedin_url
            request.user.twitter_url = twitter_url
            request.user.github_url = github_url
            request.user.scholar_url = scholar_url
            request.user.researchgate_url = researchgate_url

            try:
                validate_orcid(orcid)
                request.user.orcid = orcid
            except ValidationError as e:
                messages.error(request, e.message)

            resume = request.FILES.get("resume")
            if resume:
                request.user.resume = resume

            messages.success(request, "Your profile has been correctly updated.")

            request.user.save()
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

    return render(request, "dashboard.html", form)


@login_required
def dashboard_resume(request):
    response = StreamingHttpResponse(
        open(settings.MEDIA_ROOT + "/" + request.user.resume.name, "rb")
    )
    response["Content-Type"] = ""
    response[
        "Content-Disposition"
    ] = f'attachment; filename="{request.user.resume_name}"'
    return response


@login_required
def user_data(request):
    data = get_user_data_zip(user_id=request.user.id)

    response = HttpResponse(data.getvalue(), content_type="application/zip")
    file_name = f"{APP_NAME.replace(' ', '').lower()}_data_{str(request.user.id)}_{str(int(timezone.now().timestamp()))}.zip"
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    return response

@login_required
def user_delete(request):
    delete_user_account(user_id=request.user.id)
    
    messages.success(request, "User successfully deleted")
    return redirect('/')
