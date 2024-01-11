import csv
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandParser
from django.utils.timezone import datetime

from clients.models import Client


def string_to_decimal(s):
    s = s.replace(" ", "").replace(",", ".")
    return Decimal(s)


class Command(BaseCommand):
    """
    Load JSON clients data.
    """

    help = "Load JSON clients data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("file", type=str, help="Load csv file")

    def handle(self, *args, **options):
        with open(options["file"], encoding="utf-8") as f:
            reader = csv.reader(f)

            for row in reader[1:]:
                client = Client()
                # ФИО клиента
                client.last_name, client.first_name, client.surname = row[1].split()
                # СНИЛС
                client.snils = int(row[7])
                # долги
                if row[15] != "-":
                    client.debt = string_to_decimal(row[15])
                # Дата рождения
                date_str = row[16]
                client.birth_date = datetime().strptime(date_str, "%d.%m.%Y").date()
                client.phone = row[17]
                client.address = row[18]

            # data = json.load(f)
            # for ingredient in data:
            #     if created:
            #         self.stdout.write(
            #             self.style.SUCCESS(
            #                 f"Successfully created ingredient `{ing.name}`"
            #             )
            #         )
            #     else:
            #         self.stdout.write(
            #             self.style.WARNING(f"Ingredient `{ing.name}` already exists")
            #         )
