@bot.tree.command(name="event_now", description="テストイベント")
async def event_now(interaction: discord.Interaction):
    await interaction.response.send_message("イベント作成テスト！")
