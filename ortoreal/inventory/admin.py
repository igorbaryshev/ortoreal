from django.contrib import admin

from inventory.models import InventoryLog, Part, Item, Vendor


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor_code",
        "name",
        "price",
        "quantity_total",
        "quantity_s1",
        "quantity_s2",
        "units",
        "vendor",
        "note",
    )
    search_fields = ("vendor_code", "name")


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "operation",
        "vendor_code",
        "name",
        "quantity",
        "prosthetist",
        "date",
        "comment",
    )
    list_display_links = ("id", "operation", "vendor_code", "name")
    search_fields = ("part__vendor_code", "part__name")
    autocomplete_fields = ("part",)

    def vendor_code(self, obj):
        return obj.part.vendor_code

    vendor_code.short_description = "Артикул"

    def name(self, obj):
        return obj.part.name

    name.short_description = "Название"


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor_code", "name", "warehouse", "date_added")
    list_display_links = list_display
    search_fields = ("part__vendor_code", "part__name")

    def vendor_code(self, obj):
        return obj.part.vendor_code

    vendor_code.short_description = "Артикул"

    def name(self, obj):
        return obj.part.name

    name.short_description = "Название"


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name",)
