import os
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 投票データを保持 {message_id: {date: {user_id: status}}}
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
    embed = discord.Embed(title="【来週の予定候補】", color=0x2ecc71)
    for d in dates:
        embed.add_field(name=d, value="🟢0 🟡0 🔴0", inline=False)

    view = VoteView(dates)
    await interaction.response.send_message(embed=embed, view=view)
    message = await interaction.original_response()
    vote_data[message.id] = {d: {} for d in dates}

class VoteView(discord.ui.View):
    def __init__(self, dates):
        super().__init__(timeout=None)
        self.dates = dates
        # 各日程に対してボタンを作成
        for date in dates:
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
        vote_data[message_id][self.date][user_id] = self.status

        embed = discord.Embed(title="【来週の予定候補】", color=0x2ecc71)
        for d in vote_data[message_id]:
            votes = vote_data[message_id][d]
            counts = {"yes":0, "maybe":0, "no":0}
            users = {"yes":[], "maybe":[], "no":[]}
            for uid, s in votes.items():
                counts[s] += 1
                users[s].append(f"<@{uid}>")
            line = f"{STATUS['yes']}{counts['yes']} {', '.join(users['yes'])}\n"
            line += f"{STATUS['maybe']}{counts['maybe']} {', '.join(users['maybe'])}\n"
            line += f"{STATUS['no']}{counts['no']} {', '.join(users['no'])}"
            embed.add_field(name=d, value=line, inline=False)
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
