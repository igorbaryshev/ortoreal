from django.contrib import admin
from django.db.models import Sum

from inventory.models import (
    InventoryLog,
    Item,
    Manufacturer,
    Order,
    Part,
    Prosthesis,
    Vendor,
)
from inventory.utils import dec2pre


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("is_current", "date", "item_count", "price")

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = "Кол-во"

    def price(self, obj):
        return f"""{dec2pre(
            obj.items.aggregate(Sum("part__price"))["part__price__sum"]
        ):,}""".replace(
            ",", " "
        ).replace(
            ".", ","
        )

    price.short_description = "Всего, руб."


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor_code",
        "name",
        "price",
        "quantity_total",
        "units",
        "manufacturer",
        "vendor",
        "note",
    )
    list_display_links = list_display
    search_fields = ("vendor_code", "name")


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "operation",
        # "vendor_code",
        # "part_name",
        "quantity",
        "prosthetist",
        "date",
        "comment",
    )
    # list_display_links = ("id", "operation", "vendor_code", "part_name")
    search_fields = ("items__part__vendor_code", "items__part__name")

    # исправить позже
    # autocomplete_fields = ("part",)
    def quantity(self, obj):
        return obj.items.count()

    quantity.short_description = "кол-во"


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor_code",
        "name",
        "arrived",
        "job",
        "reserved",
        "date",
        "order",
        "free_order",
    )
    list_display_links = list_display
    search_fields = ("part__vendor_code", "part__name")
    autocomplete_fields = ("part",)

    def vendor_code(self, obj):
        return obj.part.vendor_code

    vendor_code.short_description = "Артикул"

    def name(self, obj):
        return obj.part.name

    name.short_description = "Название"


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Prosthesis)
class ProsthesisAdmin(admin.ModelAdmin):
    list_display = ("number", "kind", "price", "region")
