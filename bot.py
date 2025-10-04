import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 投票データ {message_id: {date: {status: [usernames]}}}
vote_data = {}

class VoteView(discord.ui.View):
    def __init__(self, date_str):
        super().__init__(timeout=None)
        self.date_str = date_str

    @discord.ui.button(label="参加(🟢)", style=discord.ButtonStyle.success)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "参加(🟢)")

    @discord.ui.button(label="調整可(🟡)", style=discord.ButtonStyle.primary)
    async def maybe_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "調整可(🟡)")

    @discord.ui.button(label="不可(🔴)", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "不可(🔴)")

    async def register_vote(self, interaction: discord.Interaction, status: str):
        message_id = interaction.message.id
        user = interaction.user.display_name

        if message_id not in vote_data:
            vote_data[message_id] = {}
        if self.date_str not in vote_data[message_id]:
            vote_data[message_id][self.date_str] = {"参加(🟢)": [], "調整可(🟡)": [], "不可(🔴)": []}

        # 他の選択肢から削除して新しい方に追加
        for k in vote_data[message_id][self.date_str]:
            if user in vote_data[message_id][self.date_str][k]:
                vote_data[message_id][self.date_str][k].remove(user)
        vote_data[message_id][self.date_str][status].append(user)

        # Embed更新
        embed = discord.Embed(title=f"【予定候補】{self.date_str}")
        for k, v in vote_data[message_id][self.date_str].items():
            embed.add_field(name=k, value="\n".join(v) if v else "なし", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)


# -----------------------
# /schedule コマンド（通常の1週間候補）
# -----------------------
@bot.tree.command(name="schedule", description="日程調整を開始します")
async def schedule(interaction: discord.Interaction):
    today = datetime.date.today()
    dates = [(today + datetime.timedelta(days=i)).strftime("%m/%d(%a)") for i in range(7)]

    for d in dates:
        embed = discord.Embed(title=f"【予定候補】{d}", description="投票してください！")
        embed.add_field(name="参加(🟢)", value="なし", inline=False)
        embed.add_field(name="調整可(🟡)", value="なし", inline=False)
        embed.add_field(name="不可(🔴)", value="なし", inline=False)

        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.response.send_message("📅 日程候補を作成しました！", ephemeral=True)


# -----------------------
# /event_now コマンド（突発イベント）
# -----------------------
@bot.tree.command(name="event_now", description="突発イベントを作成します")
@app_commands.describe(
    title="イベント名",
    description="詳細(任意)",
    date="日程(任意、カンマ区切り)"
)
async def event_now(interaction: discord.Interaction, title: str, description: str = "詳細なし", date: str = None):
    today = datetime.date.today()
    # 日付をリスト化（省略時は今日のみ）
    dates = [d.strip() for d in date.split(",")] if date else [today.strftime("%m/%d(%a)")]

    for d in dates:
        embed = discord.Embed(title=f"【{title}】{d}", description=description)
        embed.add_field(name="参加(🟢)", value="なし", inline=False)
        embed.add_field(name="調整可(🟡)", value="なし", inline=False)
        embed.add_field(name="不可(🔴)", value="なし", inline=False)
        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.response.send_message("📅 イベント作成完了！", ephemeral=True)


# -----------------------
# 起動時イベント
# -----------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()  # 全体同期
        print(f"🔄 Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"❌ Sync error: {e}")


# -----------------------
# Botトークン起動
# -----------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ DISCORD_BOT_TOKEN が設定されていません。Renderの環境変数を確認してください。")

bot.run(TOKEN)
