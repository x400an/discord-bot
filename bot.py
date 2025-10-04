import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 投票データ: {message_id: {user_id: status}}
vote_data = {}

STATUS = {
    "yes": "🟢",
    "maybe": "🟡",
    "no": "🔴"
}


@bot.tree.command(name="schedule", description="次週の日曜始まりの予定候補を作成します")
async def schedule(interaction: discord.Interaction):
    # ✅ Discordに「応答準備中」と伝える（3秒ルール回避）
    await interaction.response.defer(thinking=True, ephemeral=True)

    today = datetime.utcnow()
    next_sunday = today + timedelta(days=(6 - today.weekday()) + 7)
    dates = [next_sunday + timedelta(days=i) for i in range(7)]
    date_strings = [d.strftime("%m/%d(%a)") for d in dates]

    # 各日程ごとにメッセージ生成
    for date_str in date_strings:
        embed = discord.Embed(title=f"【予定候補】 {date_str}", color=0x2ecc71)
        embed.add_field(name="投票状況", value="🟢0 🟡0 🔴0", inline=False)
        view = VoteView(date_str)
        message = await interaction.channel.send(embed=embed, view=view)
        vote_data[message.id] = {}

        # 締め切り日時（作成から7日後）
        close_time = datetime.utcnow() + timedelta(days=7)
        asyncio.create_task(schedule_close(message, date_str, close_time))

    # ✅ コマンド発行者への完了通知（本人にしか見えない）
    await interaction.followup.send("✅ 予定候補を作成しました！", ephemeral=True)


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

        try:
            await update_embed(interaction.message, self.date, interaction)
        except Exception as e:
            print(f"投票更新でエラー: {e}")


async def update_embed(message, date, interaction=None):
    votes = vote_data.get(message.id, {})
    counts = {"yes": 0, "maybe": 0, "no": 0}
    users = {"yes": [], "maybe": [], "no": []}

    for uid, s in votes.items():
        counts[s] += 1
        users[s].append(f"<@{uid}>")

    line = (
        f"🟢 {counts['yes']}: {', '.join(users['yes']) if users['yes'] else 'なし'}\n"
        f"🟡 {counts['maybe']}: {', '.join(users['maybe']) if users['maybe'] else 'なし'}\n"
        f"🔴 {counts['no']}: {', '.join(users['no']) if users['no'] else 'なし'}"
    )

    embed = discord.Embed(title=f"【予定候補】 {date}", color=0x2ecc71)
    embed.add_field(name="投票状況", value=line, inline=False)

    try:
        if interaction:
            # interaction.response は1回のみ使用可能
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=interaction.message.view)
            else:
                await interaction.followup.edit_message(message_id=message.id, embed=embed, view=interaction.message.view)
        else:
            await message.edit(embed=embed, view=message.view)
    except Exception as e:
        print(f"Embed更新でエラー: {e}")


async def schedule_close(message, date, close_time):
    """指定日時に自動締め切り処理"""
    now = datetime.utcnow()
    wait_seconds = (close_time - now).total_seconds()
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    try:
        # ボタンを無効化
        for child in message.view.children:
            child.disabled = True

        # Embedを更新して締め切りマークを追加
        await update_embed(message, date)
        embed = message.embeds[0]
        embed.title += " (締め切り)"
        await message.edit(embed=embed, view=message.view)
    except Exception as e:
        print(f"締め切り処理でエラー: {e}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(e)


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
