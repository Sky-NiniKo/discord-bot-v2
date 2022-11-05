import os

import gspread
from discord import NotFound
from discord.ext.commands import Bot

from .utils import upload_image_on_imgur


class Sheet:
    def __init__(self, sheet_id: str):
        with open(r"resource/credentials/gcreds.json", "r") as gcreds_file:
            is_ok = gcreds_file.read() != ""
        if not is_ok:
            with open(r"resource/credentials/gcreds.json", "w+") as gcreds_file:
                gcreds_file.write(os.environ["gcreds"][:-1] + "," + os.environ["gcreds_private_key"] + "}")
        client = gspread.service_account(filename="resource/credentials/gcreds.json")

        # TODO: Use name instead of ID
        self.sheet = client.open_by_key(sheet_id).worksheets()[0]


class AvatarHistory(Sheet):
    def __init__(self, bot: Bot, sheet_id: str):
        super(AvatarHistory, self).__init__(sheet_id)
        self.bot = bot

    def update(self):
        nothing_row = []
        nothing_row.extend(num - len(nothing_row) + 1 for num, row in enumerate(self.sheet.col_values(1)) if row == "")

        for row in nothing_row:
            self.sheet.delete_row(row)

        for user in self.bot.users:
            user_id = str(user.id)
            col1 = self.sheet.col_values(1)
            if user_id not in col1:  # si l'utilisateur n'existe pas
                self.sheet.insert_row(
                    [user_id, str(user), user.display_avatar.url, upload_image_on_imgur(url=user.display_avatar.url)],
                    len(col1) + 1)  # créé l'utilisateur
            else:
                user_row = col1.index(user_id) + 1
                user_names = self.sheet.cell(user_row, 2).value

                if str(user) not in user_names.split(" + "):  # si le nom a changé
                    self.sheet.update_cell(user_row, 2, f"{user_names} + {user}")  # mettre le nouveau nom

                if user.display_avatar.url != self.sheet.cell(user_row, 3).value:  # si l'avatar a changé
                    self.sheet.update_cell(user_row, len(self.sheet.row_values(user_row)) + 1,
                                           upload_image_on_imgur(url=user.display_avatar.url))
                    self.sheet.update_cell(user_row, 3, user.display_avatar.url)


class SaveMsgs(Sheet):
    def __init__(self, sheet_id: str, bot: Bot):
        super(SaveMsgs, self).__init__(sheet_id)
        self.bot = bot

    def add(self, to_save: list):
        to_save = [to_save[0].channel.id] + [msg.id for msg in to_save]
        self.sheet.insert_row(list(map(str, to_save)), 1)

    def add_to_delete(self, msg):
        to_save = [msg.channel.id, msg.id, "To Delete"]
        self.sheet.insert_row(list(map(str, to_save)), 1)

    def remove(self, to_remove=None, msg=None):
        if to_remove is None:
            to_remove = []
        all_values = self.sheet.get_all_values()
        if msg:
            to_remove = [msg.channel.id, msg.id, "To Delete"]
        else:
            to_remove = [to_remove[0].channel.id] + [msg.id for msg in to_remove]
        to_remove += [""] * (len(all_values[0]) - len(to_remove))
        self.sheet.delete_row(all_values.index(list(map(str, to_remove))) + 1)

    async def get(self):
        values = []
        delete_row = 0
        for row_number, row in enumerate(self.sheet.get_all_values(), start=1):
            if not row[0]:
                self.sheet.delete_row(row_number - delete_row)
                delete_row += 1
                continue
            channel = await self.bot.fetch_channel(row[0])
            msgs = []
            error = False
            for ID in row[1:]:  # tout sauf le premier, car c'est l'ID du channel
                if ID == "To Delete":
                    error = True
                    continue
                try:
                    if ID:
                        msgs.append(await channel.fetch_message(ID))
                except NotFound:
                    error = True
            if error:
                self.sheet.delete_row(row_number - delete_row)
                delete_row += 1
                for msg in msgs:
                    if str(msgs[0].channel.type) != "private" or msg.author == self.bot.user:
                        await msg.delete()
            else:
                values.append(msgs)
        return {element[0].id: element for element in values if element}


class Statistics(Sheet):
    def __init__(self, sheet_id: str):
        super(Statistics, self).__init__(sheet_id)

    def command_used(self, command_name: str):
        col = self.sheet.col_values(1)
        if command_name in col:
            self.sheet.update_cell(col.index(command_name) + 1, 2,
                                   int(self.sheet.cell(col.index(command_name) + 1, 2).value) + 1)
        else:
            self.sheet.update_cell(len(col) + 1, 1, command_name)
            self.sheet.update_cell(len(col) + 1, 2, 1)

    def user_use_command(self, user_name: str):
        col = self.sheet.col_values(4)
        if user_name in col:
            self.sheet.update_cell(col.index(user_name) + 1, 5,
                                   int(self.sheet.cell(col.index(user_name) + 1, 5).value) + 1)
        else:
            self.sheet.update_cell(len(col) + 1, 4, user_name)
            self.sheet.update_cell(len(col) + 1, 5, 1)

    def add(self, user_name: str, command_name: str):
        self.user_use_command(user_name)
        self.command_used(command_name)


class EventsDate(Sheet):
    def add(self, date, event_type, activity_name):
        to_save = [date, event_type, activity_name]
        col = self.sheet.col_values(1)
        if date in col:
            row = col.index(date) + 1
            self.sheet.update_cell(row, 2, event_type)
            self.sheet.update_cell(row, 3, activity_name)
        else:
            self.sheet.insert_row(to_save, 1)

    def remove(self, to_remove: list):
        self.sheet.delete_row(self.sheet.get_all_values().index(to_remove) + 1)

    async def get(self):
        values = self.sheet.get_all_values()
        return {element[0]: element[1:] for element in values}
