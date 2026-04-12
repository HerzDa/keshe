from decimal import Decimal
import re
import hashlib
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Employee, Invoice, Reimbursement
from .serializers import (
    InvoiceSerializer,
    LoginSerializer,
    RegisterSerializer,
    ReimbursementSerializer,
)
from .services import BaiduServiceError, ocr_vat_invoice
from .services import generate_invoice_preview
from .utils import generate_code_6


def _pick_words(words: dict, *keys) -> str:
    for key in keys:
        item = words.get(key, {})
        if isinstance(item, dict):
            val = item.get('words', '')
        else:
            val = item or ''
        if val not in ('', None, []):
            return str(val)
    return ''


def _normalize_date(raw: str) -> str:
    digits = ''.join(re.findall(r'\d+', raw or ''))
    return digits[:8] if len(digits) >= 8 else ''


def _normalize_amount(raw: str) -> str:
    return (raw or '').replace(',', '').replace('，', '').strip()


def _build_invoice_fingerprint(parsed: dict) -> str:
    parts = [
        parsed.get('invoice_num', ''),
        parsed.get('invoice_date', ''),
        parsed.get('total_amount', ''),
        parsed.get('seller_name', ''),
        parsed.get('buyer_name', ''),
        parsed.get('seller_register_num', ''),
        parsed.get('purchaser_register_num', ''),
    ]
    base = '|'.join(parts)
    return hashlib.sha256(base.encode('utf-8')).hexdigest()


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'message': '注册成功', 'user_id': user.id})


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({
            'message': '登录成功',
            'user': {'id': user.id, 'employee_no': user.employee_no, 'name': user.name},
        })


class ProfileView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        try:
            user = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': user.id,
            'employee_no': user.employee_no,
            'name': user.name,
            'phone': user.phone,
        })

    def put(self, request):
        employee_id = request.data.get('employee_id')
        try:
            user = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        name = (request.data.get('name') or user.name).strip()
        phone = (request.data.get('phone') or user.phone).strip()
        old_password = request.data.get('old_password') or ''
        new_password = request.data.get('new_password') or ''

        if not name:
            return Response({'detail': '姓名不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        user.name = name
        user.phone = phone

        if old_password or new_password:
            if not old_password or not new_password:
                return Response({'detail': '修改密码需同时填写旧密码和新密码'}, status=status.HTTP_400_BAD_REQUEST)
            if not check_password(old_password, user.password):
                return Response({'detail': '旧密码错误'}, status=status.HTTP_400_BAD_REQUEST)
            if len(new_password) < 6:
                return Response({'detail': '新密码至少6位'}, status=status.HTTP_400_BAD_REQUEST)
            user.password = make_password(new_password)

        user.save()
        return Response({
            'message': '个人信息更新成功',
            'user': {'id': user.id, 'employee_no': user.employee_no, 'name': user.name, 'phone': user.phone},
        })


class EmployeeLookupView(APIView):
    def get(self, request):
        employee_no = (request.query_params.get('employee_no') or '').strip()
        if not employee_no:
            return Response({'detail': '请传入工号'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Employee.objects.get(employee_no=employee_no)
        except Employee.DoesNotExist:
            return Response({'detail': '工号不存在'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': user.id,
            'employee_no': user.employee_no,
            'name': user.name,
            'phone': user.phone,
        })


class UploadAndVerifyInvoiceView(APIView):
    def post(self, request):
        employee_id = request.data.get('employee_id')
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        upload_file = request.FILES.get('file')
        if not upload_file:
            return Response({'detail': '请上传发票文件'}, status=status.HTTP_400_BAD_REQUEST)

        invoice = Invoice.objects.create(employee=employee, file=upload_file)
        try:
            preview_rel = generate_invoice_preview(invoice.file.path, invoice.file.name)
            invoice.preview_image = preview_rel
            invoice.save(update_fields=['preview_image'])
        except BaiduServiceError as exc:
            invoice.verify_msg = str(exc)
            invoice.save(update_fields=['verify_msg'])

        try:
            ocr_result = ocr_vat_invoice(invoice.file.path)
            words = ocr_result.get('words_result', {})

            parsed = {
                'invoice_code': _pick_words(words, '发票代码', 'InvoiceCode'),
                'invoice_num': _pick_words(words, '发票号码', 'InvoiceNum'),
                'invoice_date': _normalize_date(_pick_words(words, '开票日期', 'InvoiceDate')),
                'check_code': _pick_words(words, '校验码', 'CheckCode'),
                'amount': _normalize_amount(_pick_words(words, '金额', '合计金额', 'TotalAmount')),
                'tax_amount': _normalize_amount(_pick_words(words, '税额', 'TotalTax')),
                'total_amount': _normalize_amount(_pick_words(words, '价税合计(小写)', '价税合计', 'AmountInFiguers', 'TotalAmount')),
                'buyer_name': _pick_words(words, '购买方名称', 'PurchaserName'),
                'seller_name': _pick_words(words, '销售方名称', 'SellerName'),
                'seller_register_num': _pick_words(words, '销售方纳税人识别号', 'SellerRegisterNum'),
                'purchaser_register_num': _pick_words(words, '购买方纳税人识别号', 'PurchaserRegisterNum'),
            }

            if not parsed['invoice_code']:
                parsed['invoice_code'] = '全电子发票'

            if not parsed['invoice_num'] or not parsed['invoice_date'] or not parsed['total_amount']:
                invoice.verify_status = Invoice.VERIFY_FAILED
                invoice.verify_msg = 'OCR识别信息不完整，无法生成唯一指纹'
                invoice.ocr_result = ocr_result
                invoice.save()
                return Response(InvoiceSerializer(invoice, context={'request': request}).data)

            fingerprint = _build_invoice_fingerprint(parsed)

            duplicate_qs = Invoice.objects.filter(
                invoice_fingerprint=fingerprint,
                verify_status=Invoice.VERIFY_SUCCESS,
            ).exclude(id=invoice.id)

            invoice.invoice_fingerprint = fingerprint
            invoice.invoice_code = parsed['invoice_code']
            invoice.invoice_num = parsed['invoice_num']
            invoice.invoice_date = parsed['invoice_date']
            invoice.check_code = parsed['check_code'][-6:] if parsed['check_code'] else ''
            invoice.buyer_name = parsed['buyer_name']
            invoice.seller_name = parsed['seller_name']
            invoice.amount = Decimal(parsed['amount']) if parsed['amount'] else None
            invoice.tax_amount = Decimal(parsed['tax_amount']) if parsed['tax_amount'] else None
            invoice.total_amount = Decimal(parsed['total_amount']) if parsed['total_amount'] else None
            invoice.ocr_result = ocr_result

            if duplicate_qs.exists():
                duplicate_invoice = duplicate_qs.order_by('id').first()
                invoice.verify_status = Invoice.VERIFY_FAILED
                invoice.verify_msg = f'验真失败：该发票已存在（编码{duplicate_invoice.code_6}）'
            else:
                invoice.verify_status = Invoice.VERIFY_SUCCESS
                invoice.verify_msg = 'OCR验真兜底通过，已生成编码'
                invoice.code_6 = generate_code_6()
            invoice.save()
        except BaiduServiceError as exc:
            invoice.verify_status = Invoice.VERIFY_FAILED
            invoice.verify_msg = str(exc)
            invoice.save()

        return Response(InvoiceSerializer(invoice, context={'request': request}).data)


class OcrByCodeView(APIView):
    def post(self, request):
        employee_id = request.data.get('employee_id')
        code_6 = request.data.get('code_6')
        try:
            invoice = Invoice.objects.get(code_6=code_6, employee_id=employee_id)
        except Invoice.DoesNotExist:
            return Response({'detail': '编码不存在'}, status=status.HTTP_404_NOT_FOUND)

        if invoice.verify_status != Invoice.VERIFY_SUCCESS:
            return Response({'detail': '发票未验真通过，禁止OCR回填'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ocr_result = ocr_vat_invoice(invoice.file.path)
        except BaiduServiceError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        words = ocr_result.get('words_result', {})

        def pick(*keys):
            for key in keys:
                item = words.get(key, {})
                if isinstance(item, dict):
                    val = item.get('words', '')
                else:
                    val = item or ''
                if val not in ('', None, []):
                    return str(val)
            return ''

        amount = pick('金额', '合计金额', 'TotalAmount')
        tax_amount = pick('税额', 'TotalTax')
        total_amount = pick('价税合计(小写)', '价税合计', 'AmountInFiguers')

        invoice.invoice_code = pick('发票代码', 'InvoiceCode') or invoice.invoice_code
        if not invoice.invoice_code:
            invoice.invoice_code = '全电子发票'
        invoice.invoice_num = pick('发票号码', 'InvoiceNum') or invoice.invoice_num
        invoice.invoice_date = pick('开票日期', 'InvoiceDate') or invoice.invoice_date
        invoice.buyer_name = pick('购买方名称', 'PurchaserName') or invoice.buyer_name
        invoice.seller_name = pick('销售方名称', 'SellerName') or invoice.seller_name

        invoice.amount = Decimal(amount.replace(',', '')) if amount else invoice.amount
        invoice.tax_amount = Decimal(tax_amount.replace(',', '')) if tax_amount else invoice.tax_amount
        invoice.total_amount = Decimal(total_amount.replace(',', '')) if total_amount else invoice.total_amount
        invoice.ocr_result = ocr_result
        invoice.save()

        data = InvoiceSerializer(invoice, context={'request': request}).data
        return Response(data)


class ReimbursementDraftOrSubmitView(APIView):
    def post(self, request):
        employee_id = request.data.get('employee_id')
        action = request.data.get('action', 'draft')
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReimbursementSerializer(data=request.data, context={'employee': employee})
        serializer.is_valid(raise_exception=True)

        invoice = serializer.validated_data['invoice']
        if hasattr(invoice, 'reimbursement'):
            return Response({'detail': '该发票已生成报销单，不可重复提交'}, status=status.HTTP_400_BAD_REQUEST)

        reimbursement = serializer.save(
            status=Reimbursement.STATUS_SUBMITTED if action == 'submit' else Reimbursement.STATUS_DRAFT,
            submitted_at=timezone.now() if action == 'submit' else None,
        )
        return Response(ReimbursementSerializer(reimbursement).data)


class MyReimbursementHistoryView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        status_filter = request.query_params.get('status')
        qs = Reimbursement.objects.filter(employee_id=employee_id).order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        data = ReimbursementSerializer(qs, many=True).data
        return Response(data)


class DashboardStatsView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        invoices = Invoice.objects.filter(employee_id=employee_id)
        reimbursements = Reimbursement.objects.filter(employee_id=employee_id)

        total_amount = sum([r.amount for r in reimbursements if r.status == Reimbursement.STATUS_SUBMITTED], Decimal('0.00'))
        recent = ReimbursementSerializer(reimbursements.order_by('-created_at')[:5], many=True).data

        return Response({
            'reimbursement_count': reimbursements.count(),
            'verify_success_count': invoices.filter(verify_status=Invoice.VERIFY_SUCCESS).count(),
            'total_amount': str(total_amount),
            'recent_records': recent,
        })


class VerifySuccessInvoiceListView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        qs = (
            Invoice.objects.filter(employee_id=employee_id, verify_status=Invoice.VERIFY_SUCCESS)
            .order_by('-created_at')
        )
        data = InvoiceSerializer(qs, many=True, context={'request': request}).data
        return Response(data)
