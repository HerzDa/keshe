from django.contrib import admin
from .models import Employee, Invoice, Reimbursement

admin.site.register(Employee)
admin.site.register(Invoice)
admin.site.register(Reimbursement)
