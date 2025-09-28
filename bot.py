```python
import os
import discord
from discord.ext import commands
from discord import app_commands

# Botの準備
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 投票データを保持する辞書
# { message_id: { date: {user_id: status} } }
vote_data = {}

# ステータスの絵文字
STATUS = {
    "yes": "🟢",   # 参加
    "maybe": "🟡", # 調整可
    "no": "🔴"     # 不可
}

# /schedule week コマンド
@bot.tree.command(name="schedule", description="一週間の予定候補を作成します")
async def schedule(interaction: discord.Interaction):
    # 仮の候補日（実際は自動生成してもOK）
    dates = ["10/01(火) 19:00", "10/03(木) 20:00", "10/05(土) 12:00"]

    embed = discord.Embed(title="【来週の予定候補】", color=0x2ecc71)
    for d in dates:
        embed.add_field(name=d, value="🟢0 🟡0 🔴0", inline=False)

    # ボタンを作成
    view = VoteView(dates)
    msg = await interaction.response.send_message(embed=embed, view=view)
    message = await interaction.original_response()

    # 投票データの初期化
    vote_data[message.id] = {d: {} for d in dates}


class VoteView(discord.ui.View):
    def __init__(self, dates):
        super().__init__(timeout=None)
        self.dates = dates

    @discord.ui.button(label="参加(🟢)", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vote(interaction, "yes")

    @discord.ui.button(label="調整可(🟡)", style=discord.ButtonStyle.primary)
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vote(interaction, "maybe")

    @discord.ui.button(label="不可(🔴)", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vote(interaction, "no")

    async def vote(self, interaction: discord.Interaction, status: str):
        message_id = interaction.message.id
        user_id = interaction.user.id

        # 最初の候補を対象に保存（改良すれば日付選択可能にできる）
        target_date = self.dates[0]
        vote_data[message_id][target_date][user_id] = status

        # Embed更新
        embed = discord.Embed(title="【来週の予定候補】", color=0x2ecc71)
        for d in self.dates:
            votes = vote_data[message_id][d]
            counts = {"yes": 0, "maybe": 0, "no": 0}
            users = {"yes": [], "maybe": [], "no": []}
            for uid, s in votes.items():
                counts[s] += 1
                users[s].append(f"<@{uid}>")

            line = f"{STATUS['yes']}{counts['yes']} {', '.join(users['yes'])}\n"
            line += f"{STATUS['maybe']}{counts['maybe']} {', '.join(users['maybe'])}\n"
            line += f"{STATUS['no']}{counts['no']} {', '.join(users['no'])}"
            embed.add_field(name=d, value=line, inline=False)

        await interaction.response.edit_message(embed=embed, view=self)


# Bot起動
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(e)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
```

