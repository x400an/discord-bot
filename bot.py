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


# -------------------------------
# /schedule コマンド (元の7日間候補)
# -------------------------------
@bot.tree.command(name="schedule", description="日程調整を開始します")
async def schedule(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # defer して3秒ルール対応

    today = datetime.date.today()
    dates = [(today + datetime.timedelta(days=i)).strftime("%m/%d(%a)") for i in range(7)]

    for d in dates:
        embed = discord.Embed(title=f"【予定候補】{d}", description="投票してください！")
        embed.add_field(name="参加(🟢)", value="なし", inline=False)
        embed.add_field(name="調整可(🟡)", value="なし", inline=False)
        embed.add_field(name="不可(🔴)", value="なし", inline=False)
        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.followup.send("📅 日程候補を作成しました！", ephemeral=True)


# -------------------------------
# /event_now コマンド (突発イベント)
# -------------------------------
@bot.tree.command(name="event_now", description="突発イベントを作成します")
@app_commands.describe(
    title="イベント名 (必須)",
    description="イベントの詳細 (任意)",
    date="投票する日程（複数可、空欄なら今日のみ）"
)
async def event_now(interaction: discord.Interaction, title: str, description: str = "", date: str = ""):
    await interaction.response.defer(ephemeral=True)  # defer

    # 日付処理
    dates = []
    if date:
        # ,区切りで複数日指定可能
        for d in date.split(","):
            try:
                parsed = datetime.datetime.strptime(d.strip(), "%Y-%m-%d").strftime("%m/%d(%a)")
                dates.append(parsed)
            except ValueError:
                await interaction.followup.send(f"⚠️ 日付フォーマットが不正です: {d} (YYYY-MM-DD)", ephemeral=True)
                return
    else:
        today = datetime.date.today()
        dates.append(today.strftime("%m/%d(%a)"))

    # 各日付にVoteView付きEmbed送信
    for d in dates:
        embed = discord.Embed(title=f"【突発イベント】{title}", description=description or "詳細なし")
        embed.add_field(name="参加(🟢)", value="なし", inline=False)
        embed.add_field(name="調整可(🟡)", value="なし", inline=False)
        embed.add_field(name="不可(🔴)", value="なし", inline=False)
        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.followup.send(f"📢 イベント `{title}` を作成しました！", ephemeral=True)


# -------------------------------
# on_ready
# -------------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"❌ Sync error: {e}")


# -------------------------------
# BOTトークンで起動
# -------------------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ DISCORD_BOT_TOKEN が設定されていません。Renderの環境変数を確認してください。")

bot.run(TOKEN)
