import random

import discord
from discord.ext import commands
from discord.ext.commands import Bot

from .activity import Activity
from .calculator import calculate
from .game import GameEngine
from .reaction import QuickDelete
from .sheet import AvatarHistory, Statistics
from .utils import is_in, values_from_one


class Command(commands.Cog):
    def __init__(self, bot: Bot, quick_delete: QuickDelete, game: GameEngine, avatar_history: AvatarHistory, sheet_s,
                 activity: Activity):
        self.bot = bot
        self.quick_delete = quick_delete
        self.game = game
        self.avatar_history = avatar_history
        self.statistics_sheet = Statistics(sheet_s)
        self.activity = activity
        self.command_list = {"?": ("help", "aide", "?"), "=": ("=", "calc"), "clear_all": ("clearA", "videA", "purgeA"),
                             "clear": ("vide", "clear", "propre", "nettoyer", "purge"), "aliases": ("aliases", "alias"),
                             "connect_4": ("puissance_4", "connect_4", "puissance4", "connect4"), "dice": ("dé", "de"),
                             "update_avatar": ("update_avatar", "update_sheet"), "ping": ("ping", "pg"),
                             "update_game_template": ("update_game_template", "update_modèle"), "code": ("code",),
                             "add_event": ("add_event", "+event"), "avatar": ("avatar", "skin"),
                             "event_list": ("event", "event_list"), "pile_ou_face": ("pile_ou_face", "pf"),
                             "statistics_sheet": ("statistique", "stat")}

    # ------------- #
    #    command    #
    # ------------- #

    @commands.command(aliases=["+event"])
    async def add_event(self, ctx, date, event_type, *activity_name):
        activity_name = " ".join(activity_name)
        self.activity.add(date, event_type, activity_name)
        msg = await ctx.send("Votre événement a été correctement enregistrer")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "add_event")

    @commands.command(aliases=["skin"])
    async def avatar(self, ctx):
        msg = await ctx.send("https://docs.google.com/spreadsheets/d/18yuov4obW1oIdaOO-SUivX_owepN6op-Nte8Vz-m4fQ/")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "avatar")

    @commands.command(aliases=["=", "calc"])
    async def calculate(self, ctx):
        content = ctx.message.content
        try:
            result = calculate(content[content.find("=") + 1:])
            if result is True:
                msgs = [await ctx.send(file=discord.File("resource/temp/result.png"))]
            elif len(result) <= 10000:
                msgs = []
                for part in [result[index: index + 1974] for index in range(0, len(result), 1974)]:
                    msgs.append(await ctx.send(part))
                msgs.reverse()
            else:
                msgs = [await ctx.send(result)]
        except (ValueError, SyntaxError, IndexError, NotImplementedError):
            msgs = [await ctx.send("Désoler mais je ne peux pas calculer ceci.")]
        except KeyboardInterrupt:
            msgs = [await ctx.send("Votre calcule est trop compliquer, je ne peux pas le traiter.")]
        await self.quick_delete.add(msgs + [ctx.message])
        self.statistics_sheet.add(str(ctx.author), "calculate")

    @commands.command(aliases=["vide", "propre", "nettoyer", "purge"])
    async def clear(self, ctx, number: int):
        async for msg in ctx.message.channel.history():
            if msg.author == self.bot.user:
                if number == 0:
                    break
                await msg.delete()
                number -= 1
        await self.quick_delete.add([ctx.message])
        self.statistics_sheet.add(str(ctx.author), "clear")

    @commands.command(aliases=["clearA", "videA", "purgeA"])
    @commands.has_permissions(manage_messages=True)
    async def clear_all(self, ctx, number: int):
        number = int(number)
        async for msg in ctx.message.channel.history(limit=number + 1):
            await msg.delete()
        self.statistics_sheet.add(str(ctx.author), "clear_all")

    @commands.command()
    async def code(self, ctx):
        msg = await ctx.author.send("https://github.com/Sky-NiniKo/discord-bot-v2")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "code")

    @commands.command(aliases=["dé", "de"])
    async def dice(self, ctx, *args):
        try:
            face = int(args[0])
        except IndexError:
            face = 6
        answer = random.randint(1, face)

        msgs = []
        if answer <= 6:
            msgs.append(await ctx.send(file=discord.File(f"resource/assets/dice/{answer}.png"), delete_after=3600))
        msgs.append(await ctx.send(f"Le dé est tombé sur {answer}"))
        await self.quick_delete.add(msgs + [ctx.message])
        self.statistics_sheet.add(str(ctx.author), "dice")

    @commands.command(aliases=["event"])
    async def event_list(self, ctx):
        if events := self.activity.get_event_list():
            msg = await ctx.send("\n".join(" ".join(x) for x in events))
        else:
            msg = await ctx.send("Il n'y a pas d'événement prévu")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "event_list")

    @commands.command(aliase=["pf"])
    async def pile_ou_face(self, ctx):
        answer = "Pile" if random.random() < 0.5 else "Face"
        msg2 = await ctx.send(file=discord.File(f"resource/assets/pièce/{answer.lower()}.png"), delete_after=3600)
        msg = await ctx.send(answer)
        await self.quick_delete.add([msg, msg2, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "pile_ou_face")

    @commands.command(aliases=["pg"])
    async def ping(self, ctx):
        msg = await ctx.send(f"Pong!\n{round(self.bot.latency * 1000, 3)} ms.")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "ping")

    @commands.command(aliases=["statistique", "stat"])
    async def statistics(self, ctx):
        msg = await ctx.send("https://docs.google.com/spreadsheets/d/19NMGwDkniWv3yonHGwGLE1XpoMsy9RMawI78Kwv1bGo/")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "statistique")

    @commands.command(aliases=["update_sheet"])
    async def update_avatar(self, ctx):
        self.avatar_history.update()
        msg = await ctx.send("L'historique des avatars a été mis à jour.")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "update_avatar")

    @commands.command(aliases=["update_modèle"])
    async def update_game_template(self, ctx):
        await self.game.update_game_template()
        msg = await ctx.send("Les salon modèle pour les jeux ont été mis à jour.")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "update_game_template")

    @commands.command(aliases=["alias"])
    async def aliases(self, ctx, command_name):
        try:
            msg = await ctx.send(values_from_one(self.command_list, command_name))
        except ValueError:
            msg = await ctx.send("Commande inconnue")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "aliases")

    @commands.command(aliases=["?"])
    async def aide(self, ctx, *args: str) -> None:
        if args:
            if isinstance(args[0], list):
                args = tuple(args[0]) + args[1:]
            if is_in(self.command_list["?"], args):
                msg = await ctx.send("La commande `!? (commande)` permet d'obtenir de l'aide sur une commande "
                                     "ou la liste des commandes avec `!?`")
            elif is_in(self.command_list["="], args):
                msg = await ctx.send("Permet de faire un calcule rapide\nEx: `=7+5` -> 12")
            elif is_in(self.command_list["clear"], args):
                msg = await ctx.send("Nettoie un nombre de messages mes messages\n"
                                     "Ex: `!clear 7` -> nettoie mes 7 plus récents messages")
            elif is_in(self.command_list["aliases"], args):
                msg = await ctx.send("Renvoie tout les aliases de la commande\n"
                                     f"Ex: `!aliases ?` -> {self.command_list['?']}")
            elif is_in(self.command_list["clear_all"], args) and ctx.author.permission_in(ctx.channel).manage_messages:
                msg = await ctx.send("Nettoie tout les messages les plus récents\n"
                                     "Ex: `!clearA 3` -> nettoie les 3 plus récents messages")
            elif is_in(self.command_list["ping"], args):
                msg = await ctx.send("Donne le ping que le bot à avec Discord")
            elif is_in(self.command_list["update_avatar"], args):
                msg = await ctx.send("Met à jour l'historique des avatars")
            elif is_in(self.command_list["update_game_template"], args):
                msg = await ctx.send("Met à jour la liste des salon modèles pour les jeux.\n"
                                     "*Note: Cette liste est automatiquement mis à jour tout les jours.*")
            elif is_in(self.command_list["add_event"], args):
                msg = await ctx.send(
                    "**Ajoute un événement.**\n"
                    "S'utile de cette façon: `!+event (année)-(mois)-(jour) (type) (nom de l'événement)`\n"
                    "`type` doit faire partie de cette liste: joue/regarde/écoute\n"
                    "Ex: `!+event 2030-01-02 regarde les étoiles` "
                    "-> ajoute un événement le 2 janvier 2030 qui dira `Regarde les étoiles`\n"
                    '*Note: joue ajoute automatiquement "à" ce qui donne joue à*')
            elif is_in(self.command_list["avatar"], args):
                msg = await ctx.send("Renvoie le lien d'un Google Sheet "
                                     "qui liste tout les avatars de toutes les personnes que le bot voie")
            elif is_in(self.command_list["code"], args):
                msg = await ctx.send("Donne le lien repo github de Sky Boot v2")
            elif is_in(self.command_list["dice"], args):
                msg = await ctx.send("Lance un dé.\n*Note: "
                                     "vous pouvez rajouter un nombre après `!de` pour changer le nombre de face du dé.")
            elif is_in(self.command_list["event_list"], args):
                msg = await ctx.send("Donne la liste des événement à venir.")
            elif is_in(self.command_list["pile_ou_face"], args):
                msg = await ctx.send("Lance un pièce.\nC'est tout.")
            elif is_in(self.command_list["statistics_sheet"], args):
                msg = await ctx.send("Donne le lien du Google Sheet avec les statistiques.\n"
                                     "*Note: vous pouvez demander à ne plus apparaître "
                                     "dans les statistiques en contactant Sky NiniKo.*")
            elif is_in(self.command_list["connect_4"], args):
                msg = await ctx.send("Permet de créé une partie de puissance 4.\n"
                                     "S'utilise de la manière suivante : `!puissance4 @(nom de ton adversaire)`\n"
                                     "*Note: tu peux mentionner plusieurs adversaires si tu le désir.*")
            elif is_in(self.command_list["chess"], args):
                msg = await ctx.send("Permet de créé une partie d'échecs.\n"
                                     "S'utilise de la manière suivante : `!échecs @(nom de ton adversaire)`\n"
                                     "*Note: tu peux mentionner le bot pour jouer contre lui.*")
            else:
                msg = await ctx.send("Commande inconnue")
        else:
            msg = await ctx.author.send("**Besoin d'aide** sur une commande ? Faite `!? (commande)`"
                                        "\nTu veux affronter ton ami aux **puissance 4** alors fait "
                                        "`!puissance4 @(nom de ton ami)`"
                                        "\nUne petite partie d'échecs ? Fait `!échecs @(nom de l'adversaire)`"
                                        "\nJe peux faire un **calcule** avec `=(calcule)`"
                                        "\nJe peux **nettoyer mes messages** avec `!clear (nombre de messages)`"
                                        "\nTu veux savoir le **ping** du bot alors fait `!ping`"
                                        "\nEnvie de **lancer un dé** ? `!de`"
                                        "\nJe peux **lancer une pièce** avec `!pf`"
                                        "\nPour voir **la liste des événement future** fait `!event`"
                                        "\nTu veux voir **l'historique des avatars** des personnes alors fait `!avatar`"
                                        "\nEnvie de **voir les autres manière d'écrire une commande** ? "
                                        "Fait `!aliases (commande)`"
                                        "\nPour **voir le code** fait `!code`"
                                        "\nJe fait des statistique et par soucie de transparence, "
                                        "tu peux **obtenir les statistiques** avec `!stat` car elles sont publique.")
        await self.quick_delete.add([msg, ctx.message])
        self.statistics_sheet.add(str(ctx.author), "aide")

    @commands.command(aliases=["puissance_4", "puissance4", "connect4"])
    async def connect_4(self, ctx):
        await self.game.connect_4(ctx)
        self.statistics_sheet.add(str(ctx.author), "connect_4")

    @commands.command(aliases=["échecs"])
    async def chess(self, ctx):
        await self.game.chess(ctx)
        self.statistics_sheet.add(str(ctx.author), "chess")
