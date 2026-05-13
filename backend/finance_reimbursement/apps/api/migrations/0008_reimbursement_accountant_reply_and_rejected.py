from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_employee_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='reimbursement',
            name='accountant_reply',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='reimbursement',
            name='status',
            field=models.CharField(choices=[('draft', '草稿'), ('submitted', '已提交'), ('approved', '历史功能票据'), ('rejected', '已拒绝')], default='draft', max_length=20),
        ),
    ]
