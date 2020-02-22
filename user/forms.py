from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=255)
    password = forms.CharField(
        widget=forms.PasswordInput, label="Password", max_length=255
    )
