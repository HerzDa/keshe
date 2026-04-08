from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Invoice


def amount_to_chinese_upper(amount: Decimal) -> str:
    digits = '零壹贰叁肆伍陆柒捌玖'
    units = ['分', '角', '元', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
    amount = Decimal(amount).quantize(Decimal('0.01'))
    num = int(amount * 100)
    if num == 0:
        return '零元整'

    parts = []
    unit_index = 0
    zero_flag = False
    while num > 0 and unit_index < len(units):
        n = num % 10
        if n == 0:
            if not zero_flag and unit_index >= 2:
                parts.append('零')
                zero_flag = True
        else:
            parts.append(units[unit_index])
            parts.append(digits[n])
            zero_flag = False
        num //= 10
        unit_index += 1

    result = ''.join(reversed(parts)).replace('零零', '零').replace('零元', '元').replace('零万', '万')
    result = result.rstrip('零')
    if not result.endswith(('分', '角')):
        result += '整'
    return result


def generate_code_6() -> str:
    year = timezone.now().strftime('%y')
    with transaction.atomic():
        latest = (
            Invoice.objects.select_for_update()
            .filter(code_6__startswith=year)
            .order_by('-code_6')
            .first()
        )
        seq = int(latest.code_6[2:]) + 1 if latest and latest.code_6 else 1
        return f'{year}{seq:04d}'
