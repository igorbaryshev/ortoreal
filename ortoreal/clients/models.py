from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from phonenumber_field.modelfields import PhoneNumberField


class Client(models.Model):
    class Region(models.TextChoices):
        MOSCOW = "Moscow", _("Москва")
        MOSCOW_REGION = "Moscow region", _("Московская область")

    last_name = models.CharField(
        _("last name"), max_length=150, blank=False, default=None
    )
    first_name = models.CharField(
        _("first name"), max_length=150, blank=False, default=None
    )
    surname = models.CharField(_("отчество"), max_length=150, blank=True)
    contract_date = models.DateField(_("Дата договора"), default=timezone.now)
    act_date = models.DateField(
        _("Дата акта(дата чека)"), default=timezone.now
    )
    phone = PhoneNumberField(
        _("Телефон"), null=False, blank=False, unique=True
    )
    address = models.TextField(_("Адрес"), max_length=1000, blank=True)
    region = models.CharField(
        "Регион",
        max_length=128,
        choices=Region.choices,
        blank=False,
        default=None,
    )
    passport = models.BooleanField(_("Паспорт"), default=False)
    SNILS = models.BooleanField(_("СНИЛС"), default=False)
    IPR = models.BooleanField(_("ИПР"), default=False)
    SprMSE = models.BooleanField(_("СпрМСЭ"), default=False)
    bank_details = models.BooleanField(_("Реквизиты"), default=False)
    parts = models.BooleanField(_("Комплектующие"), default=False)
    contour = models.BooleanField(_("Контур"), default=False)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} {self.surname}"


class Comment(models.Model):
    text = models.TextField("Комментарий(примечание)")
    client = models.ForeignKey(
        Client, verbose_name="Клиент", on_delete=models.CASCADE
    )
    date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self) -> str:
        return f"{self.date} {self.text[:20]}"


class Status(models.Model):
    class StatusChoices(models.TextChoices):
        IN_WORK = "in work", _("Принят в работу")
        ISSUED = "issued", _("Выдан")
        DOCS_SUBMITTED = "docs submitted", _("Документы сданы")
        PAYMENT_TO_CLIENT = "payment to client", _("Оплата клиенту")
        PAYMENT = "payment", _("Оплата")

    name = models.CharField(
        "Статус", max_length=150, choices=StatusChoices.choices, blank=False
    )
    client = models.ForeignKey(
        Client, verbose_name="Клиент", on_delete=models.CASCADE
    )
    date = models.DateField(auto_now_add=True)
