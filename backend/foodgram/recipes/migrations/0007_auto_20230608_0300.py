# Generated by Django 2.2.16 on 2023-06-08 00:00

from django.db import migrations, models
import recipes.validators


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_auto_20230607_2349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(help_text='Выберите время в минутах', validators=[recipes.validators.validate_cooking_time], verbose_name='Время приготовления'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(blank=True, help_text='Добавьте картинку к своему рецепту', upload_to='recipes/', verbose_name='Картинка'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='name',
            field=models.CharField(help_text='Введите название рецепта', max_length=200, validators=[recipes.validators.validate_name], verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='text',
            field=models.TextField(help_text='Введите описание рецепта', validators=[recipes.validators.validate_text], verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.IntegerField(validators=[recipes.validators.validate_ingredients_amount], verbose_name='Количество'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(help_text='Выберите цвет', max_length=7, unique=True, verbose_name='Цвет'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(help_text='Введите название тега', max_length=200, unique=True, validators=[recipes.validators.validate_name], verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(help_text='Выберите уникальное название для URL-ссылки на тег', max_length=200, unique=True, verbose_name='Слаг'),
        ),
    ]