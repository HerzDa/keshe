import os
import uuid
from django.db import models
from django.utils import timezone


class Employee(models.Model):
    ROLE_EMPLOYEE = 'employee'
    ROLE_ACCOUNTANT = 'accountant'
    ROLE_CHOICES = [
        (ROLE_EMPLOYEE, '员工'),
        (ROLE_ACCOUNTANT, '会计员'),
    ]

    employee_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=20, default='行政部')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    phone = models.CharField(max_length=20, blank=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employee'

    def __str__(self):
        return f'{self.employee_no}-{self.name}'


def invoice_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower() or '.jpg'
    date_prefix = timezone.now().strftime('%Y%m%d')
    return f'invoices/{date_prefix}/{uuid.uuid4().hex}{ext}'


class Invoice(models.Model):
    VERIFY_PENDING = 'pending'
    VERIFY_SUCCESS = 'success'
    VERIFY_FAILED = 'failed'
    VERIFY_CHOICES = [
        (VERIFY_PENDING, '待验真'),
        (VERIFY_SUCCESS, '验真成功'),
        (VERIFY_FAILED, '验真失败'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='invoices')
    code_6 = models.CharField(max_length=6, unique=True, null=True, blank=True)
    invoice_fingerprint = models.CharField(max_length=128, blank=True, db_index=True)
    file = models.FileField(upload_to=invoice_upload_to)
    preview_image = models.ImageField(upload_to='previews/%Y%m%d/', null=True, blank=True)
    verify_status = models.CharField(max_length=20, choices=VERIFY_CHOICES, default=VERIFY_PENDING)
    verify_msg = models.CharField(max_length=255, blank=True)

    invoice_code = models.CharField(max_length=32, blank=True)
    invoice_num = models.CharField(max_length=32, blank=True)
    invoice_date = models.CharField(max_length=20, blank=True)
    check_code = models.CharField(max_length=32, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    buyer_name = models.CharField(max_length=100, blank=True)
    seller_name = models.CharField(max_length=100, blank=True)

    ocr_result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoice'


class Reimbursement(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_DRAFT, '草稿'),
        (STATUS_SUBMITTED, '已提交'),
        (STATUS_APPROVED, '历史功能票据'),
        (STATUS_REJECTED, '已拒绝'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reimbursements')
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='reimbursement')
    department = models.CharField(max_length=50)
    reason = models.CharField(max_length=255)
    budget_item = models.CharField(max_length=120, default='')
    expense_type = models.CharField(max_length=50)
    reimbursement_date = models.DateField()
    remark = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_upper = models.CharField(max_length=100)
    accountant_reply = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reimbursement'


class TemporaryLoanApplication(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_CHOICES = [
        (STATUS_DRAFT, '草稿'),
        (STATUS_SUBMITTED, '已提交'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loan_applications')
    applicant_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True)
    summary = models.CharField(max_length=255)
    project_name = models.CharField(max_length=120)
    budget_item = models.CharField(max_length=120)
    usage_detail = models.TextField()
    loan_type = models.CharField(max_length=50, default='借款')
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    expected_repay_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'temporary_loan_application'


class BudgetQuota(models.Model):
    item_name = models.CharField(max_length=120, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=10000)
    used_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budget_quota'
