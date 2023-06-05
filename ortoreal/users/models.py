from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    surname = models.CharField(_("отчество"), max_length=150, blank=True)

    is_prosthetist = models.BooleanField(
        "Протезист",
        default=False,
        help_text="Отметьте, если пользователь является протезистом.",
    )
    is_manager = models.BooleanField(
        "Менеджер",
        default=False,
        help_text="Отметьте, если пользователь является менеджером.",
    )

    @property
    def initials(self):
        return f"{self.last_name[0]}{self.first_name[0]}"

    class Meta:
        verbose_name = "Работник"
        verbose_name_plural = "Работники"

    def __str__(self) -> str:
        full_name = self.get_full_name()
        if full_name:
            return full_name
        return self.username
