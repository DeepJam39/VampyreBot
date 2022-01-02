from discord.ext import commands
import discord
import random
from collections import Counter
import json

def _roll_final(net, successes):
    final = ""
    if net == 0:
        final = "Fallo"
    elif net < 0:
        if successes > 0:
            final = "Fallo"
        else:
            final = "Fracaso"
    else:
        final = f"{net} éxito{'s' if net>1 else ''}"
    return final

with open('./data/dice_rolls.json', 'r') as f:
    dice_rolls = json.load(f)
    
dice_rolls = {
    int(dice):{
        int(dif):{
            int(suc):dice_rolls[dice][dif][suc] 
            for suc in dice_rolls[dice][dif]} 
        for dif in dice_rolls[dice]} 
    for dice in dice_rolls}    

def exact_chance(dice, difficulty=6, success_amount=1):
    try:
        dice = int(dice)
        difficulty = int(difficulty)
        success_amount = int(success_amount)
    except ValueError:
        raise ValueError("Error: La cantidad de dados, la dificultad y la cantidad de éxitos deben ser números enteros.")
    
    if dice < 1:
        raise KeyError("Error: La cantidad mínima de dados es 1.")
    if dice > 20:
        raise KeyError("Error: La cantidad máxima de dados es 20.")
    if difficulty < 3:
        raise KeyError("Error: La dificultad mínima es 3.")
    if difficulty > 10:
        raise KeyError("Error: La dificultad máxima es 10.")
        
    return dice_rolls[int(dice)][int(difficulty)].get(int(success_amount))

def success_chance(dice, difficulty=6, success_amount=1):
    chance = 0
    for i in range(int(success_amount), dice+1):
        try:
            chance += exact_chance(dice, difficulty, i)
        except:
            pass
    return chance

def failure_chance(dice, difficulty=6):
    return 100-success_chance(dice, difficulty=6)

def regular_failure_chance(dice, difficulty=6, success_amount=1):
    return 100-success_chance(dice, difficulty, success_amount)-botch_chance(dice, difficulty)

def botch_chance(dice, difficulty=6):
    return exact_chance(dice, difficulty, -1)

def sfbm(dice, difficulty=6, success_amount=1):
    return (success_chance(dice, difficulty, success_amount), 
            regular_failure_chance(dice, difficulty, success_amount), 
            botch_chance(dice, difficulty), 
            Counter(dice_rolls[int(dice)][int(difficulty)]).most_common(1)[0])

def average_successes(dice, difficulty=6):
    return sum([k*dice_rolls[int(dice)][int(difficulty)][k] for k in dice_rolls[int(dice)][int(difficulty)]])/100

def pretty_sfbm(dice, difficulty = 6, success_amount=1):
    try:
        dice = int(dice)
        difficulty = int(difficulty)
        success_amount = int(success_amount)
        s_chance, f_chance, b_chance, (most_likely, most_likely_chance) = sfbm(dice, difficulty, success_amount)
    except KeyError as e:
        result_text = str(e).replace("'", "")
    except ValueError:
        result_text = "Error: La cantidad de dados, la dificultad y la cantidad de éxitos necesarios deben ser números enteros."    
    else:
        most_likely = "Fracaso" if most_likely == -1 else (
            "Fallo" if most_likely == 0 else f"{most_likely} éxito{'s' if most_likely>1 else ''}")
        result_text = f"Probabilidad de éxito: {s_chance:.0f}%\n"
        result_text += f"Probabilidad de fallo: {f_chance:.0f}%\n"
        result_text += f"Probabilidad de fracaso: {b_chance:.0f}%\n"
        result_text += f"Resultado más probable: {most_likely} (con una probabilidad del {most_likely_chance:.0f}%)"        
    return result_text

class Chance(commands.Cog, name = 'Suerte'):
    def __init__(self, bot):
        self.bot = bot
        self.last_roll = None
        
    @commands.command(aliases=['rtd'])
    async def roll(self, ctx, dice:str=None, dif:int=6):
        """
        ¡Lanza los dados! Como con el querido RPGBot, puedes decir:         
        `vp!rtd 6d10`
        y lanzará 6 dados de diez caras, pero... si en vez de eso especificas: 
        `vp!rtd 6d10 7`
        lanzará los mismos 6 dados de 10 caras, pero con una dificultad de 7. El bot cuenta los éxitos, fallos y fracasos. También puedes decir:
        `vp!rtd`
        para repetir la última tirada, o lanzar los dados correspondientes al último pronóstico que hayas hecho usando el comando vp!chance.
        
        La dificultad por defecto es 7.
        """
        if dice is None:
            if self.last_roll is not None:
                dice = self.last_roll['dice']
                sides = self.last_roll['sides']
                dif = self.last_roll['dif']
            else:
                content = "No hay tiradas registradas. Debe introducir al menos la cantidad de dados."
                await ctx.send(content)
        else:                 
            sides = 10
            i = dice.find('d')
            if i > -1:
                dice, sides = dice[:i], dice[i+1:] or 10
            dice = int(dice)
            sides = int(sides)
        
        results = [random.randint(1, sides) for i in range(dice)]
        random_number = random.randint(1, 10)
        
        format_n = lambda i: f"{i}" if i==1 else (f"**__{i}__**" if i==sides else (f"__{i}__" if i>=dif else f"||{i}||"))
        
        content = f"{ctx.author.name} lanzó  ([   {'   '.join([format_n(i) for i in results])}   ])  a dificultad {dif}\n"
        successes = len([i for i in results if i>=dif])
        ones = len([i for i in results if i==1])
        tens = len([i for i in results if i==sides])
        content += f"Éxitos: {successes}\n"
        
        if ones > 0:
            content += f"1s: {ones}\n"
            
        if tens > 0:
            content += f"{sides}s: {tens}\n"
        
        final = f"{_roll_final(successes - ones, successes)}"
        if tens > 0:
            final += f"      ||**Con especialidad:** {_roll_final(successes + tens - ones, successes + tens)}||"
        
        content += f"**Final:** {final}"
            
        #await ctx.send(embed = discord.Embed(description=content, colour=discord.Colour.blue()))
        await ctx.send(content)
        self.last_roll = {'dice': dice, 'sides': sides, 'dif': dif, 'succ': 1}
        
    @commands.command()
    async def chance(self, ctx, dice:str, dif:str="6", succ:str="1"):
        """
        Te muestra cuáles son las probabilidades de éxito, fallo y fracaso para una tirada dada, así como la cantidad más probable de éxitos.
        `vp!chance 6 7` (6 dados a dificultad 7)
        Solo funciona con dados de 10 caras. También puedes especificar la cantidad de éxitos necesarios:
        `vp!chance 6 7 3` (6 dados a dificultad 7, se necesitan 3 éxitos)        
        """
        i = dice.find('d')
        if i > -1:
            dice = dice[:i]
        
        result_text = pretty_sfbm(dice, dif, succ)
        if not result_text.startswith("Error"):
            content = f"{ctx.author.name} se prepara para lanzar {dice} dado{'s' if int(dice)>1 else ''} a dificultad {dif}."
            if int(succ) > 1:
                content += f" Necesita {succ} éxitos."
            content += f"\n\n{result_text}"
            self.last_roll = {'dice': int(dice), 'sides': 10, 'dif': int(dif), 'succ': int(succ)}
        else:
            content = result_text       
        
        await ctx.send(content)