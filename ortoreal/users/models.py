from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    surname = models.CharField(_("отчество"), max_length=150, blank=True)

    is_prosthetist = models.BooleanField(
        "протезист",
        default=False,
        help_text="отметьте, если пользователь является протезистом.",
    )
    is_manager = models.BooleanField(
        "менеджер",
        default=False,
        help_text="отметьте, если пользователь является менеджером.",
    )

    class Meta:
        verbose_name = "работник"
        verbose_name_plural = "работники"

    def __str__(self) -> str:
        full_name = self.get_full_name()
        if full_name:
            return full_name
        return self.username
