import asyncio

from discord.utils import get

from .sheet import SaveMsgs


class QuickDelete:
    def __init__(self, bot, sheet_id):
        self.bot = bot
        self.save = SaveMsgs(sheet_id, self.bot)
        self.my_msg = {}
        self.ok = False

    async def __init_my_msgs__(self):
        self.my_msg.update(await self.save.get())
        self.ok = True
        print("Initialisation de Quick Delete terminé\n")

    async def wait_for_ok(self):
        while not self.ok:
            await asyncio.sleep(1)

    async def add(self, msgs):
        self.my_msg[msgs[0].id] = msgs
        await msgs[0].add_reaction("🗑️")
        # await self.wait_for_ok()
        # self.save.add(msgs)

    async def delete(self, payload):
        message_id = payload.message_id  # récupérer le numéro du message
        await self.wait_for_ok()

        if message_id in self.my_msg:
            msgs = self.my_msg[message_id]
            for n, msg in enumerate(msgs):
                if str(msgs[0].channel.type) != "private" or msg.author == self.bot.user:
                    await msg.delete()
                elif n == 0:
                    await msg.remove_reaction("🗑️", self.bot.user)
            self.save.remove(self.my_msg[message_id])
            del self.my_msg[message_id]

    def get_save_msgs(self) -> SaveMsgs:
        return self.save


async def reaction_add(payload, quick_delete, bot):
    emoji = payload.emoji.name  # récupérer l'émoji
    canal = payload.channel_id  # récupérer le numéro du canal
    message_id = payload.message_id  # récupérer le numéro du message

    if emoji == "🗑️" and payload.user_id != bot.user.id:
        await quick_delete.delete(payload)

    if canal == 718396837442355240 and message_id == 722054829907640351 and emoji == "😎":
        partisans_animees_role = get(bot.get_guild(payload.guild_id).roles, name="Partisans des animées")
        member = payload.member
        await member.add_roles(partisans_animees_role)


async def reaction_remove(payload, bot):
    emoji = payload.emoji.name  # récupérer l'émoji
    canal = payload.channel_id  # récupérer le numéro du canal
    message_id = payload.message_id  # récupérer le numéro du message

    if canal == 718396837442355240 and message_id == 722054829907640351 and emoji == "😎":
        partisans_animees_role = get(bot.get_guild(payload.guild_id).roles, name="Partisans des animées")
        member = bot.get_guild(payload.guild_id).get_member(payload.user_id)
        await member.remove_roles(partisans_animees_role)
