# Generated by Django 5.2 on 2025-06-20 21:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_alter_user_is_bot'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='latitude_center',
            new_name='user_latitude',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='longitude_center',
            new_name='user_longitude',
        ),
        migrations.RemoveField(
            model_name='user',
            name='map_zoom',
        ),
    ]
