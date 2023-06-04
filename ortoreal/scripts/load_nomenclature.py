import csv
from decimal import Decimal

from inventory.models import Manufacturer, Part, Vendor

# UNITS = dict([(x[1].strip("."), x[0]) for x in Part.Units.choices])
NUMBER_CHARS = "0123456789-,."


def run():
    with open("scripts/import/nomenclature.csv") as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            vendor_code, name, units, manufacturer, vendor, note = row

            if units:
                units = units.strip()
            else:
                units = None

            if manufacturer:
                manufacturer, _ = Manufacturer.objects.get_or_create(
                    name=manufacturer
                )
            else:
                manufacturer = None

            if vendor:
                vendor, _ = Vendor.objects.get_or_create(name=vendor)
            else:
                vendor = None

            if not note:
                note = None

            Part.objects.get_or_create(
                vendor_code=vendor_code,
                defaults={
                    "name": name,
                    "units": units,
                    "manufacturer": manufacturer,
                    "vendor": vendor,
                    "note": note,
                },
            )
