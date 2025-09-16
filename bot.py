import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("こんにちは！ボットが稼働しています。")

# ← 環境変数からトークンを取得
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
