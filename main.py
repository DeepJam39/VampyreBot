import os
import discord
from discord.ext import commands

from better_help import Help

from cogs.data import Data
from cogs.shortcuts import Shortcuts
from cogs.transfer import Transfer
from cogs.chance import Chance
from cogs.time import Time

import cogs.orm.database_connection as db

from keep_alive import keep_alive

token = os.getenv('DISCORD_TOKEN_VAMPYRE')

db.load_db()

class Bot(commands.Bot):
    async def process_commands(self, message):
        ctx = await self.get_context(message)
        await self.invoke(ctx)

description = "I exist to make your unlife easier."
bot = Bot(command_prefix=commands.when_mentioned_or('vp!','Vp!'), 
          description=description,
          help_command=Help())
ButtonsMenu.initialize(bot)

admin_role = 'Bot Admin'    
            
@bot.event
async def on_ready():
    print(':) Hola.')
    print('Conectado como:')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)

bot.add_cog(Data(bot))
bot.add_cog(Shortcuts(bot))
bot.add_cog(Transfer(bot))
bot.add_cog(Chance(bot))
bot.add_cog(Time(bot))

keep_alive()
bot.run(token)