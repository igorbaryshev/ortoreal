import csv
from decimal import Decimal

from inventory.models import Part, Vendor

UNITS = dict([(x[1].strip("."), x[0]) for x in Part.Units.choices])
NUMBER_CHARS = "0123456789-,."


def run():
    with open("scripts/import/nomenclature.csv") as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            vendor = row[-1]
            if vendor:
                vendor, _ = Vendor.objects.get_or_create(name=row[-1])
            else:
                vendor = None

            vendor_code, name, units, price = row[:-1]

            if units:
                units = UNITS[units.strip(".")]

            if not price:
                price = "0"
            price = Decimal(
                "".join([i for i in price if i in NUMBER_CHARS]).replace(
                    ",", "."
                )
            )
            part, _ = Part.objects.get_or_create(
                vendor_code=vendor_code,
                defaults={
                    "name": name,
                    "units": units,
                    "price": price,
                    "vendor": vendor,
                },
            )
