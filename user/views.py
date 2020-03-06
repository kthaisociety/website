from django.contrib import auth, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from user import forms


def login(request):
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
                    request, "Login failed, the email or password are invalid!"
                )
    else:
        form = forms.LoginForm()

    return render(request, "login.html", {"form": form})
