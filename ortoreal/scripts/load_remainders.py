import csv

from inventory.models import Item, Part


def run():
    with open("scripts/import/remainders.csv") as file:
        reader = csv.reader(file)
        next(reader)

        batch_create = []
        for row in reader:
            part = Part.objects.get(vendor_code=row[0])
            quantity = int(row[1])
            batch_create += [
                Item(part=part, warehouse=Item.Warehouse.S1)
            ] * quantity

        Item.objects.bulk_create(batch_create)
