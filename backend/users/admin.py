from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import User


@register(User)
class UserAdminConfig(UserAdmin):
    list_display = (
        "pk",
        "email",
        "username",
        "first_name",
        "last_name",
        "avatar",
        "password",
        "recipes_count",
        "subscriptions_count",
        "subscribers_count",
    )
    list_filter = ("username", "email")
    search_fields = ("username", "email")

    @admin.display(description="Количество подписчиков")
    def subscribers_count(self, obj):
        return obj.subscribers.count()

    @admin.display(description="Количество подписок")
    def subscriptions_count(self, obj):
        return obj.subscriptions.count()

    @admin.display(description="Количество рецептов")
    def recipes_count(self, obj):
        return obj.recipes.count()
