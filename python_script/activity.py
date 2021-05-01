import random
from datetime import date, timedelta, datetime

import discord
from discord.ext.commands import Bot

from python_script.sheet import EventsDate


def easter_date(year=date.today().year):
    # Calcule le jour de la fête de pâques
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = f // 31
    day = f % 31 + 1
    return date(year, month, day)


class Activity:
    def __init__(self, bot: Bot, sheet_id: str):
        self.bot = bot
        self.sheet = EventsDate(sheet_id)
        self.events = {}
        self.activities = [("joue", "tourner en rond"), ("joue", "faire ses devoirs"), ("regarde", "des animées"),
                           ("joue", "pile ou face"), ("joue", "dire n'importe quoi"), ("joue", "faire une omelette"),
                           ("écoute", "de la musique"), ("joue", "lancer des dés"), ("joue", "faire des top 1"),
                           ("joue", "se questionner sur son existance"), ("regarde", "YouTube"),
                           ("joue", "énerver des gens"),
                           ("joue", "faire des choses pas très catholique (mais il est athée)"),
                           ("joue", "faire des gâteaux"), ("joue", "envoyer des message"),
                           ("joue", "la machine à café"), ("joue", "au frigo"),
                           ("joue", "jjjoue à jjjouùe à jjjoùée à jjjouùée àa"), ("joue", "cube cube"),
                           ("regarde", "les étoiles"), ("regarde", "le ciel"), ("écoute", "[inserer musique]"),
                           ("joue", "avec un sombrero"), ("regarde", "les fautes de français des gens pas doués")]

    async def __init_events__(self):
        self.events = await self.sheet.get()

    def add(self, event_date, event_type, activity_name):
        self.events[event_date] = [event_type, activity_name]
        self.sheet.add(event_date, event_type, activity_name)

    async def change_to(self, event_type=None, activity_name=None, **kwargs):
        if activity_name is None:
            raise ValueError("No activity name")
        if event_type == "regarde":
            await self.bot.change_presence(activity=discord.Activity(type=3, name=activity_name, **kwargs))
        elif event_type == "écoute":
            await self.bot.change_presence(activity=discord.Activity(type=2, name=activity_name, **kwargs))
        elif event_type == "joue":
            await self.bot.change_presence(activity=discord.Game(name=activity_name))
        else:
            await self.bot.change_presence(activity=discord.CustomActivity(name=activity_name, **kwargs))

    async def change(self):
        day = date.today()
        year = day.year

        # événement déjà passer
        if len(self.events) >= 1 and str(day - timedelta(days=1)) in self.events:
            self.sheet.remove([str(day - timedelta(days=1)), self.events[str(day - timedelta(days=1))]])
            del self.events[str(day - timedelta(days=1))]

        if len(self.events) >= 1 and str(day) in self.events:  # événement rajouter manuellement
            event_type, activity_name = self.events[str(day)]
            await self.change_to(event_type=event_type, activity_name=activity_name)
        elif day == date(year, 12, 24):  # noël
            await self.change_to(activity_name="est triste car il n'a pas eu de cadeaux", emoji="😭")
        elif day == date(year, 7, 14):  # 14 juillet
            await self.change_to("regarde", "tous les anciens défilés")
        elif day == easter_date():  # pâque
            await self.change_to("joue", "récolter des œufs en chocolat")
        else:
            random.seed(str(day))  # faire en sorte que l'aléatoire dépende du jour
            event_type, activity_name = random.choice(self.activities)  # activité aléatoire
            await self.change_to(event_type, activity_name)

    def get_event_list(self):
        dates = list(self.events.keys())
        dates.sort(key=lambda event_date: datetime.strptime(date, "%Y-%m-%d"))
        return [[one_date] + self.events[one_date] for one_date in dates]
