from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_invoice_preview_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='department',
            field=models.CharField(default='行政部', max_length=20),
        ),
    ]
