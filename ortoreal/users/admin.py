from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("name", "is_prosthetist", "id")

    def name(self, obj):
        return obj
    name.short_description = "ФИО"
