import time, discord, pymysql, os
from functools import wraps
from discord import Intents, AllowedMentions, Activity, ActivityType
from discord.ext.commands import AutoShardedBot as AB
from dotenv import load_dotenv

load_dotenv()

def mysql(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start = time.time()
        with self.db.cursor() as cursor:
            result = func(self, *args, **kwargs)
            end = time.time()
            execution_time = round(end - start, 3)
            affected_rows = cursor.rowcount
        self.db.commit()
        return {'execution_time': execution_time, 'result': result, 'affected_rows': affected_rows}
    return wrapper

class MySQL:
    def __init__(self, db):
        self.db = db
        self.db.cursorclass = pymysql.cursors.DictCursor
        
        self.db.execute = mysql(self.execute)
        self.db.fetch = mysql(self.fetch)

    @mysql
    def execute(self, query, params=None):
        cursor = self.db.cursor()
        cursor.execute(query, params)
        return None

    @mysql
    def fetch(self, query, params=None):
        cursor = self.db.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
    
    @mysql
    def fetchall(self, query, params=None):
        cursor = self.db.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

ok = pymysql.connect(**{
    'host': 'localhost',
    'user': 'root',
    'passwd': 'password',
    'db': 'test',
    'port': 3306,
    'charset': 'utf8',
    'connect_timeout': 3600,
    'autocommit': True
})

class EEK(AB):
    def __init__ (self, *args, **kwargs):
        super().__init__(
            command_prefix='!',
            intents = Intents.all(),
            owner_ids = [1116267335154683955, 1060655177268469811],
            help_command=None,
            allowed_mentions = AllowedMentions(
                everyone=False,
                replied_user=False,
                users=True,
                roles=False,
            ),
            activity = Activity(type=ActivityType.streaming, url='https://www.twitch.tv/#', name='Ceek cu Week in studio pregatesc EEKU sa apara pe harta')
        )
    
        self.db = MySQL(ok)

bot = EEK()

@bot.command()
async def win(ctx, user: discord.User):
    if ctx.author.id not in bot.owner_ids:
        return
    result = bot.db.fetch("SELECT * FROM users WHERE user_id = %s", (user.id,))
    if result['result']:
        points = result['result']['points'] + 50
        bot.db.execute("UPDATE users SET points = %s WHERE user_id = %s", (points, user.id))
        await ctx.reply(embed=discord.Embed(description=f"Au fost adaugate 50 de puncte userului {user.mention} (acum are {points} puncte)", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))
    else:
        bot.db.execute("INSERT INTO users (user_id, points) VALUES (%s, 50)", (user.id,))
        await ctx.reply(embed=discord.Embed(description=f"Au fost adaugate 50 de puncte userului {user.mention} (acum are 50 puncte)", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))

@bot.command()
async def lose(ctx, user: discord.User):
    if ctx.author.id not in bot.owner_ids:
        return
    result = bot.db.fetch("SELECT * FROM users WHERE user_id = %s", (user.id,))
    if result['result']:
        points = result['result']['points'] - 50
        bot.db.execute("UPDATE users SET points = %s WHERE user_id = %s", (points, user.id))
        await ctx.reply(embed=discord.Embed(description=f"Au fost eliminate 50 de puncte userului {user.mention} (acum are {points} puncte)", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))
    else:
        bot.db.execute("INSERT INTO users (user_id, points) VALUES (%s, -50)", (user.id,))
        await ctx.reply(embed=discord.Embed(description=f"Au fost eliminate 50 de puncte userului {user.mention} (acum are -50 puncte)", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))

@bot.command()
async def points(ctx, user: discord.User=None):
    if user is None: user = ctx.author
    result = bot.db.fetch("SELECT points FROM users WHERE user_id = %s", (user.id,))
    if result['result']:
        await ctx.reply(embed=discord.Embed(description=f"{user.mention} are {result['result']['points']} puncte", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))
    else:
        await ctx.reply(embed=discord.Embed(description=f"{user.mention} are 0 puncte", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))

@bot.command(aliases=["lb"])
async def leaderboard(ctx):
    results = bot.db.fetchall("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10")
    if results['result']:
        description = "\n".join([f"{i}. <@{row['user_id']}> - {row['points']} puncte" for i, row in enumerate(results['result'], start=1)])
    else:
        description = "Nimeni nare puncte"
    embed = discord.Embed(title="Leaderboard", description=description, color=discord.Colour.from_rgb(136, 8, 8))
    embed.set_footer(text="#EEK 2024")
    await ctx.reply(embed=embed)

@bot.command()
async def reset(ctx, user: discord.User):
    if ctx.author.id not in bot.owner_ids:
        return
    result = bot.db.fetch("SELECT * FROM users WHERE user_id = %s", (user.id,))
    if result['result']:
        bot.db.execute("DELETE FROM users WHERE user_id = %s", (user.id,))
        await ctx.reply(embed=discord.Embed(description=f"{user.mention} acum are 0 puncte", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))
    else:
        await ctx.reply(embed=discord.Embed(description=f"{user.mention} avea deja 0 puncte", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))

@bot.command()
async def sageti(ctx):
    file = 'sageti.txt'
    
    if not os.path.exists(file):
        return await ctx.reply(embed=discord.Embed(description=f"Nu exista sageti", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))
    
    with open(file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    if not lines:
        return await ctx.reply(embed=discord.Embed(description=f"Nu exista sageti", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))
    
    embed = discord.Embed(title="Sageti EEK", color=discord.Colour.from_rgb(136, 8, 8))
    for i, line in enumerate(lines, start=1):
        embed.add_field(name=f"Sagetica numaru {i}", value=line, inline=False)
    
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(text="#EEK 2024")
    
    await ctx.reply(embed=embed)

@bot.command()
async def addsageata(ctx, *, sajet: str):
    if ctx.author.id not in bot.owner_ids:
        return
    
    file = 'sageti.txt'
    
    if not os.path.exists(file):
        with open(file, 'w', encoding='utf-8'):
            pass
    
    with open(file, 'a', encoding='utf-8') as f:
        f.write(sajet.strip() + '\n')
    
    await ctx.reply(embed=discord.Embed(description=f"Acum {sajet} este sagetica noastra", color=discord.Colour.from_rgb(136, 8, 8)).set_footer(text="#EEK 2024"))

@bot.command()
async def help(ctx):
    commands = {
        'win': 'Adauga un win unui utilizator (ADMINISTRATOR)',
        'lose': 'Adauga un lose unui utilizator (ADMINISTRATOR)',
        'points': 'Vezi punctele unui utilizator',
        'leaderboard': 'Vezi leaderboardul',
        'reset': 'Reseteaza punctele unui utilizator (ADMINISTRATOR)',
        'sageti': 'Vezi sagetile klanului EEK',
        'addsageata': 'Adauga o sagetica (ADMINISTRATOR)'
    }
    
    description = "\n".join([f"!{command}: {description}" for command, description in commands.items()])
    embed = discord.Embed(title='Help', description=description, color=discord.Colour.from_rgb(136, 8, 8)).set_thumbnail(url=bot.user.avatar.url).set_footer(text="#EEK 2024")
    
    await ctx.reply(embed=embed)

@bot.event
async def on_ready():
    results = bot.db.fetchall("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10")
    for row in results['result']: print(row)

bot.run(os.getenv('TOKEN'))
