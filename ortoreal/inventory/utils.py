import io
import zipfile
from decimal import Decimal


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