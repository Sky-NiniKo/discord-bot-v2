import json
import random
import platform
import multiprocessing
from itertools import chain, groupby
from pathlib import Path

import chess
import chess.svg
import chess.engine
import discord
import requests
from discord.ext.commands import Bot, Context

from .reaction import QuickDelete
from .utils import generate_implicit, multiple_replace

english_pieces = ("K", "Q", "R", "B", "N")
french_pieces = ("R", "D", "T", "F", "C")
unicode_black_pieces = ("♚", "♛", "♜", "♝", "♞")
unicode_white_pieces = ("♔", "♕", "♖", "♗", "♘")


def diagonals_pos(matrix, cols, rows):
    """Get positive diagonals, going from bottom-left to top-right."""
    for di in ([(j, i - j) for j in range(cols)] for i in range(cols + rows - 1)):
        yield [matrix[i][j] for i, j in di if 0 <= i < cols and 0 <= j < rows]


def diagonals_neg(matrix, cols, rows):
    """Get negative diagonals, going from top-left to bottom-right."""
    for di in ([(j, i - cols + j + 1) for j in range(cols)] for i in range(cols + rows - 1)):
        yield [matrix[i][j] for i, j in di if 0 <= i < cols and 0 <= j < rows]


class Game:
    def __init__(self, channel, ctx: Context, bot: Bot, quick_delete: QuickDelete, game_template=None,
                 replay_separation=""):
        if game_template is None:
            game_template = {}
        self.bot = bot
        self.channel = channel
        self.msg = ctx.message
        self.players = [ctx.author] + ctx.message.mentions
        self.start = False
        self.stop = False
        self.replay = []
        self.replay_separation = replay_separation
        self.game_template = game_template
        self.quick_delete = quick_delete

    async def __init_async__(self):
        await self.quick_delete.wait_for_ok()
        self.quick_delete.save.add_to_delete(self.msg)

    async def super_message(self, first_arg):
        if first_arg in generate_implicit(("close", "quit", "exit")):
            await self.channel.delete()
            self.quick_delete.save.remove(msg=self.msg)
            await self.msg.delete()
            del self.game_template[self.channel]
            return True
        elif first_arg in generate_implicit(("replay", "save")):
            await self.channel.send(f"Voici le replay :\n{self.replay_separation.join(self.replay)}"
                                    f"\nAttention, on ne peut pas relire le replay pour l'instant")
            return True

    async def reaction(self, payload):
        return


class Connect4(Game):
    def __init__(self, channel, ctx: Context, bot: Bot, quick_delete: QuickDelete, game_template, cols=7, rows=6,
                 required_to_win=4):
        super(Connect4, self).__init__(channel, ctx, bot, quick_delete, game_template)
        self.NONE = ":white_circle:"
        self.player_color = ["🔴", "🟡", "🟢", "🔵", "🟣", "🟤", "⚪"]  # rouge, jaune, vert, bleu, violet, marron, blanc
        self.players = self.players[:len(self.player_color)]
        if bot.user in self.players:
            self.players = self.players[:2]
            self.cols = 7
            self.rows = 6
            self.is_bot = True
        else:
            self.cols = cols
            self.rows = rows
            self.is_bot = False
        self.board = [[self.NONE] * rows for _ in range(cols)]
        self.win = required_to_win
        self.player = -1
        self.numbers = tuple(f'{str(x)}⃣' for x in range(1, 10))
        self.last_msg = None

    async def info(self):
        players_name = ", ".join(player.name for player in self.players[:-1]) + " et " + self.players[-1].name
        if self.is_bot:
            await self.channel.send(
                f"Vous jouez avec {players_name}.\nBienvenue dans le puissance 4.\n\nSi vous voulez commencer faite "
                f"`start`\nSi vous voulez qu'un joueur en particulier commence faite `first @(joueur)`\n"
                f"Si vous voulez personnaliser votre colour faite `emoji (emoji)`\n" + "\\_" * 50)
        else:
            await self.channel.send(
                f"Vous jouez avec {players_name}.\nBienvenue dans le puissance 4.\n\nSi vous voulez commencer faite "
                f"`start`\nSi vous voulez changer la taille du puissance 4 faite `size (longueur)*(largeur)`\n"
                f"Si vous voulez qu'un joueur en particulier commence faite `first @(joueur)`\n"
                f"Si vous voulez faire plus qu'un puissance 4 par exemple un puissance 5 il faut faire `for_win 5`\n"
                f"Si vous voulez personnaliser votre colour faite `emoji (emoji)`\n" + "\\_" * 50)

    async def end_turn(self):
        """Show the board."""
        self.player = self.player + 1 if self.player < len(self.players) - 1 else 0
        to_show = "".join(self.numbers[:self.cols]) + "\n"
        for y in range(self.rows):
            to_show += ''.join(str(self.board[x][y]) for x in range(self.cols)) + "\n"
        embed = discord.Embed(title=f"C'est à {self.players[self.player].name}", description=to_show)
        self.last_msg = await self.channel.send(embed=embed)
        if self.players[self.player] == self.bot.user:
            request = requests.get("https://connect4.gamesolver.org/solve", params=(("pos", "".join(self.replay)),),
                                   headers={"User-Agent": ""})
            values = json.loads(request.text)["score"]
            values = [-100 if value == 100 else value for value in values]
            await self.play(max(zip(values, range(len(values))))[1])
        else:
            for col, number in enumerate(self.numbers[:self.cols]):
                if self.board[col][0] == self.NONE:
                    await self.last_msg.add_reaction(number)

    async def reaction(self, payload):
        user = self.bot.get_user(payload.user_id)
        if user == self.players[self.player]:
            if self.last_msg is not None:
                await self.last_msg.clear_reactions()
            await self.play(int(payload.emoji.name[0]) - 1)

    async def play(self, column: int, color: str = None):
        if color is None:
            color = self.player_color[self.player]
        continue_ = await self.insert(column, color)
        if continue_:  # continue_ is true if the player doesn't win
            await self.end_turn()

    async def insert(self, column, color):
        """Insert the color in the given column."""
        self.replay.append(str(column + 1))

        c = self.board[column]

        i = -1
        while c[i] != self.NONE:
            i -= 1
        c[i] = color

        return await self.check_for_win()

    async def check_for_win(self):
        """Check the current board for a winner."""
        w = self.get_winner()
        if w:
            to_show = "\\_" * 50 + "\n"
            to_show += "".join(self.numbers[:self.cols]) + "\n"
            for y in range(self.rows):
                to_show += ''.join(str(self.board[x][y]) for x in range(self.cols)) + "\n"
            to_show += f"{self.players[self.player].name} à gagner !"
            await self.channel.send(to_show)
            await self.channel.send(":tada:")
            await self.channel.send("Maintenant vous pouvez quitter avec `quit`\n" + "\\_" * 50)
        return not w

    def get_winner(self):
        """Get the winner on the current board."""
        lines = (
            self.board,  # columns
            zip(*self.board),  # rows
            diagonals_pos(self.board, self.cols, self.rows),  # positive diagonals
            diagonals_neg(self.board, self.cols, self.rows)  # negative diagonals
        )

        for line in chain(*lines):
            for color, group in groupby(line):
                if color != self.NONE and len(list(group)) >= self.win:
                    return color

    async def size(self, arg):
        try:
            cols, rows = [int(x) for x in arg.split("*")]
            if cols > 9 or rows > 15:
                await self.channel.send("Tu peux aller jusqu'à 9 colones et 15 lignes")
            else:
                self.cols, self.rows = cols, rows
                self.board = [[self.NONE] * self.rows for _ in range(self.cols)]
                self.win = min(self.cols, self.rows) if self.win >= max(self.cols, self.rows) else self.win
                await self.channel.send(f"Le puissance 4 fait maintenant {self.cols}*{self.rows}")
        except ValueError:
            await self.channel.send("Désolé mais les arguments sont invalides.\nFaite `size (colones)*(lignes)`")

    async def message(self, ctx: Context):
        first_arg = ctx.message.content.split()[0].lower()
        await super(Connect4, self).super_message(first_arg)
        if not self.start:
            if first_arg in generate_implicit(("start",)):
                self.start = True
                self.player = random.randint(0, len(self.players) - 1) if self.player == -1 else self.player
                await self.channel.send("\\_" * 50)
                await self.end_turn()
            elif first_arg in generate_implicit(("size", "taille")) and not self.is_bot:
                await self.size(ctx.message.content.split()[1])
            elif first_arg in generate_implicit(("premier", "first")):
                try:
                    self.player = self.players.index(
                        (ctx.message.mentions[0])) - 1  # -1, car ça fait +1 dès le démarrage

                    if self.player == -1:
                        self.player = len(self.players) - 1
                        await self.channel.send(f"{self.players[0].name} commencera.")
                    else:
                        await self.channel.send(f"{self.players[self.player + 1].name} commencera.")
                except ValueError:
                    await self.channel.send("Tu n'a mentionné personne")
            elif first_arg in generate_implicit(("for_win",)) and not self.is_bot:
                if ctx.message.content.split()[1].isdigit():
                    arg = int(ctx.message.content.split()[1])
                    if self.cols >= arg or self.rows >= arg:
                        self.win = arg
                        await self.channel.send(f"Il faudra maintenant aligné {arg} pièce pour gagner.")
                    else:
                        await self.channel.send("Ce nombre est trop grand pour la taille de ton puissance 4")
                else:
                    await self.channel.send("Tu dois indiquer un nombre")
            elif first_arg in generate_implicit(("emoji",)):
                emoji = ctx.message.content.split()[1]
                self.player_color[self.players.index(ctx.author)] = emoji
                await self.channel.send(f"La pièce de {ctx.author.name} sere maintenant ceci : {emoji}")


class Chess(Game):
    def __init__(self, channel, ctx: Context, bot: Bot, quick_delete: QuickDelete, game_template):
        super(Chess, self).__init__(channel, ctx, bot, quick_delete, game_template, replay_separation="|")
        self.chess_games_number = sum(map(lambda value: isinstance(value, Chess),
                                          self.game_template.values())) + 1  # Il ne se compte pas lui-même donc +1, mais je ne suis pas sûr
        if self.chess_games_number >= 256:
            raise BufferError("Too many game in same time this can cause performance issue")
        self.first_player = ""
        self.player = -1
        self.show_analyse = False
        self.players = self.players[:2]
        self.board = chess.Board()
        self.draw = {player: False for player in self.players}
        self.last_move = chess.Move.null()
        self.engine = chess.engine.UciProtocol()
        self.transport = None
        self.path = Path(__file__).parent.parent

    async def info(self):
        path = self.path / "resource/chess engines/" / (
            "stockfish_15_x64_popcnt.exe"
            if "Windows" in platform.platform()
            else "stockfish_15_x64_popcnt"
        )

        self.transport, self.engine = await chess.engine.popen_uci(path.as_posix())

        hash_size = 256 // self.chess_games_number
        for game in self.game_template.values():
            if isinstance(game, Chess):
                await game.update_hash(hash_size)
        await self.engine.configure({"Threads": multiprocessing.cpu_count()})

        players_name = ", ".join(map(lambda player: player.name, self.players[:-1])) + " et " + self.players[-1].name
        await self.channel.send(
            f"Vous jouez avec {players_name}.\nBienvenue dans le jeux d'échecs.\n\nSi vous voulez commencer faite "
            f"`start`\nSi vous voulez qu'un joueur en particulier commence faite `first @(joueur)`\n"
            f"Si vous voulez avoir un indication sur les chances que quelqu'un gagne faite `chance`\n\n"
            f"Pour déplacer les pièces écrivez un movement en Notation algébrique abrégée française, anglaise ou "
            f"figurine (<https://fr.wikipedia.org/wiki/Notation_algébrique#Notation_algébrique_abrégée>) "
            f"ou en écrivant simplement les cases. Exemple : e2e4\n{''.join(unicode_white_pieces)}\n" + "\\_" * 50)

    async def send_board(self, msg=""):
        import cairosvg
        if self.board.is_check():
            svg_board = chess.svg.board(self.board, orientation=self.board.turn, lastmove=self.last_move,
                                        check=self.board.king(self.board.turn), size=500)
        else:
            svg_board = chess.svg.board(self.board, orientation=self.board.turn, lastmove=self.last_move, size=500)
        cairosvg.svg2png(bytestring=svg_board, write_to=self.path / "resource/temp/chess board.png")

        await self.channel.send(msg, file=discord.File(self.path / "resource/temp/chess board.png"))

    async def stop_game(self):
        await self.engine.quit()
        self.stop = True

    async def resigns(self):
        to_send = f"{self.players[self.player].name} à abandonner.\n"
        self.player = self.player + 1 if self.player < len(self.players) - 1 else 0
        to_send += f"{self.players[self.player].name} à gagner par forfait."
        await self.channel.send(to_send)
        await self.stop_game()

    async def end_turn(self, first_turn=False):
        if not first_turn:
            self.player = self.player + 1 if self.player < len(self.players) - 1 else 0
        self.draw = {player: False for player in self.players}
        await self.send_board(f"C'est à {self.players[self.player].mention}")

        if self.show_analyse:
            analyse = await self.engine.analyse(self.board, chess.engine.Limit(time=0.1))
            score = analyse["score"].white()
            if isinstance(score, chess.engine.Cp):
                pawn = int(str(score)) / 100
                await self.channel.send(f'{"+" * (pawn > 0)}{pawn} centipawn pour les blancs.')
            else:
                mate = score.mate()
                color = "blancs" if mate > 0 else "noirs"
                await self.channel.send(f"Mate en {abs(mate)} coups pour les {color}.")

        if self.players[self.player] == self.bot.user:
            response = requests.get(
                f"https://tablebase.lichess.ovh/standard?fen={self.board.fen()}")  # permet de conclure en fin de partie
            response = json.loads(str(response.content, encoding=response.apparent_encoding))
            if any((response['wdl'], response['dtz'], response['dtm'])):
                if any(map(lambda x: x < 0, (response['wdl'], response['dtz'], response['dtm']))):
                    await self.resigns()
                    return
                move = self.board.parse_uci(response['moves'][0]['uci'])
                await self.verify(move)

            analyse = await self.engine.analyse(self.board, chess.engine.Limit(depth=15))
            score = analyse["score"].white() if self.bot.user == self.first_player else analyse["score"].black()
            if isinstance(score, chess.engine.Mate) and score.wdl().expectation() == 0:
                await self.resigns()
                return
            result = await self.engine.play(self.board, chess.engine.Limit(depth=15))
            self.board.push(result.move)
            await self.verify(result.move)

    async def verify(self, move: chess.Move):
        self.replay.append(str(move))
        self.last_move = move
        if not self.board.is_game_over():
            await self.end_turn()
        else:
            await self.send_board()
            if self.board.is_checkmate():
                await self.channel.send(f"{self.players[self.player]} à gagner.")
            else:
                await self.channel.send("Match nul.")
            await self.stop_game()

    async def message(self, ctx: Context):
        msg = ctx.message.content
        first_arg = msg.split()[0].lower()
        if await super(Chess, self).super_message(first_arg):
            return
        if not self.start:
            if first_arg in generate_implicit(("start",)):
                self.player = random.randint(0, len(self.players) - 1) if self.player == -1 else self.player
                self.first_player = self.players[self.player]
                self.start = True
                await self.end_turn(first_turn=True)
            elif first_arg in generate_implicit(("first", "premier")):
                try:
                    self.player = self.players.index((ctx.message.mentions[0])) - 1
                    await self.channel.send(f"{self.players[self.player].name} commencera.")
                except ValueError:
                    await self.channel.send("Tu n'a mentionné personne")
            elif first_arg in generate_implicit(("chance", "analyse", "chances")):
                await self.channel.send(
                    f"Les chances de gagner {'ne ' * self.show_analyse}seront {'pas ' * self.show_analyse}afficher.\n"
                    f"Vous pouvez inverser cela en refaisant `chance`")
                self.show_analyse = not self.show_analyse
        elif not self.stop:
            if first_arg in generate_implicit(("nul", "=")):
                if all(self.draw.values()):
                    await self.channel.send("Les joueurs se sont mis d'accord sur un match nul.")
                    await self.stop_game()
                self.draw[ctx.message.author] = not self.draw[ctx.message.author]
                cancel = not self.draw[ctx.message.author]
                await self.channel.send(
                    f"{ctx.author.name} à {'demander un' * self.draw[ctx.message.author]}{'annuler son' * cancel} nul.")
                if self.draw[ctx.message.author] and not self.draw[self.bot.user]:
                    await self.engine_accept_draw()
            elif msg in generate_implicit(("non nul", "pas nul")):
                self.draw = {player: False for player in self.players}
            elif first_arg in generate_implicit(("forfait", "abandon")):
                await self.resigns()
            else:
                try:
                    try:
                        move = self.board.push_san(
                            multiple_replace(multiple_replace(msg, unicode_black_pieces, english_pieces),
                                             unicode_white_pieces, english_pieces))
                    except ValueError:
                        try:
                            move = self.board.push_san(multiple_replace(msg, french_pieces, english_pieces))
                        except ValueError:
                            try:
                                move = self.board.push_san(msg)
                            except ValueError:
                                move = self.board.push_uci(msg)
                    await self.verify(move)
                except ValueError:
                    await self.channel.send("Mouvement invalide.")

    async def engine_accept_draw(self):
        analyse = await self.engine.analyse(self.board, chess.engine.Limit(depth=15))
        score = analyse["score"].white().wdl().expectation()
        score = score if self.bot.user == self.first_player else 1 - score
        if score - min(len(self.replay) * 0.01, 0.2) < 0.4:
            self.draw[self.bot.user] = True
            await self.channel.send(f"{self.bot.user.name} à accepter le nul.")
            if all(self.draw):
                await self.channel.send("Les joueurs se sont mis d'accord sur un match nul.")
                await self.stop_game()
        else:
            await self.channel.send(f"{self.bot.user.name} à refuser le nul.")
            self.draw = {player: False for player in self.players}

    async def update_hash(self, size):
        await self.engine.configure({"Hash": size})


class GameEngine:
    def __init__(self, bot: Bot, quick_delete: QuickDelete):
        self.bot = bot
        self.games = {}
        self.game_template = {}
        self.quick_delete = quick_delete

    async def update_game_template(self):
        first_start = self.game_template == {}

        for guild in self.bot.guilds:
            for channel in guild.channels:
                if str(channel) in {"template", "game", "games", "modèle"}:
                    self.game_template[guild] = channel
                if first_start and "game-" in str(channel):
                    await channel.delete()

    async def create_game(self, ctx: Context):
        channel = await self.game_template[ctx.guild].clone(name=f"game-{len(self.games) + 1}")
        await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
        for mention in ctx.message.mentions:
            await channel.set_permissions(mention, read_messages=True, send_messages=True)
        return channel

    async def connect_4(self, ctx: Context):
        try:
            channel = await self.create_game(ctx)
            self.games[channel] = Connect4(channel, ctx, self.bot, self.quick_delete, self.games)
            await self.games[channel].info()
        except KeyError:
            await ctx.send("Ce serveur ne supporte pas cette fonctionnalité")

    async def chess(self, ctx: Context):
        try:
            channel = await self.create_game(ctx)
            self.games[channel] = Chess(channel, ctx, self.bot, self.quick_delete, self.games)
            self.bot.loop.create_task(self.games[channel].__init_async__())
            await self.games[channel].info()
        except KeyError:
            await ctx.send("Ce serveur ne supporte pas cette fonctionnalité")
        except BufferError:
            await ctx.send("Trop de gens joue aux échecs, "
                           "le bot ne peut pas lancer d'autre partie pour des raisons de performance")

    async def reaction(self, payload):
        channel = await self.bot.fetch_channel(payload.channel_id)
        await self.games[channel].reaction(payload)

    async def message(self, ctx: Context):
        try:
            await self.games[ctx.channel].message(ctx)
        except OSError:
            await ctx.send("Le convertisseur de .svg en .png ne marche pas, cela rend impossible l'affichage "
                           "d'un plateau d'échecs.\nRéessayer un autre jours ou demander à mon créateur.")
