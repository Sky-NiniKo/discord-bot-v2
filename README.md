[![Codacy Badge](https://app.codacy.com/project/badge/Grade/7b33e2d1ccea4737a380004eea247b04)](https://www.codacy.com/gh/Sky-NiniKo/discord-bot-v2/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Sky-NiniKo/discord-bot-v2&amp;utm_campaign=Badge_Grade)
![License](https://img.shields.io/github/license/Sky-NiniKo/discord-bot-v2)
![Code size in bytes](https://img.shields.io/github/languages/code-size/Sky-NiniKo/discord-bot-v2)
![Repo size](https://img.shields.io/github/repo-size/Sky-NiniKo/discord-bot-v2)
![Lines of code](https://img.shields.io/tokei/lines/github/Sky-NiniKo/discord-bot-v2)
![Last commit](https://img.shields.io/github/last-commit/Sky-NiniKo/discord-bot-v2)
# Run at home (only Windows and Linux are supported)
First install all python dependencies of Pipfile.lock and if you are on Linux install all packages in Aptfile with apt.

In the `resource` folder open `credentials` folder and put 2 files in it, `.env` and `gcreds.json` that you get from this tutorial https://www.youtube.com/watch?v=cnPlKLEGR7E&t=32s.
## .env
Fill .env like this (the information with an * are essential to start the program and the one with a ¤ are essential to have all the functionalities of the bot and not to have any error)
```ini
[Discord Bot]
DISCORD_BOT_TOKEN = <*Your discord bot token>
OWNER = <Your discord account ID>

IMGUR_CLIENT_ID = <¤Imgur API: CLIENT_ID>

SHEET_AVATAR_HISTORY = <*Google Sheet ID>
SHEET_SAVE_MSGS = <*Google Sheet ID>
SHEET_STATISTICS = <*Google Sheet ID>
SHEET_EVENT_DATE = <*Google Sheet ID>
```
Where to find this information?

Discord account ID: https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-

Imgur API: https://api.imgur.com/#registerapp

Google Sheet ID: In a typical Google Sheet URL → https://docs.google.com/spreadsheets/d/ (Is it here) /
## Start
If you are on Windows launch main.py and if you are on Linux launch start.sh

## Difficulties or you want more information
Open an issue https://github.com/Sky-NiniKo/discord-bot-v2/issues/new/choose
