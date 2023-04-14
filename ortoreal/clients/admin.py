from django.contrib import admin
from django.db import models
from django.forms import Textarea

from clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "contract_date",
        "act_date",
        "phone",
        "address",
        "region",
        "passport",
        "IPR",
        "SprMSE",
        "bank_details",
        "parts",
        "contour",
    )
    list_display_links = ("full_name",)

    search_fields = ("full_name",)

    def full_name(self, obj):
        return obj.__str__()

    full_name.short_description = "ФИО Клиента"

    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }
