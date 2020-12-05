
from discord.ext import commands

from utils.music_player import MusicPlayer

bot = commands.Bot(command_prefix="!", case_insensitive=True)


@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')


bot.add_cog(MusicPlayer(bot))
bot.run("NzgyNjMyMDY2OTE0OTc1Nzk0.X8PA6Q.cFl3SQ7l4B4tuo873hJEgqO7sFA")
