import datetime
import os
import re

from django.conf import settings
from django.db import models

from webapp.models import Category, Organization
from webapp_engine.models import TelegramBaseModel, TelegramBasePictureModel


class Channel(TelegramBaseModel):
    TELEGRAM_OBJECT_PROPERTIES = (
        "title",
        "date",
        "broadcast",
        "verified",
        "megagroup",
        "restricted",
        "signatures",
        "min",
        "scam",
        "has_link",
        "has_geo",
        "slowmode_enabled",
        "fake",
        "gigagroup",
        "access_hash",
        "username",
    )
    title = models.CharField(max_length=255, blank=True)
    about = models.TextField(blank=True)
    telegram_location = models.TextField(blank=True)
    username = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(null=True)
    participants_count = models.PositiveBigIntegerField(null=True)
    is_active = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)
    are_messages_crawled = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    broadcast = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    megagroup = models.BooleanField(default=False)
    gigagroup = models.BooleanField(default=False)
    restricted = models.BooleanField(default=False)
    signatures = models.BooleanField(default=False)
    min = models.BooleanField(default=False)
    scam = models.BooleanField(default=False)
    has_link = models.BooleanField(default=False)
    has_geo = models.BooleanField(default=False)
    slowmode_enabled = models.BooleanField(default=False)
    fake = models.BooleanField(default=False)
    access_hash = models.BigIntegerField(null=True)
    in_degree = models.PositiveIntegerField(null=True)
    out_degree = models.PositiveIntegerField(null=True)

    def __str__(self):
        return self.title or str(self.telegram_id)

    @property
    def telegram_url(self):
        return f"t.me/{self.username or self.telegram_id}"

    @property
    def profile_picture(self):
        return self.profilepicture_set.order_by("date").last()

    @property
    def activity_period(self):
        date_template = "%B %Y"
        messages = self.message_set.all().order_by("date")
        start = self.date
        end = self.date
        if messages.exists():
            start = min(start, messages.first().date)
            end = max(end, messages.last().date)

        return (
            f"{start.strftime(date_template)} - {end.strftime(date_template)}"
            if end < datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
            else f"{start.strftime(date_template)} - "
        )

    def save(self, *args, **kwargs):
        self.username = self.username or ""
        super().save(*args, **kwargs)
        self.in_degree = (
            Message.objects.filter(channel__organization__is_interesting=True, forwarded_from=self)
            .exclude(channel=self)
            .count()
        )
        self.out_degree = (
            Message.objects.filter(channel=self, forwarded_from__organization__is_interesting=True)
            .exclude(forwarded_from=self)
            .count()
        )
        super().save(update_fields=["in_degree", "out_degree"])


class Message(TelegramBaseModel):
    TELEGRAM_OBJECT_PROPERTIES = (
        "date",
        "out",
        "mentioned",
        "post",
        "from_scheduled",
        "message",
        "grouped_id",
        "views",
        "forwards",
        "pinned",
    )
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="message_set")
    date = models.DateTimeField(null=True)
    out = models.BooleanField(default=False)
    mentioned = models.BooleanField(default=False)
    post = models.BooleanField(default=False)
    from_scheduled = models.BooleanField(default=False, null=True)
    message = models.TextField(blank=True)
    forwarded_from = models.ForeignKey(
        Channel, on_delete=models.SET_NULL, null=True, related_name="forwarded_message_set"
    )
    forwarded_from_private = models.PositiveBigIntegerField(null=True)
    references = models.ManyToManyField(Channel, related_name="reference_message_set")
    missing_references = models.TextField(blank=True)
    grouped_id = models.BigIntegerField(null=True)
    views = models.PositiveBigIntegerField(null=True)
    forwards = models.PositiveBigIntegerField(null=True)
    pinned = models.BooleanField(null=True, default=False)
    has_been_pinned = models.BooleanField(default=False)
    webpage_url = models.URLField(max_length=255, default="", blank=True)
    webpage_type = models.CharField(max_length=255, default="", blank=True)

    def __str__(self):
        return f"{self.channel.title} [{self.date or self.telegram_id}]"

    def save(self, *args, **kwargs):
        self.message = self.message or ""
        super().save(*args, **kwargs)
        if self.pinned:
            self.has_been_pinned = True
            super().save(update_fields=("has_been_pinned",))

    @classmethod
    def _args_for_from_telegram_object(cls, telegram_object):
        return {"telegram_id": telegram_object.id, "channel__telegram_id": telegram_object.peer_id.channel_id}

    def get_telegram_references(self):
        refs = []
        for url in re.findall("t.me/(?:[-\w.]|(?:%[\da-fA-F]{2}))+", str(self.message)):
            refs.append(url[5:])

        return refs

    @property
    def message_picture(self):
        return self.messagepicture_set.order_by("date").last()

    @property
    def telegram_url(self):
        return os.path.join(self.channel.telegram_url, str(self.telegram_id))


class ProfilePicture(TelegramBasePictureModel):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)

    def get_media_path(self):
        return os.path.join(settings.MEDIA_ROOT, "channels", self.channel.username, "profile")


class MessagePicture(TelegramBasePictureModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)

    def get_media_path(self):
        return os.path.join(settings.MEDIA_ROOT, "channels", self.message.channel.username, "message")
