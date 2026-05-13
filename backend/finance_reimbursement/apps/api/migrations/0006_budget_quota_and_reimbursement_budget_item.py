from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_temporary_loan_application'),
    ]

    operations = [
        migrations.AddField(
            model_name='reimbursement',
            name='budget_item',
            field=models.CharField(default='', max_length=120),
        ),
        migrations.CreateModel(
            name='BudgetQuota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=120, unique=True)),
                ('total_amount', models.DecimalField(decimal_places=2, default=10000, max_digits=12)),
                ('used_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'budget_quota',
            },
        ),
    ]
