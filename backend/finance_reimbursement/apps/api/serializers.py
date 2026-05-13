from decimal import Decimal
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers
from .models import Employee, Invoice, Reimbursement, TemporaryLoanApplication
from .utils import amount_to_chinese_upper


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['employee_no', 'name', 'department', 'role', 'phone', 'password']

    def validate_employee_no(self, value):
        if Employee.objects.filter(employee_no=value).exists():
            raise serializers.ValidationError('工号已存在')
        return value

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    employee_no = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        employee_no = attrs['employee_no']
        password = attrs['password']
        try:
            user = Employee.objects.get(employee_no=employee_no)
        except Employee.DoesNotExist as exc:
            raise serializers.ValidationError('账号不存在') from exc

        if not check_password(password, user.password):
            raise serializers.ValidationError('密码错误')

        attrs['user'] = user
        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'employee', 'code_6', 'file', 'file_url', 'verify_status', 'verify_msg',
            'invoice_code', 'invoice_num', 'invoice_date', 'check_code', 'amount', 'tax_amount',
            'total_amount', 'buyer_name', 'seller_name', 'preview_url', 'ocr_result', 'created_at'
        ]
        read_only_fields = ['id', 'employee', 'code_6', 'verify_status', 'verify_msg', 'ocr_result', 'created_at']

    def get_file_url(self, obj):
        req = self.context.get('request')
        return req.build_absolute_uri(obj.file.url) if req else obj.file.url

    def get_preview_url(self, obj):
        req = self.context.get('request')
        if obj.preview_image:
            return req.build_absolute_uri(obj.preview_image.url) if req else obj.preview_image.url
        if obj.file:
            return req.build_absolute_uri(obj.file.url) if req else obj.file.url
        return ''


class ReimbursementSerializer(serializers.ModelSerializer):
    code_6 = serializers.CharField(write_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_department = serializers.CharField(source='employee.department', read_only=True)
    invoice_basic = serializers.SerializerMethodField(read_only=True)
    status_label = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reimbursement
        fields = [
            'id', 'employee_name', 'employee_department', 'code_6', 'department', 'reason', 'budget_item', 'expense_type',
            'reimbursement_date', 'remark', 'amount', 'amount_upper', 'accountant_reply', 'status',
            'submitted_at', 'created_at', 'invoice_basic', 'status_label'
        ]
        read_only_fields = ['id', 'amount_upper', 'submitted_at', 'created_at', 'employee_name', 'invoice_basic']

    def get_status_label(self, obj):
        return dict(Reimbursement.STATUS_CHOICES).get(obj.status, obj.status)

    def get_invoice_basic(self, obj):
        inv = obj.invoice
        req = self.context.get('request')
        preview_url = ''
        if inv.preview_image:
            preview_url = req.build_absolute_uri(inv.preview_image.url) if req else inv.preview_image.url
        elif inv.file:
            preview_url = req.build_absolute_uri(inv.file.url) if req else inv.file.url
        return {
            'code_6': inv.code_6,
            'invoice_code': inv.invoice_code,
            'invoice_num': inv.invoice_num,
            'invoice_date': inv.invoice_date,
            'total_amount': inv.total_amount,
            'buyer_name': inv.buyer_name,
            'seller_name': inv.seller_name,
            'preview_url': preview_url,
        }

    def validate(self, attrs):
        code_6 = attrs.pop('code_6')
        employee = self.context['employee']
        try:
            invoice = Invoice.objects.get(code_6=code_6, employee=employee)
        except Invoice.DoesNotExist as exc:
            raise serializers.ValidationError('未找到该编码对应发票') from exc

        if invoice.verify_status != Invoice.VERIFY_SUCCESS:
            raise serializers.ValidationError('该发票未验真通过，禁止报销')

        attrs['invoice'] = invoice
        attrs['employee'] = employee
        if invoice.total_amount and not attrs.get('amount'):
            attrs['amount'] = Decimal(invoice.total_amount)
        return attrs

    def create(self, validated_data):
        amount = validated_data['amount']
        validated_data['amount_upper'] = amount_to_chinese_upper(amount)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'amount' in validated_data:
            validated_data['amount_upper'] = amount_to_chinese_upper(validated_data['amount'])
        return super().update(instance, validated_data)


class TemporaryLoanApplicationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)

    class Meta:
        model = TemporaryLoanApplication
        fields = [
            'id', 'employee_name', 'applicant_name', 'phone', 'summary', 'project_name', 'budget_item',
            'usage_detail', 'loan_type', 'loan_amount', 'expected_repay_date', 'description',
            'status', 'submitted_at', 'created_at'
        ]
        read_only_fields = ['id', 'employee_name', 'submitted_at', 'created_at']
