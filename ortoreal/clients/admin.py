from django.contrib import admin

from clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name",)
    list_display_links = ("full_name",)

    search_fields = ("full_name",)

    def full_name(self, obj):
        return obj.__str__()

    full_name.short_description = "ФИО Клиента"
