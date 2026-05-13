from decimal import Decimal
import re
import hashlib
from pathlib import Path
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BudgetQuota, Employee, Invoice, Reimbursement, TemporaryLoanApplication
from .serializers import (
    InvoiceSerializer,
    LoginSerializer,
    RegisterSerializer,
    ReimbursementSerializer,
    TemporaryLoanApplicationSerializer,
)
from .services import BaiduServiceError, ocr_vat_invoice
from .services import generate_invoice_preview
from .utils import amount_to_chinese_upper, generate_code_6

DEPARTMENT_OPTIONS = ['行政部', '人事部', '财务部', '市场部', '销售部', '产品部', '技术部']


def _ensure_budget_quota(item_name: str) -> BudgetQuota:
    clean_name = (item_name or '').strip()
    if not clean_name:
        raise ValueError('相关预算项不能为空')
    quota, _ = BudgetQuota.objects.get_or_create(item_name=clean_name)
    return quota


def _deduct_budget(item_name: str, amount: Decimal):
    if amount <= 0:
        return
    quota = _ensure_budget_quota(item_name)
    available = quota.total_amount - quota.used_amount
    if available < amount:
        raise ValueError(f'预算不足：{item_name} 可用{available}，本次申请{amount}')
    quota.used_amount = quota.used_amount + amount
    quota.save(update_fields=['used_amount', 'updated_at'])


def _refund_budget(item_name: str, amount: Decimal):
    if amount <= 0:
        return
    quota = _ensure_budget_quota(item_name)
    quota.used_amount = max(Decimal('0'), quota.used_amount - amount)
    quota.save(update_fields=['used_amount', 'updated_at'])


def _is_accountant(employee: Employee) -> bool:
    return employee.role == Employee.ROLE_ACCOUNTANT


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
            'user': {
                'id': user.id,
                'employee_no': user.employee_no,
                'name': user.name,
                'department': user.department,
                'role': user.role,
            },
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
            'department': user.department,
            'role': user.role,
            'phone': user.phone,
        })

    def put(self, request):
        employee_id = request.data.get('employee_id')
        try:
            user = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        name = (request.data.get('name') or user.name).strip()
        department = (request.data.get('department') or user.department).strip()
        phone = (request.data.get('phone') or user.phone).strip()
        old_password = request.data.get('old_password') or ''
        new_password = request.data.get('new_password') or ''

        if not name:
            return Response({'detail': '姓名不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        if department not in DEPARTMENT_OPTIONS:
            return Response({'detail': '部门不在可选范围内'}, status=status.HTTP_400_BAD_REQUEST)

        user.name = name
        user.department = department
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
            'user': {
                'id': user.id,
                'employee_no': user.employee_no,
                'name': user.name,
                'department': user.department,
                'phone': user.phone,
            },
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
            'department': user.department,
            'role': user.role,
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

        if action == 'submit':
            try:
                _deduct_budget(
                    serializer.validated_data.get('budget_item', ''),
                    Decimal(serializer.validated_data.get('amount') or '0')
                )
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        reimbursement = serializer.save(
            status=Reimbursement.STATUS_SUBMITTED if action == 'submit' else Reimbursement.STATUS_DRAFT,
            submitted_at=timezone.now() if action == 'submit' else None,
        )
        return Response(ReimbursementSerializer(reimbursement).data)


class TemporaryLoanDraftOrSubmitView(APIView):
    def post(self, request):
        employee_id = request.data.get('employee_id')
        action = request.data.get('action', 'draft')
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        payload = {
            'applicant_name': request.data.get('applicant_name') or employee.name,
            'phone': request.data.get('phone') or employee.phone,
            'summary': request.data.get('summary') or request.data.get('reason') or '',
            'project_name': request.data.get('project_name') or '',
            'budget_item': request.data.get('budget_item') or '',
            'usage_detail': request.data.get('usage_detail') or '',
            'loan_type': request.data.get('loan_type') or '借款',
            'loan_amount': request.data.get('loan_amount') or request.data.get('amount') or '0',
            'expected_repay_date': request.data.get('expected_repay_date'),
            'description': request.data.get('description') or request.data.get('remark') or '',
            'status': TemporaryLoanApplication.STATUS_SUBMITTED if action == 'submit' else TemporaryLoanApplication.STATUS_DRAFT,
            'submitted_at': timezone.now() if action == 'submit' else None,
        }

        serializer = TemporaryLoanApplicationSerializer(data=payload)
        serializer.is_valid(raise_exception=True)

        if action == 'submit':
            try:
                _deduct_budget(
                    payload.get('budget_item', ''),
                    Decimal(payload.get('loan_amount') or '0')
                )
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        loan = serializer.save(employee=employee)
        return Response(TemporaryLoanApplicationSerializer(loan).data)


class MyReimbursementHistoryView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        status_filter = request.query_params.get('status')
        qs = Reimbursement.objects.filter(employee_id=employee_id).order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        data = ReimbursementSerializer(qs, many=True).data
        return Response(data)


class ReimbursementEditDeleteRevokeView(APIView):
    def put(self, request, reimbursement_id):
        employee_id = request.data.get('employee_id')
        try:
            reimbursement = Reimbursement.objects.get(id=reimbursement_id, employee_id=employee_id)
        except Reimbursement.DoesNotExist:
            return Response({'detail': '报销单不存在'}, status=status.HTTP_404_NOT_FOUND)

        if reimbursement.status not in [Reimbursement.STATUS_DRAFT, Reimbursement.STATUS_REJECTED]:
            return Response({'detail': '仅草稿或已拒绝可修改'}, status=status.HTTP_400_BAD_REQUEST)

        reimbursement.department = request.data.get('department', reimbursement.department)
        reimbursement.reason = request.data.get('reason', reimbursement.reason)
        reimbursement.budget_item = request.data.get('budget_item', reimbursement.budget_item)
        reimbursement.expense_type = request.data.get('expense_type', reimbursement.expense_type)
        reimbursement.reimbursement_date = request.data.get('reimbursement_date', reimbursement.reimbursement_date)
        reimbursement.remark = request.data.get('remark', reimbursement.remark)
        if reimbursement.status == Reimbursement.STATUS_REJECTED:
            reimbursement.accountant_reply = ''

        amount = request.data.get('amount')
        if amount not in (None, ''):
            reimbursement.amount = Decimal(str(amount))
            reimbursement.amount_upper = amount_to_chinese_upper(reimbursement.amount)

        reimbursement.save()
        return Response(ReimbursementSerializer(reimbursement).data)

    def delete(self, request, reimbursement_id):
        employee_id = request.query_params.get('employee_id')
        try:
            reimbursement = Reimbursement.objects.get(id=reimbursement_id, employee_id=employee_id)
        except Reimbursement.DoesNotExist:
            return Response({'detail': '报销单不存在'}, status=status.HTTP_404_NOT_FOUND)

        if reimbursement.status not in [Reimbursement.STATUS_DRAFT, Reimbursement.STATUS_REJECTED]:
            return Response({'detail': '仅草稿或已拒绝可删除'}, status=status.HTTP_400_BAD_REQUEST)

        reimbursement.delete()
        return Response({'message': '删除成功'})

    def post(self, request, reimbursement_id):
        employee_id = request.data.get('employee_id')
        action = request.data.get('action', 'revoke')
        try:
            reimbursement = Reimbursement.objects.get(id=reimbursement_id, employee_id=employee_id)
        except Reimbursement.DoesNotExist:
            return Response({'detail': '报销单不存在'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'revoke':
            if reimbursement.status not in [Reimbursement.STATUS_SUBMITTED, Reimbursement.STATUS_REJECTED]:
                return Response({'detail': '仅已提交或已拒绝票据可撤销'}, status=status.HTTP_400_BAD_REQUEST)

            if reimbursement.status == Reimbursement.STATUS_SUBMITTED:
                _refund_budget(reimbursement.budget_item, Decimal(reimbursement.amount or '0'))
            reimbursement.status = Reimbursement.STATUS_DRAFT
            reimbursement.submitted_at = None
            reimbursement.accountant_reply = ''
            reimbursement.save(update_fields=['status', 'submitted_at', 'accountant_reply'])
            return Response({'message': '撤销成功，已恢复为草稿'})

        if action == 'submit':
            if reimbursement.status not in [Reimbursement.STATUS_DRAFT, Reimbursement.STATUS_REJECTED]:
                return Response({'detail': '仅草稿或已拒绝可提交'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                _deduct_budget(reimbursement.budget_item, Decimal(reimbursement.amount or '0'))
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

            reimbursement.status = Reimbursement.STATUS_SUBMITTED
            reimbursement.submitted_at = timezone.now()
            reimbursement.accountant_reply = ''
            reimbursement.save(update_fields=['status', 'submitted_at', 'accountant_reply'])
            return Response({'message': '提交成功'})

        return Response({'detail': 'action仅支持 submit/revoke'}, status=status.HTTP_400_BAD_REQUEST)


class AccountantReimbursementPendingListView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        try:
            user = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not _is_accountant(user):
            return Response({'detail': '仅会计员可访问'}, status=status.HTTP_403_FORBIDDEN)

        qs = Reimbursement.objects.filter(status=Reimbursement.STATUS_SUBMITTED).order_by('-created_at')
        data = ReimbursementSerializer(qs, many=True, context={'request': request}).data
        return Response(data)


class AccountantReimbursementHistoryListView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        try:
            user = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not _is_accountant(user):
            return Response({'detail': '仅会计员可访问'}, status=status.HTTP_403_FORBIDDEN)

        qs = Reimbursement.objects.filter(status__in=[Reimbursement.STATUS_APPROVED, Reimbursement.STATUS_REJECTED]).order_by('-created_at')
        data = ReimbursementSerializer(qs, many=True, context={'request': request}).data
        return Response(data)


class AccountantReimbursementAuditView(APIView):
    def post(self, request, reimbursement_id):
        employee_id = request.data.get('employee_id')
        action = request.data.get('action')
        try:
            user = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': '员工不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not _is_accountant(user):
            return Response({'detail': '仅会计员可审批'}, status=status.HTTP_403_FORBIDDEN)

        try:
            reimbursement = Reimbursement.objects.get(id=reimbursement_id)
        except Reimbursement.DoesNotExist:
            return Response({'detail': '报销单不存在'}, status=status.HTTP_404_NOT_FOUND)

        if reimbursement.status != Reimbursement.STATUS_SUBMITTED:
            return Response({'detail': '当前状态不可审批'}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'approve':
            reimbursement.status = Reimbursement.STATUS_APPROVED
            reimbursement.accountant_reply = ''
            reimbursement.save(update_fields=['status', 'accountant_reply'])
            return Response({'message': '审批同意成功'})

        if action == 'revoke':
            _refund_budget(reimbursement.budget_item, Decimal(reimbursement.amount or '0'))
            reimbursement.status = Reimbursement.STATUS_DRAFT
            reimbursement.submitted_at = None
            reimbursement.accountant_reply = ''
            reimbursement.save(update_fields=['status', 'submitted_at', 'accountant_reply'])
            return Response({'message': '审批撤回成功，已退回草稿'})

        if action == 'reject':
            reply = (request.data.get('reply') or '').strip()
            if not reply:
                return Response({'detail': '请填写拒绝原因或补充说明'}, status=status.HTTP_400_BAD_REQUEST)
            _refund_budget(reimbursement.budget_item, Decimal(reimbursement.amount or '0'))
            reimbursement.status = Reimbursement.STATUS_REJECTED
            reimbursement.accountant_reply = reply
            reimbursement.save(update_fields=['status', 'accountant_reply'])
            return Response({'message': '已拒绝并完成回复'})

        return Response({'detail': '不支持的审批动作'}, status=status.HTTP_400_BAD_REQUEST)


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


def _parse_budget_template_lines(lines):
    rows = []
    current_heading = ''
    for raw in lines:
        line = (raw or '').strip()
        if not line:
            continue

        if re.match(r'^[一二三四五六七八九十]+、', line):
            current_heading = line
            rows.append({
                'type': 'heading',
                'category': current_heading,
                'subject': current_heading,
                'description': '',
            })
            continue

        if line.startswith('科目名称') or line.startswith('表格科目名称'):
            continue

        parts = [p.strip() for p in re.split(r'\t+|\s{2,}', line) if p.strip()]
        if not parts:
            continue

        subject = parts[0]
        if subject in {'——', '-'}:
            continue

        description = parts[-1] if len(parts) > 1 else ''
        rows.append({
            'type': 'item',
            'category': current_heading,
            'subject': subject,
            'budget': 10000,
            'used': 0,
            'available': 10000,
            'used_percent': 0,
            'description': '' if description in {'——', '-'} else description,
        })

    return rows


class ProjectBudgetTemplateView(APIView):
    def get(self, request):
        base_dir = Path(__file__).resolve().parents[4]
        template_file = base_dir / '新建 文本文档.txt'
        if not template_file.exists():
            return Response({'detail': '预算模板文件不存在'}, status=status.HTTP_404_NOT_FOUND)

        with template_file.open('r', encoding='utf-8') as f:
            lines = f.readlines()

        rows = _parse_budget_template_lines(lines)
        item_names = [r['subject'] for r in rows if r.get('type') == 'item' and r.get('subject')]
        quota_map = {q.item_name: q for q in BudgetQuota.objects.filter(item_name__in=item_names)}

        for name in item_names:
            if name not in quota_map:
                quota_map[name] = _ensure_budget_quota(name)

        for row in rows:
            if row.get('type') != 'item':
                continue
            quota = quota_map.get(row.get('subject'))
            if not quota:
                continue
            total = Decimal(quota.total_amount)
            used = Decimal(quota.used_amount)
            available = total - used
            row['budget'] = float(total)
            row['used'] = float(used)
            row['available'] = float(available)
            row['used_percent'] = float((used / total * 100) if total > 0 else 0)
        return Response({'rows': rows})


class ReimbursementStatisticsView(APIView):
    def get(self, request):
        employee_id = request.query_params.get('employee_id')
        valid_statuses = [Reimbursement.STATUS_SUBMITTED, Reimbursement.STATUS_APPROVED]

        personal_categories = [
            '硬件费', '材料费', '燃料动力费', '测试化验加工费', '外协费',
            '软件费', '差旅费（培训相关）', '其他硬件相关及杂项', '业务接待费/工作餐费',
        ]

        total_personal = (
            Reimbursement.objects.filter(employee_id=employee_id, status__in=valid_statuses)
            .aggregate(total=Sum('amount'))
            .get('total')
            or Decimal('0')
        )

        weights = [20, 14, 10, 9, 12, 11, 8, 9, 7]
        personal_values = []
        if total_personal > 0:
            remaining = Decimal(total_personal)
            for i, w in enumerate(weights):
                if i == len(weights) - 1:
                    amount = remaining
                else:
                    amount = (Decimal(total_personal) * Decimal(w) / Decimal(100)).quantize(Decimal('0.01'))
                    remaining -= amount
                personal_values.append(float(amount))
        else:
            personal_values = [0.0 for _ in personal_categories]

        department_map = {k: 0.0 for k in DEPARTMENT_OPTIONS}
        dept_rows = (
            Reimbursement.objects.filter(status__in=valid_statuses)
            .values('department')
            .annotate(total=Sum('amount'))
        )
        for row in dept_rows:
            dept_name = row['department'] or ''
            if dept_name in department_map:
                department_map[dept_name] = float(row['total'] or 0)

        return Response({
            'personal': {
                'labels': personal_categories,
                'values': personal_values,
            },
            'department': {
                'labels': list(department_map.keys()),
                'values': list(department_map.values()),
            },
        })
