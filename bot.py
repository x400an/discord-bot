import datetime
import os

# Intents
intents = discord.Intents.default()
intents.message_content = True

@@ -12,6 +13,9 @@
# 投票データ {message_id: {date: {status: [usernames]}}}
vote_data = {}

# ----------------------------
# 投票用View
# ----------------------------
class VoteView(discord.ui.View):
    def __init__(self, date_str):
        super().__init__(timeout=None)
@@ -38,7 +42,7 @@ async def register_vote(self, interaction: discord.Interaction, status: str):
        if self.date_str not in vote_data[message_id]:
            vote_data[message_id][self.date_str] = {"参加(🟢)": [], "調整可(🟡)": [], "不可(🔴)": []}

        # 他の選択肢から削除して新しい方に追加
        # 他の選択肢から削除
        for k in vote_data[message_id][self.date_str]:
            if user in vote_data[message_id][self.date_str][k]:
                vote_data[message_id][self.date_str][k].remove(user)
@@ -51,14 +55,11 @@ async def register_vote(self, interaction: discord.Interaction, status: str):

        await interaction.response.edit_message(embed=embed, view=self)


# -------------------------------
# /schedule コマンド (元の7日間候補)
# -------------------------------
# ----------------------------
# /schedule コマンド
# ----------------------------
@bot.tree.command(name="schedule", description="日程調整を開始します")
async def schedule(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # defer して3秒ルール対応

    today = datetime.date.today()
    dates = [(today + datetime.timedelta(days=i)).strftime("%m/%d(%a)") for i in range(7)]

@@ -67,52 +68,41 @@ async def schedule(interaction: discord.Interaction):
        embed.add_field(name="参加(🟢)", value="なし", inline=False)
        embed.add_field(name="調整可(🟡)", value="なし", inline=False)
        embed.add_field(name="不可(🔴)", value="なし", inline=False)
        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.followup.send("📅 日程候補を作成しました！", ephemeral=True)
        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.response.send_message("📅 日程候補を作成しました！", ephemeral=True)

# -------------------------------
# /event_now コマンド (突発イベント)
# -------------------------------
@bot.tree.command(name="event_now", description="突発イベントを作成します")
# ----------------------------
# /event_now コマンド
# ----------------------------
@bot.tree.command(name="event_now", description="突発イベントを作成")
@app_commands.describe(
    title="イベント名 (必須)",
    description="イベントの詳細 (任意)",
    date="投票する日程（複数可、空欄なら今日のみ）"
    title="イベント名",
    description="詳細（任意）",
    date="投票日程（任意、複数可、カンマ区切り、例: 10/05,10/06）"
)
async def event_now(interaction: discord.Interaction, title: str, description: str = "", date: str = ""):
    await interaction.response.defer(ephemeral=True)  # defer

    # 日付処理
    dates = []
async def event_now(interaction: discord.Interaction, title: str, description: str = None, date: str = None):
    # 日程を決定
    if date:
        # ,区切りで複数日指定可能
        for d in date.split(","):
            try:
                parsed = datetime.datetime.strptime(d.strip(), "%Y-%m-%d").strftime("%m/%d(%a)")
                dates.append(parsed)
            except ValueError:
                await interaction.followup.send(f"⚠️ 日付フォーマットが不正です: {d} (YYYY-MM-DD)", ephemeral=True)
                return
        dates = [d.strip() for d in date.split(",")]
    else:
        today = datetime.date.today()
        dates.append(today.strftime("%m/%d(%a)"))
        dates = [today.strftime("%m/%d(%a)")]

    # 各日付にVoteView付きEmbed送信
    for d in dates:
        embed = discord.Embed(title=f"【突発イベント】{title}", description=description or "詳細なし")
        embed = discord.Embed(title=f"【突発イベント】{title} - {d}", description=description or "詳細なし")
        embed.add_field(name="参加(🟢)", value="なし", inline=False)
        embed.add_field(name="調整可(🟡)", value="なし", inline=False)
        embed.add_field(name="不可(🔴)", value="なし", inline=False)
        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.followup.send(f"📢 イベント `{title}` を作成しました！", ephemeral=True)
        await interaction.channel.send(embed=embed, view=VoteView(d))

    await interaction.response.send_message(f"🚨 イベント「{title}」を作成しました！", ephemeral=True)

# -------------------------------
# ----------------------------
# on_ready
# -------------------------------
# ----------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
@@ -122,10 +112,9 @@ async def on_ready():
    except Exception as e:
        print(f"❌ Sync error: {e}")


# -------------------------------
# BOTトークンで起動
# -------------------------------
# ----------------------------
# トークンで起動
# ----------------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ DISCORD_BOT_TOKEN が設定されていません。Renderの環境変数を確認してください。")