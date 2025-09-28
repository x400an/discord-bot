import os
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 投票データ {message_id: {user_id: status}}
vote_data = {}

STATUS = {
    "yes": "🟢",
    "maybe": "🟡",
    "no": "🔴"
}

# /schedule week コマンド
@bot.tree.command(name="schedule", description="一週間の予定候補を作成します")
async def schedule(interaction: discord.Interaction):
    dates = ["10/01(火) 19:00", "10/03(木) 20:00", "10/05(土) 12:00"]

    for date in dates:
        embed = discord.Embed(title=f"【予定候補】 {date}", color=0x2ecc71)
        embed.add_field(name="投票状況", value="🟢0 🟡0 🔴0", inline=False)

        view = VoteView(date)
        await interaction.channel.send(embed=embed, view=view)

class VoteView(discord.ui.View):
    def __init__(self, date):
        super().__init__(timeout=None)
        self.date = date
        self.add_item(VoteButton(date, "yes", discord.ButtonStyle.success, "参加(🟢)"))
        self.add_item(VoteButton(date, "maybe", discord.ButtonStyle.primary, "調整可(🟡)"))
        self.add_item(VoteButton(date, "no", discord.ButtonStyle.danger, "不可(🔴)"))

class VoteButton(discord.ui.Button):
    def __init__(self, date, status, style, label):
        super().__init__(style=style, label=label)
        self.date = date
        self.status = status

    async def callback(self, interaction: discord.Interaction):
        message_id = interaction.message.id
        user_id = interaction.user.id

        if message_id not in vote_data:
            vote_data[message_id] = {}

        vote_data[message_id][user_id] = self.status

        # 投票状況集計
        counts = {"yes":0, "maybe":0, "no":0}
        for s in vote_data[message_id].values():
            counts[s] += 1

        embed = discord.Embed(title=f"【予定候補】 {self.date}", color=0x2ecc71)
        embed.add_field(name="投票状況", value=f"🟢{counts['yes']} 🟡{counts['maybe']} 🔴{counts['no']}", inline=False)

        await interaction.response.edit_message(embed=embed, view=self.view)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(e)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
