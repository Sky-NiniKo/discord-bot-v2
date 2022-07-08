import _thread
import asyncio
import logging
import os
import platform
import time
from datetime import timedelta, date

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from python_script.activity import Activity
from python_script.command import Command
from python_script.game import GameEngine
from python_script.reaction import QuickDelete, reaction_add, reaction_remove
from python_script.sheet import AvatarHistory
from python_script.utils import set_client_id

if platform.system() == "Windows":
    os.environ['PATH'] = r'resource/cairo/Windows' + ';' + os.environ['PATH']

logger = logging.getLogger(__name__)
start = time.time()

load_dotenv()

# importation/définition des identifiants
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
OWNER = int(os.environ["OWNER"])
IMGUR_CLIENT_ID = os.environ["IMGUR_CLIENT_ID"]
set_client_id(IMGUR_CLIENT_ID)
sheet_a = os.environ["SHEET_AVATAR_HISTORY"]
sheet_m = os.environ["SHEET_SAVE_MSGS"]
sheet_s = os.environ["SHEET_STATISTICS"]
sheet_e = os.environ["SHEET_EVENT_DATE"]

# définition des classes
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
quick_delete = QuickDelete(bot, sheet_m)
game = GameEngine(bot, quick_delete)
avatar_history = AvatarHistory(bot, sheet_a)
activity = Activity(bot, sheet_e)
command = Command(bot, quick_delete, game, avatar_history, sheet_s, activity)


async def send_error(exception, user_id, message):
    logger.exception(exception)
    user = await bot.get_user(user_id)
    await user.send(message)


@bot.event
async def on_ready():
    print(f"Bot prêt en {round(time.time() - chrono, 3)}s\nTotal : {round(time.time() - start, 3)}s\n")

    if OWNER:
        bot.owner_id = OWNER

    try:
        print("Initialisation des événements.", end=" ")
        await activity.__init_events__()
        print("Terminé\nInitialisation de Quick Delete")
        bot.loop.create_task(quick_delete.__init_my_msgs__())
        print("Mise à jours des game_template et changement des activités\n")
        await game.update_game_template()
        await activity.change()

        tomorrow = (date.today() + timedelta(days=1)).day
        while date.today().day == tomorrow:
            await asyncio.sleep(1)
        everyday_task.start()
    except Exception as e:
        await send_error(e, bot.owner_id, "Il y a eu une erreur après le on_ready")
        import traceback as tb
        print(''.join(tb.format_exception(None, e, e.__traceback__)))


@bot.event
async def on_message(message):
    try:
        ctx = await bot.get_context(message)

        if message.author == bot.user:
            return

        if ctx.channel.id in (x.id for x in list(game.games.keys())):
            await game.message(ctx)
        elif message.content.startswith("="):
            await command.calculate(ctx)
        elif message.content.startswith(f"{bot.command_prefix}help"):
            await command.aide(ctx, message.content.split()[1:])
        elif message.content.startswith(bot.command_prefix):
            await bot.process_commands(message)
    except Exception as e:
        await send_error(e, bot.owner_id, "Il y a eu une erreur sur un message")
        import traceback as tb
        print(''.join(tb.format_exception(None, e, e.__traceback__)))


@bot.event
async def on_raw_reaction_add(payload):
    try:
        if payload.channel_id in [x.id for x in list(game.games.keys())] and payload.user_id != bot.user.id:
            await game.reaction(payload)
        else:
            await reaction_add(payload, quick_delete, bot)
    except Exception as e:
        await send_error(e, bot.owner_id, "Il y a eu une erreur après que quelqu'un a réagit")
        import traceback as tb
        print(''.join(tb.format_exception(None, e, e.__traceback__)))


@bot.event
async def on_raw_reaction_remove(payload):
    try:
        await reaction_remove(payload, bot)
    except Exception as e:
        await send_error(e, bot.owner_id, "Il y a eu une erreur après que quelqu'un a enlever sa réaction")
        import traceback as tb
        print(''.join(tb.format_exception(None, e, e.__traceback__)))


@tasks.loop(hours=24)
async def everyday_task():
    print("Mise à jours des game_template et changement des activités\n")
    await game.update_game_template()
    await activity.change()
    print("Mise à jours de l'historique des avatars")
    _thread.start_new_thread(avatar_history.update, ())


# lancement du bot
bot.add_cog(command)
chrono = time.time()
print(f"Lancement du bot après {round(time.time() - start, 3)}s")
bot.run(DISCORD_BOT_TOKEN)
