# Generated by Django 4.2.16 on 2024-12-09 02:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Excel_App', '0004_alter_excelfile_file_alter_excelfile_file_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='excelfile',
            name='last_modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='excelfile',
            name='file',
            field=models.FileField(upload_to='excel_files/'),
        ),
        migrations.AlterField(
            model_name='excelfile',
            name='file_name',
            field=models.CharField(max_length=255),
        ),
    ]