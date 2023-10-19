# Generated by Django 4.2.6 on 2023-10-18 20:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=255)),
                ('user_name', models.CharField(default='user', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('title', models.CharField(max_length=250)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('body', models.TextField()),
                ('publish', models.DateTimeField(default=django.utils.timezone.now)),
                ('published', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published')], default='draft', max_length=10)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blog_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-publish',),
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(default='user', max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('home_page', models.URLField(blank=True, verbose_name='Home Page')),
                ('captcha', models.CharField(default='', max_length=48, verbose_name='CAPTCHA')),
                ('image', models.ImageField(blank=True, help_text='Upload an image (optional)', null=True, upload_to='comment_images', verbose_name='Upload Image')),
                ('text_file', models.FileField(blank=True, help_text='Upload a text file (optional)', null=True, upload_to='comment_text_files', verbose_name='Upload Text File')),
                ('client_info', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='comments.clientinfo')),
                ('parent_comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies_to', to='comments.comment')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='comments.post')),
            ],
        ),
    ]
