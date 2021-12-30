from discord.ext import commands
from discord import File
from datetime import date
import os
admin_role = 'Bot Admin'
class Transfer(commands.Cog, name = 'Importar y Exportar'):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True)
    async def export(self, ctx):
        pass
            
    @export.command(name = 'channel')
    @commands.has_role(admin_role)
    async def export_channel(self, ctx, channel):
        channel = self.bot.get_channel(int(channel[2:-1]))
        messages = await channel.history().flatten()
        messages = "\n\n".join([m.content.replace("\n** **","") for m in messages[::-1]])
        filename = f"{channel.name}_{date.today().strftime('%Y-%m-%d')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(messages)
            
        with open(filename, "rb") as f:
            await ctx.send(f"Contenido del canal <#{channel.id}>:", file=File(f, filename))
            
        os.remove(filename)