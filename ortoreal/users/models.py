from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    first_name = models.CharField(
        _("first name"), max_length=150, blank=False, default=None
    )
    surname = models.CharField(_("отчество"), max_length=150, blank=True)
    last_name = models.CharField(
        _("last name"), max_length=150, blank=False, default=None
    )
    is_prosthetist = models.BooleanField("Протезист", default=False)

    class Meta:
        verbose_name = "Работник"
        verbose_name_plural = "Работники"

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.surname}"
