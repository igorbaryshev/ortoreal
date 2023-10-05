import locale

from django.utils import timezone


def get_date_display(date) -> str:
    locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
    return timezone.localtime(date).strftime("%d-%b-%Y %H:%M")


def log(items=None) -> None:
    pass
