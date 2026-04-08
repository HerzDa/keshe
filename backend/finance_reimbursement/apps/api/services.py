import base64
import os
import requests
from django.conf import settings


class BaiduServiceError(Exception):
    pass


def _normalize_invoice_type(raw: str) -> str:
    text = (raw or '').strip()
    if text in {'03', '11', '10', '01'}:
        return text
    if '电子' in text and '普通' in text:
        return '11'
    if '电子' in text and '专用' in text:
        return '10'
    if '专用' in text:
        return '01'
    if '普通' in text:
        return '03'
    return '03'


def _get_access_token() -> str:
    if not settings.BAIDU_API_KEY or not settings.BAIDU_SECRET_KEY:
        raise BaiduServiceError('未配置百度API Key或Secret Key')

    url = (
        'https://aip.baidubce.com/oauth/2.0/token'
        f'?grant_type=client_credentials&client_id={settings.BAIDU_API_KEY}'
        f'&client_secret={settings.BAIDU_SECRET_KEY}'
    )
    resp = requests.get(url, timeout=10)
    data = resp.json()
    token = data.get('access_token')
    if not token:
        raise BaiduServiceError(f'获取百度access_token失败: {data}')
    return token


def _encode_file(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def verify_vat_invoice(file_path: str, invoice_info: dict) -> dict:
    token = _get_access_token()
    url = f"{settings.BAIDU_VERIFY_URL}?access_token={token}"

    ext = os.path.splitext(file_path)[1].lower()
    data = {
        'invoice_type': _normalize_invoice_type(invoice_info.get('invoice_type', '')),
        'invoice_code': invoice_info.get('invoice_code', ''),
        'invoice_num': invoice_info.get('invoice_num', ''),
        'invoice_date': invoice_info.get('invoice_date', ''),
        'check_code': invoice_info.get('check_code', ''),
        'total_amount': invoice_info.get('total_amount', ''),
    }
    if ext == '.pdf':
        data['pdf_file'] = _encode_file(file_path)
        data['pdf_file_num'] = '1'
    else:
        data['image'] = _encode_file(file_path)

    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if 'error_code' in result:
        raise BaiduServiceError(f"验真失败: {result.get('error_msg')}")
    return result


def ocr_vat_invoice(file_path: str) -> dict:
    token = _get_access_token()
    url = f"{settings.BAIDU_OCR_URL}?access_token={token}"
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        data = {'pdf_file': _encode_file(file_path), 'pdf_file_num': '1'}
    else:
        data = {'image': _encode_file(file_path)}
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if 'error_code' in result:
        raise BaiduServiceError(f"OCR失败: {result.get('error_msg')}")
    return result
