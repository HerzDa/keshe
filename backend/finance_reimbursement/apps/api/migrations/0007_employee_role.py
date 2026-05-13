from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_budget_quota_and_reimbursement_budget_item'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='role',
            field=models.CharField(choices=[('employee', '员工'), ('accountant', '会计员')], default='employee', max_length=20),
        ),
    ]
