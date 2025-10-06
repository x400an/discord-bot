import discord
from discord import app_commands
import datetime

# IntentsとBotの初期化
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# 投票データ
vote_data = {}

# 投票用View
class VoteView(discord.ui.View):
    def __init__(self, date_str):
        super().__init__(timeout=None)
        self.date_str = date_str

    @discord.ui.button(label="参加(🟢)", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "参加(🟢)")

    @discord.ui.button(label="調整可(🟡)", style=discord.ButtonStyle.blurple)
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "調整可(🟡)")

    @discord.ui.button(label="不可(🔴)", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "不可(🔴)")

    async def register_vote(self, interaction: discord.Interaction, status: str):
        user = interaction.user.name
        message_id = interaction.message.id

        if message_id not in vote_data:
            vote_data[message_id] = {}

        if self.date_str not in vote_data[message_id]:
            vote_data[message_id][self.date_str] = {
                "参加(🟢)": [], "調整可(🟡)": [], "不可(🔴)": []
            }

        # 他の選択肢から削除
        for k in vote_data[message_id][self.date_str]:
            if user in vote_data[message_id][self.date_str][k]:
                vote_data[message_id][self.date_str][k].remove(user)

        # 新しい選択肢に追加
        vote_data[message_id][self.date_str][status].append(user)

        # Embed更新
        embed = interaction.message.embeds[0]
        for k in ["参加(🟢)", "調整可(🟡)", "不可(🔴)"]:
            users = vote_data[message_id][self.date_str][k]
            embed.set_field_at(
                ["参加(🟢)", "調整可(🟡)", "不可(🔴)"].index(k),
                name=k,
                value="\n".join(users) if users else "なし",
                inline=False
            )

        await interaction.response.edit_message(embed=embed, view=self)

# /schedule コマンド
@tree.command(name="schedule", description="日程調整を開始します")
async def schedule(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    today = datetime.date.today()
    dates = [(today + datetime.timedelta(days=i)).strftime("%m/%d(%a)") for i in range(7)]

    for d in dates:
        embed = discord.Embed(title=f"【日程候補】{d}", description="以下のボタンで投票してください")
        embed.add_field(name="参加(🟢)", value="なし", inline=False)
        embed.add_field(name="調整可(🟡)", value="なし", inline=False)
        embed.add_field(name="不可(🔴)", value="なし", inline=False)
        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.followup.send("📅 日程候補を作成しました！", ephemeral=True)

# Bot起動時にコマンド同期
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await tree.sync()
        print("✅ Slash commands synced!")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# トークンで起動
import os
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ DISCORD_BOT_TOKEN が設定されていません。Renderの環境変数を確認してください。")

bot.run(TOKEN)