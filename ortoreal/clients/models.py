from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.formats import date_format

from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


class StatusChoices(models.TextChoices):
    IN_WORK = "in work", _("Принят в работу")
    ISSUED = "issued", _("Выдан")
    DOCS_SUBMITTED = "docs submitted", _("Документы сданы")
    PAYMENT_TO_CLIENT = "payment to client", _("Оплата клиенту")
    PAYMENT = "payment", _("Оплата")


class Contact(models.Model):
    class ContactType(models.TextChoices):
        THEY_CALLED = "they_called", _("Звонок")
        WE_CALLED = "we_called", _("Обзвон")
        VIA_PRO = "via_pro", _("Через протезиста")

    class YesNo(models.TextChoices):
        YES = "yes", _("Да")
        NO = "no", _("Нет")

    last_name = models.CharField(
        _("last name"), max_length=150, blank=False, default=None
    )
    first_name = models.CharField(
        _("first name"), max_length=150, blank=False, default=None
    )
    surname = models.CharField(_("отчество"), max_length=150, blank=True)
    how_contacted = models.CharField(
        _("Откуда"), max_length=150, choices=ContactType.choices
    )
    call_date = models.DateField(_("Дата звонка"), default=timezone.now)
    prosthetist = models.ForeignKey(
        User, verbose_name=_("Протезист"), on_delete=models.SET_NULL, null=True
    )
    phone = PhoneNumberField(_("Телефон"), unique=True)
    address = models.TextField(_("Адрес"), max_length=1000, blank=True)
    last_prosthesis_date = models.CharField(
        _("Пред. протез"),
        max_length=150,
        default="первичн",
        blank=True,
        help_text="Примерная дата получения последнего протеза",
    )
    call_result = models.CharField(
        _("Результат звонка"), max_length=1024, blank=True
    )
    comment = models.CharField(
        _("Комментарий"),
        max_length=1024,
        blank=True,
        help_text="Комментарий протезиста",
    )
    MTZ_date = models.DateField(_("МТЗ"), null=True, blank=True)
    result = models.CharField(
        _("Результат"),
        max_length=16,
        null=True,
        blank=True,
        choices=YesNo.choices,
        help_text="Согласились или нет",
    )

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.surname}"

    def get_phone_display(self):
        return self.phone.as_national.replace(" ", "")

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields]

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} {self.surname}"


class Client(models.Model):
    class Region(models.TextChoices):
        MOSCOW = "Moscow", _("Москва")
        MOSCOW_REGION = "Moscow region", _("Московская область")

    class ContactType(models.TextChoices):
        THEY_CALLED = "they_called", _("Звонок")
        WE_CALLED = "we_called", _("Обзвон")
        VIA_PRO = "via_pro", _("Через протезиста")

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
    how_contacted = models.CharField(
        _("Откуда"), max_length=150, choices=ContactType.choices
    )
    prosthetist = models.ForeignKey(
        User,
        verbose_name="Протезист",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    region = models.CharField(
        "Регион",
        max_length=128,
        choices=Region.choices,
        blank=False,
        default=None,
    )
    cost = models.DecimalField(
        _("Стоимость, руб."), max_digits=11, decimal_places=2
    )

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
            return f"{self.get_status_display()}", f"({date})"
        return ("--нет статуса--",)

    status_display.fget.short_description = "Статус"

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

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} {self.surname}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status:
            Status.objects.create(name=self.status, client=self)


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
        "Название", max_length=150, choices=StatusChoices.choices, blank=False
    )
    client = models.ForeignKey(
        Client,
        verbose_name="Клиент",
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    date = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name}({self.date})"

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"


class Order(models.Model):
    client = models.ForeignKey(
        Client,
        verbose_name="Клиент",
        related_name="orders",
        on_delete=models.CASCADE,
    )
    prosthetist = models.ForeignKey(
        User,
        verbose_name="Протезист",
        related_name="jobs",
        on_delete=models.SET_NULL,
        null=True,
    )
    price = models.DecimalField("Цена", max_digits=11, decimal_places=2)
    date = models.DateField("Дата заказа", default=timezone.now)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
