import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os

# -------------------
# Bot設定
# -------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------
# 投票データ管理
# {message_id: {date_or_event: {status: [usernames]}}}
# -------------------
vote_data = {}

# -------------------
# 投票用ビュー
# -------------------
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

# -------------------
# /schedule: 定期的な日程調整
# -------------------
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

# -------------------
# /event_now: 突発イベント作成
# -------------------
@bot.tree.command(name="event_now", description="突発イベントを作成して投票できます")
@app_commands.describe(
    title="イベント名",
    description="詳細説明（任意）",
    date="投票日程（複数可、カンマ区切り、任意）"
)
async def event_now(interaction: discord.Interaction, title: str, description: str = None, date: str = None):
    if date:
        date_list = [d.strip() for d in date.split(",")]
    else:
        today = datetime.date.today()
        date_list = [today.strftime("%m/%d(%a)")]

    for d in date_list:
        embed_title = f"【突発イベント】{title} - {d}"
        embed = discord.Embed(title=embed_title, description=description or "詳細なし")
        embed.add_field(name="参加(🟢)", value="なし", inline=False)
        embed.add_field(name="調整可(🟡)", value="なし", inline=False)
        embed.add_field(name="不可(🔴)", value="なし", inline=False)

        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.response.send_message(f"⚡ 突発イベント『{title}』を作成しました！", ephemeral=True)

# -------------------
# Bot起動時
# -------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# -------------------
# トークン取得 & 起動
# -------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ DISCORD_BOT_TOKEN が設定されていません。Renderの環境変数を確認してください。")

bot.run(TOKEN)
