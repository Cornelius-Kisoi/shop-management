# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0003_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='payment_method',
            field=models.CharField(
                choices=[('cash', 'Cash'), ('mpesa', 'M-Pesa'), ('till', 'Till'), ('credit', 'Credit')],
                default='cash',
                max_length=20
            ),
        ),
    ]
