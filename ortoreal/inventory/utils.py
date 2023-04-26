import io
import zipfile
from functools import wraps
from decimal import Decimal

from django.shortcuts import get_list_or_404, redirect
from django.contrib.auth import get_user_model

User = get_user_model()


def dec2pre(value):
    if not value:
        value = 0
    return Decimal(value).quantize(Decimal('.01'))


def generate_zip(files):
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(
        mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as zf:
        for f in files:
            zf.writestr(f[0], f[1])

    return mem_zip.getvalue()


def is_prosthetist(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        prosthetists = get_list_or_404(User, is_prosthetist=True)
        if request.user in prosthetists:
            return f(request, *args, **kwargs)
        return redirect('inventory:parts')
    return wrapper