import discord
import asyncio
from discord.ext import commands
from src.utils.logger import get_logger

logger = get_logger("DiscordBot")

class MarketplaceDiscordBot:
    def __init__(self, token, channel_id, reply_callback=None):
        self.token = token
        self.channel_id = int(channel_id)
        self.reply_callback = reply_callback

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)

        self._setup_events()

    def _setup_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f"Discord Bot connected as {self.bot.user}")

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            # Check if message is a reply in the designated channel
            if message.channel.id == self.channel_id:
                # Basic format: !reply <profile_id> <thread_id> <message>
                if message.content.startswith("!reply"):
                    parts = message.content.split(" ", 3)
                    if len(parts) >= 4:
                        profile_id = parts[1]
                        thread_id = parts[2]
                        reply_text = parts[3]

                        if self.reply_callback:
                            success = self.reply_callback(profile_id, thread_id, reply_text)
                            if success:
                                await message.channel.send(f"✅ Reply sent to {thread_id} on profile {profile_id}")
                            else:
                                await message.channel.send(f"❌ Failed to send reply.")
                    else:
                        await message.channel.send("Invalid format. Use: !reply <profile_id> <thread_id> <message>")

    async def send_notification(self, profile_id, sender_name, message_preview):
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                msg = f"📩 **New Message**\n**Profile:** {profile_id}\n**From:** {sender_name}\n**Preview:** {message_preview}"
                await channel.send(msg)
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    def run_in_background(self):
        # In a real PyQt6 app, this needs to be run in an async QThread or QRunnable
        # combined with qasync to not block the main event loop.
        loop = asyncio.get_event_loop()
        loop.create_task(self.bot.start(self.token))
