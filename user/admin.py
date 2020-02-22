from django.contrib import admin

from user.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ("id", "email", "name", "surname", "type")
    list_display = ("email", "name", "surname", "type")
    list_filter = ("type", "email_verified", "is_active")
    ordering = ("name", "surname", "email", "type")
