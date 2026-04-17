from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_employee_department'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemporaryLoanApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applicant_name', models.CharField(max_length=50)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('summary', models.CharField(max_length=255)),
                ('project_name', models.CharField(max_length=120)),
                ('budget_item', models.CharField(max_length=120)),
                ('usage_detail', models.TextField()),
                ('loan_type', models.CharField(default='借款', max_length=50)),
                ('loan_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('expected_repay_date', models.DateField(blank=True, null=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('draft', '草稿'), ('submitted', '已提交')], default='draft', max_length=20)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loan_applications', to='api.employee')),
            ],
            options={
                'db_table': 'temporary_loan_application',
            },
        ),
    ]
