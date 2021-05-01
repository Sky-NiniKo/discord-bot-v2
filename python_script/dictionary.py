def format_definition(word, pronunciation=None, classe=None, other=None, definitions=None):
    if definitions is None:
        definitions = []
    to_return = f"**{word}**"
    if pronunciation is not None:
        to_return += f" [{pronunciation}]"
    if classe is not None:
        to_return += f" {classe}"
    if other is not None:
        to_return += f" {other}"
    for num, definition in enumerate(definitions, start=1):
        to_return += f"\n{num}. {definition}"
    return to_return


class Dictionary:
    def __init__(self):
        self.word_list = ("natan",)

    async def search(self, ctx):
        if ctx.message.content.startswith(self.word_list[0]):
            await ctx.send(format_definition("natan", "natã", "n.p.", "(du lat. *natus*, branleur)",
                                             ("Personne qui n'est pas dotée d'une trés grande intelligence (syn. con)",
                                              "Personne ayant un amour incommensurable envers les animés (syn. weeb)")))
