from discord.ext import commands
from discord import File
from datetime import date
import os
admin_role = 'Bot Admin'

async def data_backup(backup_channel):
    date_str = date.today().strftime('%Y-%m-%d')
    with open('./data/time.json', "rb") as f:
        await backup_channel.send(file=File(f, f"time_{date_str}.json"))
    with open('./data/vampyre.db', "rb") as f:
        await backup_channel.send(file=File(f, f"vampyre_{date_str}.db"))

class Transfer(commands.Cog, name = 'Importar y Exportar'):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True)
    async def export(self, ctx):
        pass
            
    @export.command(name = 'channel')
    @commands.has_role(admin_role)
    async def export_channel(self, ctx, channel):
        """
        Exporta el contenido completo de un canal como fichero de texto.
        """
        channel = self.bot.get_channel(int(channel[2:-1]))
        messages = await channel.history().flatten()
        messages = "\n\n".join([m.content.replace("\n** **","") for m in messages[::-1]])
        filename = f"{channel.name}_{date.today().strftime('%Y-%m-%d')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(messages)
            
        with open(filename, "rb") as f:
            await ctx.send(f"Contenido del canal <#{channel.id}>:", file=File(f, filename))
            
        os.remove(filename)


    @export.command(name = 'database', aliases = ['db'])
    @commands.has_role(admin_role)
    async def export_database(self, ctx, channel=None):
        if channel is not None:
            channel = self.bot.get_channel(int(channel[2:-1]))
        else:
            channel = ctx.channel
        await data_backup(channel)
        