import glob
import os
from dataclasses import dataclass

from django.conf import settings
from django.core.management.base import BaseCommand

from webapp.models import Channel, Message, MessagePicture, ProfilePicture

from asgiref.sync import async_to_sync, sync_to_async
from telethon import errors
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel as TelegramChannel, ChatFull


@dataclass
class Data:
    data: TelegramChannel
    full_data: ChatFull
    profile_picture_list: list

    def total_cost(self) -> float:
        return self.unit_price * self.quantity_on_hand


class Command(BaseCommand):
    args = ""
    help = "crawling Telegram groups"
    wait_time = 1  # in seconds

    def handle(self, *args, **options):
        for telegram_channel in (
            Channel.objects.filter(organization__is_interesting=True).order_by("-id").iterator(chunk_size=10)
        ):
            entity = async_to_sync(self.get_entity)(telegram_channel.telegram_id)
            telegram_channel.set_from_telegram_object(entity.data)
            telegram_channel.set_from_full_telegram_object(entity.full_data)
            telegram_channel.save()
            for telegram_picture, picture_filename in entity.profile_picture_list:
                ProfilePicture.from_telegram_object(
                    telegram_picture,
                    force_update=True,
                    defaults={"channel": telegram_channel, "picture": picture_filename},
                )
            async_to_sync(self.set_messages)(telegram_channel)

        self.clean_leftovers()

        for c in Channel.objects.filter(organization__is_interesting=False):
            c.save()

    async def set_messages(self, channel):
        async with TelegramClient("anon", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH) as client:
            await client.start(phone=settings.TELEGRAM_PHONE_NUMBER)
            last_message = await channel.message_set.order_by("telegram_id").alast()
            min_id = last_message.telegram_id if last_message is not None else 0
            message_list = [
                m async for m in client.iter_messages(channel.telegram_id, min_id=min_id, wait_time=self.wait_time)
            ]
            max_id = None
            if not channel.are_messages_crawled:
                first_message = await channel.message_set.order_by("telegram_id").afirst()
                max_id = first_message.telegram_id if first_message else None
            if max_id is not None:
                message_list += [
                    m async for m in client.iter_messages(channel.telegram_id, max_id=max_id, wait_time=self.wait_time)
                ]

            for telegram_message in message_list:
                message = await Message.afrom_telegram_object(
                    telegram_message, force_update=True, defaults={"channel": channel}
                )
                missing_references = []
                if (
                    telegram_message.fwd_from
                    and telegram_message.fwd_from.from_id
                    and hasattr(telegram_message.fwd_from.from_id, "channel_id")
                ):
                    if await Channel.objects.filter(telegram_id=telegram_message.fwd_from.from_id.channel_id).aexists():
                        message.forwarded_from = await Channel.objects.aget(
                            telegram_id=telegram_message.fwd_from.from_id.channel_id
                        )
                    else:
                        try:
                            self.wait()
                            new_telegram_channel = self.client.get_entity(telegram_message.fwd_from.from_id.channel_id)
                            message.forwarded_from = Channel.from_telegram_object(
                                new_telegram_channel, force_update=True
                            )
                        except errors.rpcerrorlist.ChannelPrivateError:
                            message.forwarded_from_private = telegram_message.fwd_from.from_id.channel_id
                        except AttributeError:
                            message.forwarded_from_private = 0

                    for reference in message.get_telegram_references():
                        reference = reference.strip().lower()
                        if reference in self.skippable_references:
                            continue
                        if Channel.objects.filter(username=reference).exists():
                            message.references.add(Channel.objects.filter(username=reference).first())
                        else:
                            try:
                                self.wait()
                                new_telegram_channel = self.client.get_entity(reference)
                                message.references.add(
                                    Channel.from_telegram_object(new_telegram_channel, force_update=True)
                                )
                            except (ValueError, errors.rpcerrorlist.UsernameInvalidError):
                                pass
                            except Exception:
                                missing_references.append(reference)

                if telegram_message.entities:
                    for entity in telegram_message.entities:
                        tme = "https://t.me/"
                        if hasattr(entity, "url") and entity.url.startswith(tme):
                            reference = entity.url[len(tme) :].split("/")[0].strip().lower()
                        else:
                            continue
                        if reference in self.skippable_references:
                            continue
                        if Channel.objects.filter(username=reference).exists():
                            message.references.add(Channel.objects.filter(username=reference).first())
                        else:
                            try:
                                self.wait()
                                new_telegram_channel = self.client.get_entity(reference)
                                message.references.add(
                                    Channel.from_telegram_object(new_telegram_channel, force_update=True)
                                )
                            except (ValueError, errors.rpcerrorlist.UsernameInvalidError):
                                pass
                            except Exception:
                                missing_references.append(reference)

                if telegram_message.media:
                    self.get_message_picture(telegram_message)
                    if hasattr(telegram_message.media, "webpage"):
                        message.webpage_url = (
                            telegram_message.media.webpage.url if hasattr(telegram_message.media.webpage, "url") else ""
                        )
                        message.webpage_type = (
                            telegram_message.media.webpage.type
                            if hasattr(telegram_message.media.webpage, "type")
                            else ""
                        )

                if missing_references:
                    message.missing_references = "|" + "|".join(missing_references)

                await sync_to_async(message.save)()

            channel.are_messages_crawled = True
            await sync_to_async(channel.save)()
            print(f"  * {len(message_list)} messaggi")

    async def get_entity(self, channel):
        async with TelegramClient("anon", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH) as client:
            await client.start(phone=settings.TELEGRAM_PHONE_NUMBER)
            data = await client.get_entity(channel)
            full_data = await client(GetFullChannelRequest(channel=channel))
            picture_list = await client.get_profile_photos(channel)
            return Data(data, full_data, profile_picture_list=[(p, client.download_media(p)) for p in picture_list])

    def clean_leftovers(self):
        for file_path in glob.glob(f"{settings.BASE_DIR}/photo_*.jpg"):
            try:
                os.remove(file_path)
            except Exception:
                pass

    def get_message_picture(self, telegram_message):
        if not hasattr(telegram_message.media, "photo"):
            return

        try:
            picture_filename = self.client.download_media(telegram_message)
            MessagePicture.from_telegram_object(
                telegram_message.media.photo,
                force_update=True,
                defaults={
                    "message": Message.objects.get(
                        channel__telegram_id=telegram_message.peer_id.channel_id, telegram_id=telegram_message.id
                    ),
                    "picture": picture_filename,
                },
            )
        except (errors.rpcerrorlist.FileMigrateError, ValueError) as e:
            print(e)
            print(telegram_message.__dict__)
