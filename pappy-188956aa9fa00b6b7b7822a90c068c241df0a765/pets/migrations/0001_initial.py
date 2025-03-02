# Generated by Django 5.0.2 on 2025-01-26 14:56

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('announcements', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('is_breeding_match', models.BooleanField(default=False, verbose_name='Совпадение для вязки')),
                ('compatibility_score', models.FloatField(blank=True, null=True, verbose_name='Оценка совместимости')),
                ('announcement1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_first', to='announcements.announcement', verbose_name='Объявление 1')),
                ('announcement2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_second', to='announcements.announcement', verbose_name='Объявление 2')),
                ('user1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_user1', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь 1')),
                ('user2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_user2', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь 2')),
            ],
            options={
                'verbose_name': 'Совпадение',
                'verbose_name_plural': 'Совпадения',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SwipeAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.CharField(choices=[('like', 'Лайк'), ('dislike', 'Дизлайк')], max_length=10, verbose_name='Направление')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('announcement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pets_swipes', to='announcements.announcement', verbose_name='Объявление')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pets_swipes', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Действие свайпа',
                'verbose_name_plural': 'Действия свайпов',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'announcement')},
            },
        ),
        migrations.CreateModel(
            name='SwipeHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата просмотра')),
                ('is_returned', models.BooleanField(default=False, verbose_name='Было возвращение')),
                ('announcement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pets_view_history', to='announcements.announcement', verbose_name='Объявление')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pets_swipe_history', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'История свайпов',
                'verbose_name_plural': 'История свайпов',
                'ordering': ['-viewed_at'],
                'unique_together': {('user', 'announcement')},
            },
        ),
    ]
