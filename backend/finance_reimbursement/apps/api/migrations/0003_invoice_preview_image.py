from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_invoice_fingerprint'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='preview_image',
            field=models.ImageField(blank=True, null=True, upload_to='previews/%Y%m%d/'),
        ),
    ]
