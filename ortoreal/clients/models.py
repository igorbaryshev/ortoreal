from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CharField, Value
from django.db.models.functions import Cast, Concat, Substr
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


class StatusChoices(models.TextChoices):
    IN_WORK = "in work", _("Принят в работу")
    ISSUED = "issued", _("Выдан")
    DOCS_SUBMITTED = "docs submitted", _("Документы сданы")
    PAYMENT_TO_CLIENT = "payment to client", _("Оплата клиенту")
    PAYMENT = "payment", _("Оплата")


class ContactType(models.TextChoices):
    THEY_CALLED = "they_called", _("Звонок")
    WE_CALLED = "we_called", _("Обзвон")


def get_contact_type_choices():
    prosthetists = (
        User.objects.filter(is_prosthetist=True)
        .annotate(
            id_as_str=Cast("id", output_field=CharField()),
            initials=Concat(
                Substr("last_name", 1, 1), Substr("first_name", 1, 1)
            ),
        )
        .values_list("id_as_str", "initials")
    )
    return ContactType.choices + list(prosthetists)


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
    act_date = models.DateField(_("Дата акта(чека)"), default=timezone.now)
    phone = PhoneNumberField(
        _("Телефон"), null=False, blank=False, unique=True
    )
    address = models.TextField(_("Адрес"), max_length=1000, blank=True)
    how_contacted = models.CharField(_("Откуда обратились"), max_length=150)
    prosthetist = models.ForeignKey(
        User,
        verbose_name="Протезист",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        limit_choices_to={"is_prosthetist": True},
    )
    region = models.CharField(
        "Регион",
        max_length=128,
        choices=Region.choices,
        blank=True,
        default=None,
    )

    passport = models.BooleanField(_("Паспорт"), default=False)
    SNILS = models.BooleanField(_("СНИЛС"), default=False)
    IPR = models.BooleanField(_("ИПР"), default=False)
    SprMSE = models.BooleanField(_("СпрМСЭ"), default=False)
    bank_details = models.BooleanField(
        _("Рекв."), default=False, help_text="Реквизиты"
    )
    parts = models.BooleanField(
        _("Компл."),
        default=False,
        help_text="Протезист дал комплектующие",
    )
    contour = models.BooleanField(
        _("Контур"), default=False, help_text="Выпуск в контуре"
    )

    def get_phone_display(self):
        return self.phone.as_national.replace(" ", "")

    def get_full_name(self):
        full_name = f"{self.last_name} {self.first_name}"
        if self.surname:
            full_name += " " + self.surname
        return full_name

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self) -> str:
        return self.get_full_name()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # if self.status:
        #     Status.objects.create(name=self.status, client=self)

    def get_absolute_url(self):
        return reverse("clients:client", kwargs={"pk": self.pk})


class Contact(models.Model):
    class YesNo(models.TextChoices):
        YES = "yes", _("Да")
        NO = "no", _("Нет")

    client = models.ForeignKey(
        Client, verbose_name="Клиент", on_delete=models.CASCADE
    )
    call_date = models.DateField(_("Дата звонка"), default=timezone.now)
    last_prosthesis_date = models.CharField(
        "Пред. протез",
        max_length=150,
        default="первичн",
        blank=True,
        help_text="Примерная дата получения последнего протеза",
    )
    prosthesis_type = models.CharField("Протез", max_length=150, blank=True)
    call_result = models.CharField(
        _("Результат звонка"), max_length=1024, blank=True
    )
    comment = models.CharField(
        _("Комментарий"),
        max_length=1024,
        blank=True,
        help_text="Комментарий протезиста",
    )
    MTZ_date = models.DateField(_("МТЗ"), blank=True, null=True)
    result = models.CharField(
        _("Результат"),
        max_length=16,
        blank=True,
        choices=YesNo.choices,
        help_text="Согласились или нет",
    )

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields]

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"

    def __str__(self) -> str:
        return f"{self.client}"


class Comment(models.Model):
    text = models.TextField("Комментарий(примечание)")
    client = models.ForeignKey(
        Client,
        verbose_name="Клиент",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self) -> str:
        return f"{self.date} {self.text[:20]}"


class Status(models.Model):
    name = models.CharField(
        "Статус", max_length=150, choices=StatusChoices.choices, blank=False
    )
    job = models.ForeignKey(
        "Job",
        verbose_name="Работа",
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    date = models.DateTimeField("Дата", auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name}({self.date})"

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"


class Job(models.Model):
    prosthesis = models.ForeignKey(
        "inventory.Prosthesis",
        verbose_name="Протез",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    client = models.ForeignKey(
        Client,
        verbose_name="Клиент",
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    prosthetist = models.ForeignKey(
        User,
        verbose_name="Протезист",
        on_delete=models.SET_NULL,
        null=True,
        related_name="jobs",
        limit_choices_to={"is_prosthetist": True},
    )
    date = models.DateTimeField("Дата", default=timezone.now)
    status = models.CharField(
        _("Статус"), max_length=150, choices=StatusChoices.choices, blank=True
    )

    @property
    def status_display(self):
        statuses = self.statuses.order_by("-date")
        if statuses:
            date = date_format(
                statuses[0].date, format="SHORT_DATE_FORMAT", use_l10n=True
            )
            return f"{self.get_status_display()} {date}"
        return ("--нет статуса--",)

    status_display.fget.short_description = "Статус"

    class Meta:
        verbose_name = "Работа"
        verbose_name_plural = "Работы"

    def __str__(self) -> str:
        return f"{self.client} ({self.status_display})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.statuses.filter(name=self.status).exists():
            new_status = Status(name=self.status, job=self)
            new_status.save()

    def get_absolute_url(self):
        return reverse("clients:job", kwargs={"pk": self.pk})
