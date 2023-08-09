from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ModelForm, Textarea
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from clients.models import (
    BankDetails,
    Client,
    Comment,
    Contact,
    ContactTypeChoice,
    Job,
    Passport,
    Status,
)
from inventory.models import Item

User = get_user_model()


class ClientAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prosthetist"].queryset = User.objects.filter(
            is_prosthetist=True
        )


class JobAdminForm(ModelForm):
    def clean(self):
        client = self.cleaned_data["client"]
        prosthesis = self.cleaned_data["prosthesis"]
        if client.region != prosthesis.region:
            raise forms.ValidationError(
                {
                    "prosthesis": "регион протеза не может отличаться от региона клиента"
                }
            )


class CommentInline(admin.TabularInline):
    model = Comment
    fk_name = "contact"
    extra = 1
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    inlines = [
        CommentInline,
    ]
    list_display = (
        "full_name",
        "call_date",
        "last_prosthesis_date",
        "call_result",
        "comments",
        "MTZ_date",
        "result",
    )
    ordering = ("result", "-call_date")

    def full_name(self, obj):
        return obj.__str__()

    full_name.short_description = "ФИО клиента"

    def comments(self, obj):
        if obj.comments.exists():
            comment = obj.comments.latest("date")
            return mark_safe(f"{comment.date.date()}<br>{comment.text[:20]}")

    comments.short_description = "комментарии"

    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }


class ContactInline(admin.StackedInline):
    model = Contact
    fk_name = "client"
    ordering = ("-call_date",)
    extra = 0
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }


class JobInline(admin.StackedInline):
    model = Job
    fk_name = "client"
    extra = 0
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }


class PassportInline(admin.StackedInline):
    model = Passport
    fk_name = "client"
    extra = 1
    max_num = 1


class BankDetailsInline(admin.StackedInline):
    model = BankDetails
    fk_name = "client"
    extra = 1
    max_num = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    form = ClientAdminForm

    list_display = (
        "full_name",
        # "contract_date",
        # "act_date",
        "phone",
        "address",
        # "how_contacted",
        "prosthetist",
        "region",
        # "admin_status_display",
        "Passport",
        "SNILS",
        "IPR",
        "SprMSE",
        "Bank_Details",
        # "parts",
        # "contour",
    )
    inlines = [
        PassportInline,
        BankDetailsInline,
        ContactInline,
        JobInline,
    ]
    list_display_links = ("full_name",)

    search_fields = ("full_name",)

    def full_name(self, obj):
        return str(obj)

    full_name.short_description = "ФИО клиента"

    def Passport(self, obj):
        if obj.passport.exists():
            return True
        return False

    Passport.boolean = True
    Passport.short_description = "паспорт"

    def SNILS(self, obj):
        if obj.snils:
            return True
        return False

    SNILS.boolean = True
    SNILS.short_description = "СНИЛС"

    def IPR(self, obj):
        if obj.ipr:
            return True
        return False

    IPR.boolean = True
    IPR.short_description = "ИПР"

    def SprMSE(self, obj):
        if obj.sprmse:
            return True
        return False

    SprMSE.boolean = True
    SprMSE.short_description = "СпрMCЭ"

    def Bank_Details(self, obj):
        if obj.bank_details.exists():
            return True
        return False

    Bank_Details.boolean = True
    Bank_Details.short_description = "рекв."

    # def admin_status_display(self, obj):
    #     return format_html_join(
    #         mark_safe("<br/>"),
    #         "{}",
    #         ((line,) for line in obj.status_display),
    #     )

    # admin_status_display.short_description = "Статус"

    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }


class ItemInline(admin.TabularInline):
    model = Item
    fk_name = "reserved"


class StatusInline(admin.TabularInline):
    model = Status
    fk_name = "job"
    extra = 0
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 2, "cols": 60})},
    }


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    inlines = [
        #    ItemInline,
        StatusInline,
    ]
    list_display = ("client", "prosthesis", "prosthetist", "date", "status")

    def status(self, obj):
        return str(obj.status_display)

    status.short_description = "cтатус"


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "client", "prosthetist")

    def client(self, obj):
        return obj.job.client

    client.short_description = "клиент"

    def prosthetist(self, obj):
        return obj.job.prosthetist

    prosthetist.short_description = "протезист"
