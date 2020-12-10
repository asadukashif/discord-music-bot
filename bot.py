import os

import dotenv
from discord.ext import commands

from utils.music_player import MusicPlayer

dotenv.load_dotenv(".env")
bot = commands.Bot(command_prefix=["~"], case_insensitive=True)


@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')


bot.add_cog(MusicPlayer(bot))
bot.run(os.getenv('DISCORD_KEY'))
