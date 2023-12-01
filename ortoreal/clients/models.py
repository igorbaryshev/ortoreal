import uuid
from tabnanny import verbose
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


class Status(models.Model):
    class StatusNames(models.TextChoices):
        IN_WORK = "in work", _("принят в работу")
        ISSUED = "issued", _("выдан")
        DOCS_SUBMITTED = "docs submitted", _("документы сданы")
        PAYMENT_TO_CLIENT = "payment to client", _("оплата клиенту")
        PAYMENT = "payment", _("оплата")

    class StatusColors(models.TextChoices):
        IN_WORK = "in work", "B6D7A8"
        ISSUED = "issued", "6AA84F"
        DOCS_SUBMITTED = "docs submitted", "34A853"
        PAYMENT_TO_CLIENT = "payment to client", "00FFFF"
        PAYMENT = "payment", "6D9EEB"

    name = models.CharField(
        "статус",
        max_length=150,
        choices=StatusNames.choices,
        default=StatusNames.IN_WORK,
        blank=False,
        null=False,
    )
    job = models.ForeignKey(
        "Job",
        verbose_name="работа",
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    date = models.DateTimeField("дата", default=timezone.now)
    comment = models.TextField("комментарий", blank=True)
    color = models.CharField(
        "цвет",
        max_length=150,
        choices=StatusColors.choices,
        default=StatusColors.IN_WORK,
        blank=False,
        null=False,
    )

    def __str__(self) -> str:
        date = date_format(
            timezone.localdate(self.date), format="SHORT_DATE_FORMAT", use_l10n=True
        )
        return f"{self.get_name_display()} {date}"

    class Meta:
        verbose_name = "статус"
        verbose_name_plural = "статусы"

    def save(self, *args, **kwargs):
        self.color = self.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "clients:edit_job_status",
            kwargs={"pk": self.job.pk, "status_pk": self.pk},
        )


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
    birth_date = models.DateField(_("дата рождения"), blank=True, null=True)
    phone = PhoneNumberField(_("телефон"), blank=False, null=False, unique=True)
    address = models.TextField(_("адрес"), max_length=1000)
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
    snils = models.CharField("СНИЛС", blank=True, null=True)
    snils_scan = models.FileField(
        "скан СНИЛС", upload_to=client_directory_path, blank=True, null=True
    )
    ipr = models.FileField(
        "ИПР", upload_to=client_directory_path, blank=True, null=True
    )

    sprmse = models.FileField(
        "CпрМСЭ", upload_to=client_directory_path, blank=True, null=True
    )

    def get_phone_display(self):
        return self.phone.as_national.replace(" ", "")

    def get_full_name(self):
        full_name = f"{self.last_name} {self.first_name}"
        if self.surname:
            full_name += " " + self.surname
        return full_name

    def get_name_with_initials(self):
        name = f"{self.last_name} {self.first_name[0]}."
        if self.surname:
            name += f"{self.surname[0]}."
        return name

    @property
    def full_name(self):
        return self.get_full_name()

    def get_latest_job_statuses(self):
        statuses = []
        for job in self.jobs.all():
            statuses.append(job.status_display)
        return statuses

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


class Passport(models.Model):
    def passport_directory_path(self, filename):
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
        return f"passport/{self.id}/{filename}"

    client = models.ForeignKey(
        Client,
        verbose_name="клиент",
        on_delete=models.CASCADE,
        related_name="passport",
    )
    series = models.CharField("серия", max_length=4)
    number = models.CharField("номер", max_length=6)
    date_of_issue = models.DateField("дата выдачи")
    who_issued = models.CharField("кем выдан", max_length=1024)
    division_code = models.CharField("код подразделения", max_length=7)
    scan = models.FileField(
        "скан", upload_to=passport_directory_path, blank=True, null=True
    )

    class Meta:
        verbose_name = "паспортные данные"


class BankDetails(models.Model):
    client = models.ForeignKey(
        Client,
        verbose_name="клиент",
        on_delete=models.CASCADE,
        related_name="bank_details",
    )
    account_number = models.CharField("№ Счёта (р/с)", max_length=20)
    bank = models.CharField("в банке (название)", max_length=1024)
    BIC = models.CharField("БИК", max_length=8)
    correspondent_account = models.CharField("к/с", max_length=20)

    class Meta:
        verbose_name = "реквизиты"


class Contact(models.Model):
    class YesNo(models.TextChoices):
        YES = "yes", _("да")
        NO = "no", _("нет")

    client = models.ForeignKey(
        Client,
        verbose_name="клиент",
        on_delete=models.CASCADE,
        related_name="contacts",
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
    call_result = models.CharField(_("результат звонка"), max_length=1024, blank=True)
    # comment = models.CharField(
    #     _("комментарий"),
    #     max_length=1024,
    #     blank=True,
    #     help_text="комментарий протезиста",
    # )

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
        verbose_name = "обращение"
        verbose_name_plural = "обращения"

    def __str__(self) -> str:
        return f"{self.client}"

    # def save(self, *args, **kwargs):
    #     """
    #     Создаём работу, если клиент согласился в обращении.
    #     """
    #     super().save(*args, **kwargs)
    #     if self.result == Contact.YesNo.YES:
    #         Job.objects.get_or_create(client=self.client)


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
        return f"{self.date.date()} {self.text[:20]}"


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
    is_finished = models.BooleanField("завершена", default=False)

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
        client_name = self.client.get_name_with_initials()
        return f"{self.prosthesis}, {client_name} ({self.status_display})"

    def save(self, *args, **kwargs):
        """
        Проверяем, что регион клиента и протеза одинаковые.
        """
        if self.prosthesis and self.client.region != self.prosthesis.region:
            raise IntegrityError("регион клиента и протеза должны быть равны")
        super().save(*args, **kwargs)
        if not self.statuses.exists():
            Status.objects.create(job=self)

    def get_absolute_url(self):
        return reverse("clients:job", kwargs={"pk": self.pk})
