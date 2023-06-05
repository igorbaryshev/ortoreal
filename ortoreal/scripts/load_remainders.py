import csv

from inventory.models import Item, Part


def run():
    with open("scripts/import/remainders.csv") as file:
        reader = csv.reader(file)
        next(reader)

        batch_create = []
        Item.objects.all().delete()

        for row in reader:
            try:
                part = Part.objects.get(vendor_code=row[0])
            except Part.DoesNotExist:
                print(row[0])
            quantity = int(row[1])
            batch_create += [Item(part=part, arrived=True)] * quantity

        Item.objects.bulk_create(batch_create)
