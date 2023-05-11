from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@admin.register(User)
class MyUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("last_name", "first_name", "surname", "email")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_prosthetist",
                    "is_manager",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("name", "is_prosthetist", "is_manager", "id")
    list_filter = (
        "is_prosthetist",
        "is_manager",
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    )

    def name(self, obj):
        return obj

    name.short_description = "ФИО"
