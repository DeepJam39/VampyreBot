import discord
from discord.ext import commands, tasks

from datetime import datetime
import pytz
import json

from .data import apply_time_effects, is_admin

from reactionmenu import ButtonsMenu, ComponentsButton

admin_role = 'Bot Admin'

def load_time_data():
    with open('./data/time.json', 'r') as f:
        time_data = json.load(f)
    return time_data
    
def dump_time_data(time_data):
    with open('./data/time.json', 'w') as f:
        json.dump(time_data, f)
        
def dt_delta_str(dt):
    delta_str = ""
    difference = (dt - datetime.now()).total_seconds()
    minutes, seconds = divmod(difference, 60)
    if minutes <= 0:
        delta_str = "Actualización inminente"
    else:
        hours, minutes = divmod(minutes, 60)
        hours, minutes = int(hours), int(minutes)
        if hours > 0:
            delta_str += f"{hours} hora{'s' if hours>1 else ''}"
            if minutes > 0:
                delta_str += f" y {minutes} minuto{'s' if minutes>1 else ''}"
        else:
            delta_str += f"{minutes} minuto{'s' if minutes>1 else ''}"
    return delta_str
    
async def advance_date(bot):    
    time_data = load_time_data()
    time_data['day'] += 1
    dump_time_data(time_data)
    notifications_channel = bot.get_channel(time_data['notifications_channel'])
    await apply_time_effects(time_data['day'], notifications_channel)
    
def pause_updates():
    time_data = load_time_data()
    time_data['running'] = False
    dump_time_data(time_data)

def play_updates():
    time_data = load_time_data()
    time_data['running'] = True
    dump_time_data(time_data)
    
async def get_time_embed(owner_is_admin, bot):
    time_data = load_time_data()        
    time_embed = discord.Embed(title='Tiempo', colour=discord.Colour.blue())  
    buttons = []
    
    #time_embed.add_field(name="Día", value=f"{time_data['day']}", inline=False)
    day_of_month = time_data['day'] % 30
    if day_of_month == 30:
        day_of_month = 30  
    time_embed.add_field(name="Día del mes (aproximado)", value=f"{day_of_month}", inline=True)    

    if time_data['running']:
        time_embed.add_field(name="Paso automático del tiempo", value="Activado", inline=False)
        next_dt = datetime.fromtimestamp(time_data['next'])

        time_embed.add_field(name="Próxima actualización", value=f"{dt_delta_str(next_dt)}", inline=False)

        tz_format = lambda d, tz: d.astimezone(pytz.timezone(tz)).strftime("%d/%m/%Y, %H:%M")
        time_embed.add_field(name="Ciudad de México", value=f"{tz_format(next_dt, 'America/Mexico_City')}", inline=True)
        time_embed.add_field(name="La Habana", value=f"{tz_format(next_dt, 'Cuba')}", inline=True)
        time_embed.add_field(name="Caracas", value=f"{tz_format(next_dt, 'America/Caracas')}", inline=True)
        time_embed.add_field(name="Buenos Aires", value=f"{tz_format(next_dt, 'America/Buenos_Aires')}", inline=True)
        time_embed.add_field(name="Madrid", value=f"{tz_format(next_dt, 'Europe/Madrid')}", inline=True)
        
        if owner_is_admin:
            pause_followup = ComponentsButton.Followup()
            pause_followup.set_caller_details(pause_updates)
            buttons.append(ComponentsButton(style=ComponentsButton.style.grey, label='Desactivar actualizaciones',
                                     custom_id=ComponentsButton.ID_CALLER, followup=pause_followup))
    else:
        time_embed.add_field(name="Paso automático del tiempo", value="Desactivado", inline=False)
        if owner_is_admin:
            play_followup = ComponentsButton.Followup()
            play_followup.set_caller_details(play_updates)
            buttons.append(ComponentsButton(style=ComponentsButton.style.green, label='Activar actualizaciones',
                                     custom_id=ComponentsButton.ID_CALLER, followup=play_followup))
    
    if owner_is_admin:
        advance_followup = ComponentsButton.Followup()
        advance_followup.set_caller_details(advance_date, bot)
        buttons.append(ComponentsButton(style=ComponentsButton.style.green, label='Avanzar un día',
                                 custom_id=ComponentsButton.ID_CALLER, followup=advance_followup))
        
    buttons.append(ComponentsButton(style=ComponentsButton.style.primary, label='Cerrar',
                                  custom_id=ComponentsButton.ID_END_SESSION))
    return time_embed, buttons
    
    
async def time_refresh_buttons(menu):
    time_embed, buttons = await get_time_embed(is_admin(menu.owner), menu._bot)
    await menu.update([time_embed], buttons)
    
async def time_menu_listener(payload):
    button = payload.button
    menu = button.menu
    if button.custom_id.startswith(ComponentsButton.ID_CALLER):
        await time_refresh_buttons(menu)
    
class Time(commands.Cog, name = 'Tiempo'):
    def __init__(self, bot):
        self.bot = bot
        
    @tasks.loop(minutes=10)    
    async def check_time(self):   
        time_data = load_time_data()
        
        t = datetime.now().timestamp()
        
        if t >= time_data['next']:
            time_data['next'] += time_data['lapse']
            dump_time_data(time_data)
			await self.bot.data_backup(time_data['backup_channel'])
            if time_data['running']:
                await advance_date(self.bot)
        


    @commands.Cog.listener()
    async def on_ready(self):
        self.check_time.start()
        
    @commands.command()
    async def time(self, ctx):
        time_menu = ButtonsMenu(ctx, menu_type=ButtonsMenu.TypeEmbed, show_page_director=False)
        time_embed, buttons = await get_time_embed(is_admin(time_menu.owner), self.bot)
        time_menu.add_page(time_embed)
        for button in buttons:
            time_menu.add_button(button)
        time_menu.set_relay(time_menu_listener)
        await time_menu.start()