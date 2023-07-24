import uuid
from typing import Iterable, Optional

from django.contrib.auth import get_user_model
from django.db import IntegrityError, models
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
    IN_WORK = "in work", _("принят в работу")
    ISSUED = "issued", _("выдан")
    DOCS_SUBMITTED = "docs submitted", _("документы сданы")
    PAYMENT_TO_CLIENT = "payment to client", _("оплата клиенту")
    PAYMENT = "payment", _("оплата")


# class ContactType(models.TextChoices):
#     THEY_CALLED = "they_called", _("звонок")
#     WE_CALLED = "we_called", _("обзвон")


class ContactTypeChoice(models.Model):
    name = models.CharField("название опции", max_length=128, blank=True)
    prosthetist = models.ForeignKey(
        User,
        verbose_name="протезист",
        limit_choices_to={"is_prosthetist": True},
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "откуда обратились"
        verbose_name_plural = "откуда обратились"

    def __str__(self) -> str:
        return str(self.prosthetist or self.name)


class Client(models.Model):
    class Region(models.TextChoices):
        MOSCOW = "Moscow", _("Москва")
        MOSCOW_REGION = "Moscow region", _("Московская область")

    def client_directory_path(self, filename):
        """
        Название директория для файлов клиента.
        """
        filename = (
            str(self.id)
            + "_"
            + str(uuid.uuid4())[:8]
            + "."
            + filename.rsplit(".", 1)[-1]
        )
        return f"clients/{self.id}/{filename}"

    last_name = models.CharField(
        _("last name"), max_length=150, blank=False, default=None
    )
    first_name = models.CharField(
        _("first name"), max_length=150, blank=False, default=None
    )
    surname = models.CharField(_("отчество"), max_length=150, blank=True)
    # contract_date = models.DateField(_("дата договора"), default=timezone.now)
    # act_date = models.DateField(_("дата акта(чека)"), default=timezone.now)
    phone = PhoneNumberField(
        _("телефон"), null=False, blank=False, unique=True
    )
    address = models.TextField(_("адрес"), max_length=1000, blank=True)
    prosthetist = models.ForeignKey(
        User,
        verbose_name="протезист",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        limit_choices_to={"is_prosthetist": True},
    )
    region = models.CharField(
        "регион",
        max_length=128,
        choices=Region.choices,
    )

    # passport = models.BooleanField(_("Паспорт"), default=False)
    passport = models.FileField(
        "паспорт", upload_to=client_directory_path, blank=True, null=True
    )
    # SNILS = models.BooleanField(_("СНИЛС"), default=False)
    snils = models.FileField(
        "СНИЛС", upload_to=client_directory_path, blank=True, null=True
    )
    # IPR = models.BooleanField(_("ИПР"), default=False)
    ipr = models.FileField(
        "ИПР", upload_to=client_directory_path, blank=True, null=True
    )
    # SprMSE = models.BooleanField(_("СпрМСЭ"), default=False)
    sprmse = models.FileField(
        "CпрМСЭ", upload_to=client_directory_path, blank=True, null=True
    )
    # bank_details = models.BooleanField(
    #    _("рекв."), default=False, help_text="реквизиты"
    # )
    bank_details = models.FileField(
        "реквизиты", upload_to=client_directory_path, blank=True, null=True
    )
    parts = models.BooleanField(
        "комплектующие",
        default=False,
        help_text="протезист дал комплектующие",
    )
    contour = models.BooleanField(
        "контур", default=False, help_text="выпуск в контуре"
    )

    def get_phone_display(self):
        return self.phone.as_national.replace(" ", "")

    def get_full_name(self):
        full_name = f"{self.last_name} {self.first_name}"
        if self.surname:
            full_name += " " + self.surname
        return full_name

    class Meta:
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"

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
        YES = "yes", _("да")
        NO = "no", _("нет")

    client = models.ForeignKey(
        Client, verbose_name="клиент", on_delete=models.CASCADE
    )
    call_date = models.DateField(_("дата звонка"), default=timezone.now)
    last_prosthesis_date = models.CharField(
        "предыдущий протез",
        max_length=150,
        default="первичн.",
        blank=True,
        help_text="примерная дата получения последнего протеза",
    )
    prosthesis_type = models.CharField("протез", max_length=150, blank=True)
    call_result = models.CharField(
        _("результат звонка"), max_length=1024, blank=True
    )
    comment = models.CharField(
        _("комментарий"),
        max_length=1024,
        blank=True,
        help_text="комментарий протезиста",
    )
    MTZ_date = models.DateField(_("МТЗ"), blank=True, null=True)
    result = models.CharField(
        _("результат"),
        max_length=16,
        blank=True,
        choices=YesNo.choices,
        help_text="согласились или нет",
    )

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields]

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"

    def __str__(self) -> str:
        return f"{self.client}"

    def save(self, *args, **kwargs):
        """
        Создаём работу, если клиент согласился в обращении.
        """
        super().save(*args, **kwargs)
        if self.result == Contact.YesNo.YES:
            Job.objects.get_or_create(client=self.client)


class Comment(models.Model):
    contact = models.ForeignKey(
        Contact,
        verbose_name="контакт",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField("комментарий(примечание)")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "комментарий"
        verbose_name_plural = "комментарии"

    def __str__(self) -> str:
        return f"{self.date} {self.text[:20]}"


class Status(models.Model):
    name = models.CharField(
        "статус",
        max_length=150,
        choices=StatusChoices.choices,
        blank=False,
        null=False,
        default=StatusChoices.IN_WORK,
    )
    job = models.ForeignKey(
        "Job",
        verbose_name="работа",
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    date = models.DateTimeField("дата", default=timezone.now)
    comment = models.TextField("комментарий", blank=True)

    def __str__(self) -> str:
        date = date_format(
            self.date, format="SHORT_DATE_FORMAT", use_l10n=True
        )
        return f"{self.get_name_display()} {date}"

    class Meta:
        verbose_name = "статус"
        verbose_name_plural = "статусы"


class Job(models.Model):
    client = models.ForeignKey(
        Client,
        verbose_name="клиент",
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    how_contacted = models.ForeignKey(
        ContactTypeChoice,
        verbose_name="откуда обратились",
        on_delete=models.SET_NULL,
        null=True,
    )
    prosthetist = models.ForeignKey(
        User,
        verbose_name="протезист",
        on_delete=models.SET_NULL,
        null=True,
        related_name="jobs",
        limit_choices_to={"is_prosthetist": True},
    )
    prosthesis = models.ForeignKey(
        "inventory.Prosthesis",
        verbose_name="протез",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    date = models.DateTimeField(_("date"), default=timezone.now)
    # status = models.CharField(
    # _("статус"), max_length=150, choices=StatusChoices.choices, blank=True
    # )

    @property
    def status_display(self):
        if self.statuses.exists():
            return str(self.statuses.latest("date"))
            # date = date_format(
            # status.date, format="SHORT_DATE_FORMAT", use_l10n=True
            # )
            # return f"{status.name} {date}"
        return "—нет статуса—"

    status_display.fget.short_description = "статус"

    class Meta:
        verbose_name = "работа"
        verbose_name_plural = "работы"

    def __str__(self) -> str:
        return f"{self.client} ({self.status_display})"

    def save(self, *args, **kwargs):
        """
        Проверяем, что регион клиента и протеза одинаковые.
        """
        if self.prosthesis and self.client.region != self.prosthesis.region:
            raise IntegrityError("регион клиента и протеза должны быть равны")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("clients:job", kwargs={"pk": self.pk})
