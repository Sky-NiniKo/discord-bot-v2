import _thread
import asyncio
import configparser
import logging
import os
import platform
import time
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

from python_script.activity import Activity
from python_script.command import Command
from python_script.dictionary import Dictionary
from python_script.game import GameEngine
from python_script.reaction import QuickDelete, reaction_add, reaction_remove
from python_script.sheet import AvatarHistory
from python_script.utils import set_client_id

if platform.system() == "Windows":
    os.environ['PATH'] = r'resource/cairo/Windows' + ';' + os.environ['PATH']

logger = logging.getLogger(__name__)
start = time.time()

# importation/définition des indentifiants
if os.path.isfile(r"resource/credentials/creds.ini"):
    creds = configparser.ConfigParser()
    creds.read("resource/credentials/creds.ini")
    TOKEN = creds.get("Discord Bot", "TOKEN")
    Creator_ID = int(creds.get("Discord Bot", "Creator_ID"))
    Client_ID = creds.get("Imgur", "Client_ID")
    set_client_id(Client_ID)
    sheet_a = creds.get("Google Sheet", "Avatar_history")
    sheet_m = creds.get("Google Sheet", "Save_msgs")
    sheet_s = creds.get("Google Sheet", "Statistics")
    sheet_e = creds.get("Google Sheet", "Event_date")
else:
    TOKEN = os.environ["Discord_Bot_TOKEN"]
    Creator_ID = int(os.environ["Discord_Bot_Creator_ID"])
    Client_ID = os.environ["Imgur_Client_ID"]
    set_client_id(Client_ID)
    sheet_a = os.environ["Google_Sheet_Avatar"]
    sheet_m = os.environ["Google_Sheet_Save_msgs"]
    sheet_s = os.environ["Google_Sheet_Statistics"]
    sheet_e = os.environ["Google_Sheet_Event"]

# définition des class
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
dictionary = Dictionary()
quick_delete = QuickDelete(bot, sheet_m)
game = GameEngine(bot, quick_delete)
avatar_history = AvatarHistory(bot, sheet_a)
activity = Activity(bot, sheet_e)
command = Command(bot, quick_delete, game, avatar_history, sheet_s, activity)


async def send_error(exception, user_id, message):
    logger.exception(exception)
    user = await bot.fetch_user(user_id)
    await user.send(message)


@bot.event
async def on_ready():
    print(f"Bot prêt en {round(time.time() - chrono, 3)}s\nTotal : {round(time.time() - start, 3)}s\n")
    try:
        print("Initialisation des évenements.", end=" ")
        await activity.__init_events__()
        print("Terminé\nInitialisation de Quick Delete")
        bot.loop.create_task(quick_delete.__init_my_msgs__())
        print("Mise à jours des game_template et changement des activités\n")
        await game.update_game_template()
        await activity.change()

        tomorrow = (datetime.now() + timedelta(days=1)).day
        while datetime.now().day == tomorrow:
            await asyncio.sleep(1)
        everyday_task.start()
    except Exception as e:
        await send_error(e, Creator_ID, "Il y a eu une erreur après le on_ready")


@bot.event
async def on_message(message):
    try:
        ctx = await bot.get_context(message)

        if message.author == bot.user:
            return

        if ctx.channel.id in [x.id for x in list(game.games.keys())]:
            await game.message(ctx)
        elif message.content.startswith("="):
            await command.calculate(ctx)
        elif message.content.startswith(f"{bot.command_prefix}help"):
            await command.aide(ctx, message.content.split()[1:])
        elif message.content.startswith(bot.command_prefix):
            await bot.process_commands(message)
        else:
            await dictionary.search(ctx)
    except Exception as e:
        await send_error(e, Creator_ID, "Il y a eu une erreur sur un message")


@bot.event
async def on_raw_reaction_add(payload):
    try:
        if payload.channel_id in [x.id for x in list(game.games.keys())] and payload.user_id != bot.user.id:
            await game.reaction(payload)
        else:
            await reaction_add(payload, quick_delete, bot)
    except Exception as e:
        await send_error(e, Creator_ID, "Il y a eu une erreur après que quelqu'un a réagie")


@bot.event
async def on_raw_reaction_remove(payload):
    try:
        await reaction_remove(payload, bot)
    except Exception as e:
        await send_error(e, Creator_ID, "Il y a eu une erreur après que quelqu'un a enlever sa réaction")


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
bot.run(TOKEN)
