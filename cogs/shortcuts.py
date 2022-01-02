from discord.ext import commands
from .data import blood_delta, wp_delta, pwp_delta, hp_delta, agg_delta
admin_role = 'Bot Admin'
class Shortcuts(commands.Cog, name = 'Atajos'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['g', 'give'])
    @commands.has_role(admin_role)
    async def giveitem(self, ctx, item:str, amount:int, character:str):
		"""
		Da determinada cantidad de un objeto a un personaje dado, usando a RPGBot.
		"""
        await ctx.send(f"rp!giveitem {item} {amount} {character}", delete_after=10)

    @commands.command(aliases=['gb'])
    @commands.has_role(admin_role)
    async def giveblood(self, ctx, amount:int, character:str):
		"""
		Da determinada cantidad de puntos de sangre a un personaje dado.
		"""
        await ctx.send(blood_delta(character, amount))

    @commands.command(aliases=['gx', 'gxp'])
    @commands.has_role(admin_role)
    async def givexp(self, ctx, amount:int, character:str):
		"""
		Da determinada cantidad de puntos de experiencia a un personaje dado, usando a RPGBot.
		"""
        item = "Puntos-de-Experiencia"
        await self.giveitem(ctx, item, amount, character)

    @commands.command(aliases=['gw', 'gwp', 'gfv'])
    @commands.has_role(admin_role)
    async def givewp(self, ctx, amount:int, character:str):
		"""
		Da determinada cantidad de puntos de fuerza de voluntad (temporales) a un personaje dado.
		"""
        await ctx.send(wp_delta(character, amount))

    @commands.command(aliases=['gpw', 'gpwp', 'gpfv'])
    @commands.has_role(admin_role)
    async def givepwp(self, ctx, amount:int, character:str):
		"""
		Da determinada cantidad de puntos de fuerza de voluntad (permanentes) a un personaje dado.
		"""
        await ctx.send(pwp_delta(character, amount))

    @commands.command(aliases=['ghp', 'gh'])
    @commands.has_role(admin_role)
    async def givehp(self, ctx, amount:int, character:str):
		"""
		Da determinada cantidad de puntos de vida a un personaje dado.
		"""
        await ctx.send(hp_delta(character, amount))

    @commands.command(aliases=['ga', 'gagg'])
    @commands.has_role(admin_role)
    async def giveagg(self, ctx, amount:int, character:str):
		"""
		Da determinada cantidad de niveles de daño agravado a un personaje dado.
		"""
        await ctx.send(agg_delta(character, amount))
        await ctx.send(hp_delta(character, -3*amount))
        
    @commands.command(aliases=['gl', 'gleth'])
    @commands.has_role(admin_role)
    async def giveleth(self, ctx, amount:int, character:str):
		"""
		Da determinada cantidad de niveles de daño letal a un personaje dado.
		"""
        await ctx.send(leth_delta(character, amount))
        await ctx.send(hp_delta(character, -2*amount))

    @commands.command(aliases=['t', 'take'])
    @commands.has_role(admin_role)
    async def takeitem(self, ctx, item:str, amount:int, character:str):
		"""
		Elimina determinada cantidad de un objeto a un personaje dado, usando a RPGBot.
		"""
        await ctx.send(f"rp!takeitem {item} {amount} {character}", delete_after=10)

    @commands.command(aliases=['tb'])
    @commands.has_role(admin_role)
    async def takeblood(self, ctx, amount:int, character:str):
		"""
		Elimina determinada cantidad de puntos de sangre de un personaje dado.
		"""
        await ctx.send(blood_delta(character, -amount))

    @commands.command(aliases=['tx', 'txp'])
    @commands.has_role(admin_role)
    async def takexp(self, ctx, amount:int, character:str):
		"""
		Elimina determinada cantidad de puntos de experiencia de un personaje dado, usando a RPGBot.
		"""
        item = "Puntos-de-Experiencia"
        await self.takeitem(ctx, item, amount, character)

    @commands.command(aliases=['tw', 'twp', 'tfv'])
    @commands.has_role(admin_role)
    async def takewp(self, ctx, amount:int, character:str):
		"""
		Elimina determinada cantidad de puntos de fuerza de voluntad (temporales) de un personaje dado.
		"""
        await ctx.send(wp_delta(character, -amount))

    @commands.command(aliases=['tpw', 'tpwp', 'tpfv'])
    @commands.has_role(admin_role)
    async def takepwp(self, ctx, amount:int, character:str):
		"""
		Elimina determinada cantidad de puntos de fuerza de voluntad (permanentes) de un personaje dado.
		"""
        await ctx.send(pwp_delta(character, -amount))

    @commands.command(aliases=['thp', 'th'])
    @commands.has_role(admin_role)
    async def takehp(self, ctx, amount:int, character:str):
		"""
		Elimina determinada cantidad de puntos de vida de un personaje dado.
		"""
        await ctx.send(hp_delta(character, -amount))

    @commands.command(aliases=['ta', 'tagg'])
    @commands.has_role(admin_role)
    async def takeagg(self, ctx, amount:int, character:str):
		"""
		Elimina determinada cantidad de niveles de daño agravado de un personaje dado.
		"""
        await ctx.send(agg_delta(character, -amount))
        await ctx.send(hp_delta(character, 3*amount))
        
    @commands.command(aliases=['tl', 'tleth'])
    @commands.has_role(admin_role)
    async def takeleth(self, ctx, amount:int, character:str):
		"""
		Elimina determinada cantidad de niveles de daño letal de un personaje dado.
		"""
        await ctx.send(leth_delta(character, -amount))
        await ctx.send(hp_delta(character, 2*amount))