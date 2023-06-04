import csv
from datetime import datetime
from decimal import Decimal

from django.utils.timezone import make_aware

from inventory.models import Item, Part, Vendor

NUMBER_CHARS = "0123456789-,."


def run():
    with open("scripts/import/reception.csv") as file:
        reader = csv.reader(file)
        next(reader)

        batch_create = []
        for row in reader:
            part, quantity, price, vendor, date = row[0], *row[2:]

            part = Part.objects.get(vendor_code=part)

            quantity = int(quantity)

            try:
                if "." in price:
                    price = price.replace(",", " ").replace(".", ",")
                price = Decimal(
                    "".join([i for i in price if i in NUMBER_CHARS]).replace(
                        ",", "."
                    )
                )
            except Exception:
                raise Exception(price)

            date = make_aware(datetime.strptime(date, "%d-%m-%y"))

            warehouse = Item.Warehouse.S1
            vendor2 = False
            if vendor == "2":
                warehouse = Item.Warehouse.S2
                vendor2 = True

            if warehouse == Item.Warehouse.S1 or part.price is None:
                part.price = price

            part.save()

            batch_create += [
                Item(
                    part=part,
                    price=price,
                    date=date,
                    warehouse=warehouse,
                    vendor2=vendor2,
                    arrived=True,
                )
            ] * quantity

        Item.objects.bulk_create(batch_create)
