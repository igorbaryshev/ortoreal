from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from clients.models import Client, Job

User = get_user_model()


class Order(models.Model):
    current = models.BooleanField("Текущий", default=True)
    date = models.DateTimeField("Дата", default=timezone.now)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self) -> str:
        current = "закрыт"
        if self.current:
            current = "текущий"
        return f"Заказ {self.id} ({current})"


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
        ITEMS = "items", _("ед.")

    vendor_code = models.CharField("Артикул", max_length=256, unique=True)
    name = models.CharField("Наименование", max_length=1024)
    units = models.CharField(
        "Единицы",
        max_length=32,
        choices=Units.choices,
        blank=True,
        default=Units.ITEMS,
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
    def quantity_s1(self):
        return f"{self.items.filter(warehouse='s1', job=None).count()}"

    quantity_s1.fget.short_description = "Кол-во(С1)"

    @property
    def quantity_s2(self):
        return f"{self.items.filter(warehouse='s2', job=None).count()}"

    quantity_s2.fget.short_description = "Кол-во(С2)"

    @property
    def quantity_total(self):
        """
        Кол-во комплектующих, которые
        пришли на склад, и не взяты в работу.
        """
        total = self.items.filter(job=None).exclude(warehouse="").count()
        return f"{total}"

    quantity_total.fget.short_description = "Кол-во"

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields if f.name != "units"]

    class Meta:
        verbose_name = "модель комплектующего"
        verbose_name_plural = "Номенклатура"

    def __str__(self) -> str:
        return f"{self.vendor_code} - {self.name}"


class Item(models.Model):
    class Warehouse(models.TextChoices):
        S1 = "s1", _("Склад 1")
        S2 = "s2", _("Склад 2")

    part = models.ForeignKey(
        Part,
        verbose_name="Артикул",
        on_delete=models.CASCADE,
        related_name="items",
        blank=False,
        null=False,
    )
    date_added = models.DateField("Дата", default=timezone.now)
    warehouse = models.CharField(
        "Склад", max_length=16, choices=Warehouse.choices, blank=True
    )
    job = models.ForeignKey(
        Job,
        verbose_name="Работа",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="items",
    )
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="items",
    )
    reserved = models.ForeignKey(
        Job,
        verbose_name="Резерв",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reserved_items",
    )

    @classmethod
    def get_field_names(cls):
        return [f.verbose_name for f in cls._meta.fields]

    class Meta:
        verbose_name = "Комплектующее на складе"
        verbose_name_plural = "Комплектующие на складе"

    def __str__(self):
        return self.part.__str__()


class ProsthesisModel(models.Model):
    class Region(models.TextChoices):
        MOSCOW = "Moscow", _("Москва")
        MOSCOW_REGION = "Moscow region", _("Московская область")

    name = models.CharField("Название", max_length=1024)
    price = models.DecimalField("Цена", max_digits=11, decimal_places=2)
    #    parts = models.ManyToManyField(Item, verbose_name="Комплектующие")
    region = models.CharField("Регион", max_length=128, choices=Region.choices)

    #
    class Meta:
        verbose_name = "Модель протеза"
        verbose_name_plural = "Модели протезов"

    def __str__(self) -> str:
        return self.name


class InventoryLog(models.Model):
    class PartialLogAction(models.TextChoices):
        EMPTY = "", _("---выбрать---")
        RETURN = "RETURN", _("Возврат")
        TAKE = "TAKE", _("Расход")

    class LogAction(models.TextChoices):
        EMPTY = "", _("---выбрать---")
        RECEPTION = "RECEPTION", _("Приход")
        RETURN = "RETURN", _("Возврат")
        TAKE = "TAKE", _("Расход")

    operation = models.CharField(
        "Операция", max_length=32, choices=LogAction.choices
    )
    items = models.ManyToManyField(Item, verbose_name="Комплектующие")
    job = models.ForeignKey(
        Job,
        verbose_name="Клиент",
        on_delete=models.CASCADE,
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
    date = models.DateTimeField("Дата", default=timezone.now)
    comment = models.CharField("Комментарий", max_length=1024, blank=True)

    # @property
    # def quantity(self):
    #     return self.items.count()
# 
    # quantity.fget.short_description = "Количество"

    #@property
    #def vendor_code(self):
    #    if self.items.exists():
    #        return self.items.all()[0].part.vendor_code
    #    return "—"
#
    #vendor_code.fget.short_description = "Артикул"
#
    #@property
    #def part_name(self):
    #    if self.items.exists():
    #        return self.items.all()[0].part.name
    #    return "—"
#
    #part_name.fget.short_description = "Наименование"

    class Meta:
        verbose_name = "Операция на складе"
        verbose_name_plural = "Операции на складе"

    def __str__(self):
        return f"{self.operation}"


class Prosthesis(models.Model):
    number = models.CharField("Номер изделия", max_length=150, unique=True)
    kind = models.CharField("Вид", max_length=1024, blank=True)
    name = models.CharField("Наименование", max_length=1024, blank=True)
    price = models.DecimalField("Стоимость", max_digits=11, decimal_places=2)

    class Meta:
        verbose_name = "Протез"
        verbose_name_plural = "Протезы"

    def __str__(self) -> str:
        return f"{self.number}"
