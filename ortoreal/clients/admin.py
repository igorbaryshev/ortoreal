from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models
from django.forms import Textarea, ModelForm
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from clients.models import Client, Contact

User = get_user_model()


class ClientAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prosthetist"].queryset = User.objects.filter(
            is_prosthetist=True
        )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "call_date",
        "last_prosthesis_date",
        "call_result",
        "comment",
        "MTZ_date",
        "result",
    )

    def full_name(self, obj):
        return obj.__str__()

    full_name.short_description = "ФИО Клиента"

    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    form = ClientAdminForm

    list_display = (
        "full_name",
        "contract_date",
        "act_date",
        "phone",
        "address",
        "how_contacted",
        "prosthetist",
        "region",
        "admin_status_display",
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

    def admin_status_display(self, obj):
        return format_html_join(
            mark_safe("<br/>"),
            "{}",
            ((line,) for line in obj.status_display),
        )

    admin_status_display.short_description = "Статус"

    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }
