import _thread
import asyncio
from datetime import date

from python_script.activity import Activity
from python_script.sheet import AvatarHistory
from python_script.game import GameEngine


class EverydayTask:
    def __init__(self, avatar_history: AvatarHistory, game: GameEngine, activity: Activity):
        self.avatar_history = avatar_history
        self.game = game
        self.activity = activity

    async def start(self):
        while True:
            print("Mise à jours des game_template et changement des activités\n")
            await self.game.update_game_template()
            await self.activity.change()

            day = date.today()
            while (date.today() - day).days < 1:  # attend un nouveau jour
                await asyncio.sleep(1)

            print("Mise à jours de l'historique des avatars")
            _thread.start_new_thread(self.avatar_history.update, ())
