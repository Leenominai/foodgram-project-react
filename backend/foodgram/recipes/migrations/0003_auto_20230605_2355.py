# Generated by Django 2.2.16 on 2023-06-05 20:55

from django.db import migrations, models
import recipes.validators


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20230605_2340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(help_text='Выберите время в минутах', validators=[recipes.validators.validate_cooking_time], verbose_name='Время приготовления'),
        ),
    ]
