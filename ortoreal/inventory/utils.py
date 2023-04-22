from decimal import Decimal


def dec2pre(value):
    if not value:
        value = 0
    return Decimal(value).quantize(Decimal('.01'))
