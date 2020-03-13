from django.contrib import auth, messages
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from user import forms


def user_login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("app_home"))

    if request.method == "POST":
        form = forms.LoginForm(request.POST)
        next_page = request.GET.get("next", "/")
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
    if request.user.is_authenticated and request.user.email_verified and request.user.registration_finished:
        return HttpResponseRedirect(reverse("app_home"))

    if request.method == "POST":
        form = forms.LoginForm(request.POST)
        next_page = request.GET.get("next", "/")
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
                    request, "Registration failed, the email or password are invalid."
                )
        else:
            messages.error(
                request, "Some required fields haven't been entered correctly."
            )
    else:
        form = forms.LoginForm()

    return render(request, "register.html", {"form": form})
