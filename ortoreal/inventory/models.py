from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import Patient

User = get_user_model()


class Vendor(models.Model):
    name = models.CharField(max_length=1024)

    class Meta:
        verbose_name = "Производитель/поставщик"
        verbose_name_plural = "Производители/поставщики"

    def __str__(self):
        return self.name


class Part(models.Model):
    class Units(models.TextChoices):
        PAIRS = "pairs", _("пар")
        PIECES = "pieces", _("шт.")
        SETS = "sets", _("компл.")
        PACKAGES = "packages", _("упак.")

    vendor_code = models.CharField("Артикул", max_length=256, unique=True)
    name = models.CharField("Наименование", max_length=1024)
    units = models.CharField(
        "Единицы", max_length=32, choices=Units.choices, blank=True
    )
    price = models.DecimalField("Цена, руб.", max_digits=11, decimal_places=2)
    vendor = models.ForeignKey(
        Vendor,
        verbose_name="Производитель/поставщик",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    note = models.CharField("Примечание", max_length=1024, blank=True)

    @property
    def quantity(self):
        return f"{self.items.count()}"
    quantity.fget.short_description = "Кол-во"

    class Meta:
        verbose_name = "Модель комплектующего"
        verbose_name_plural = "Модели комплектующих"

    def __str__(self) -> str:
        return f"{self.vendor_code} - {self.name}"


class Item(models.Model):
    part = models.ForeignKey(
        Part,
        verbose_name="Комплектующее",
        on_delete=models.CASCADE,
        related_name="items",
    )
    date_added = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Комплектующее на складе"
        verbose_name_plural = "Комплектующие на складе"


class Product(models.Model):
    class Region(models.TextChoices):
        MOSCOW = "Moscow", _("Москва")
        MOSCOW_REGION = "Moscow region", _("Московская область")

    name = models.CharField("Название", max_length=1024)
    price = models.DecimalField("Цена", max_digits=11, decimal_places=2)
    parts = models.ManyToManyField(Item, verbose_name="Комплектующие")
    region = models.CharField("Регион", max_length=128, choices=Region.choices)
    patient = models.ForeignKey(
        Patient,
        verbose_name="Инвалид",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Модель протеза"
        verbose_name_plural = "Модели протезов"

    def __str__(self) -> str:
        return self.name


class InventoryLog(models.Model):
    class LogAction(models.TextChoices):
        RECEIVED = "RECEPTION", _("Приход")
        TOOK = "TOOK", _("Взял")
        RETURNED = "RETURNED", _("Вернул")

    operation = models.CharField(
        "Операция", max_length=32, choices=LogAction.choices
    )
    part = models.ForeignKey(
        Part, verbose_name="Комплектующее", on_delete=models.CASCADE
    )
    quantity = models.SmallIntegerField("Количество")
    patient = models.ForeignKey(
        Patient,
        verbose_name="Инвалид",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    prosthetist = models.ForeignKey(
        User,
        verbose_name="Протезист",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    comment = models.CharField("Комментарий", max_length=1024, blank=True)
    date = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Операция на складе"
        verbose_name_plural = "Операции на складе"

    def __str__(self):
        return f"{self.operation} {self.quantity} {self.part}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.operation == self.LogAction.RECEIVED:
            batch = [Item(part=self.part, date_added=self.date) for _ in range(self.quantity)]
            Item.objects.bulk_create(batch)
