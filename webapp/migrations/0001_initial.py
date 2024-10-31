# Generated by Django 4.2.16 on 2024-10-30 19:29

import django.db.models.deletion
from django.db import migrations, models

import colorfield.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("_created", models.DateTimeField(auto_now_add=True)),
                ("_updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "color",
                    colorfield.fields.ColorField(default="#FF0000", image_field=None, max_length=25, samples=None),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Channel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("_created", models.DateTimeField(auto_now_add=True)),
                ("_updated", models.DateTimeField(auto_now=True)),
                ("telegram_id", models.BigIntegerField()),
                ("title", models.CharField(blank=True, max_length=255)),
                ("about", models.TextField(blank=True)),
                ("telegram_location", models.TextField(blank=True)),
                ("username", models.CharField(blank=True, max_length=255)),
                ("date", models.DateTimeField(null=True)),
                ("participants_count", models.PositiveBigIntegerField(null=True)),
                ("is_interesting", models.BooleanField(default=None, null=True)),
                ("is_active", models.BooleanField(default=False)),
                ("are_messages_crawled", models.BooleanField(default=False)),
                ("broadcast", models.BooleanField(default=True)),
                ("verified", models.BooleanField(default=False)),
                ("megagroup", models.BooleanField(default=False)),
                ("gigagroup", models.BooleanField(default=False)),
                ("restricted", models.BooleanField(default=False)),
                ("signatures", models.BooleanField(default=False)),
                ("min", models.BooleanField(default=False)),
                ("scam", models.BooleanField(default=False)),
                ("has_link", models.BooleanField(default=False)),
                ("has_geo", models.BooleanField(default=False)),
                ("slowmode_enabled", models.BooleanField(default=False)),
                ("fake", models.BooleanField(default=False)),
                ("access_hash", models.BigIntegerField(null=True)),
                ("in_degree", models.PositiveIntegerField(null=True)),
                ("out_degree", models.PositiveIntegerField(null=True)),
                (
                    "category",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="webapp.category"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("_created", models.DateTimeField(auto_now_add=True)),
                ("_updated", models.DateTimeField(auto_now=True)),
                ("telegram_id", models.BigIntegerField()),
                ("date", models.DateTimeField(null=True)),
                ("out", models.BooleanField(default=False)),
                ("mentioned", models.BooleanField(default=False)),
                ("post", models.BooleanField(default=False)),
                ("from_scheduled", models.BooleanField(default=False, null=True)),
                ("message", models.TextField(blank=True)),
                ("forwarded_from_private", models.PositiveBigIntegerField(null=True)),
                ("missing_references", models.TextField(blank=True)),
                ("grouped_id", models.BigIntegerField(null=True)),
                ("views", models.PositiveBigIntegerField(null=True)),
                ("forwards", models.PositiveBigIntegerField(null=True)),
                ("pinned", models.BooleanField(default=False, null=True)),
                ("has_been_pinned", models.BooleanField(default=False)),
                ("webpage_url", models.URLField(blank=True, default="", max_length=255)),
                ("webpage_type", models.CharField(blank=True, default="", max_length=255)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="message_set", to="webapp.channel"
                    ),
                ),
                (
                    "forwarded_from",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="forwarded_message_set",
                        to="webapp.channel",
                    ),
                ),
                ("references", models.ManyToManyField(related_name="reference_message_set", to="webapp.channel")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("_created", models.DateTimeField(auto_now_add=True)),
                ("_updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "color",
                    colorfield.fields.ColorField(default="#FF0000", image_field=None, max_length=25, samples=None),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProfilePicture",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("_created", models.DateTimeField(auto_now_add=True)),
                ("_updated", models.DateTimeField(auto_now=True)),
                ("telegram_id", models.BigIntegerField()),
                ("picture", models.ImageField(max_length=255, upload_to="")),
                ("date", models.DateTimeField(null=True)),
                ("channel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="webapp.channel")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="MessagePicture",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("_created", models.DateTimeField(auto_now_add=True)),
                ("_updated", models.DateTimeField(auto_now=True)),
                ("telegram_id", models.BigIntegerField()),
                ("picture", models.ImageField(max_length=255, upload_to="")),
                ("date", models.DateTimeField(null=True)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="webapp.message")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="channel",
            name="organization",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="webapp.organization"),
        ),
    ]
