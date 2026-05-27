import discord
import os
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput, Select

TOKEN = os.environ["TOKEN"]
MODERATION_CHANNEL_ID = int(os.environ["MODERATION_CHANNEL_ID"])

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


class AnketaModalPart2(Modal, title="Анкета — часть 2 из 2"):
    plans_season = TextInput(label="6. Планы на текущий сезон", style=discord.TextStyle.paragraph, placeholder="Опишите ваши планы...", required=True, max_length=500)
    activities = TextInput(label="7. Чем займётесь на сервере?", style=discord.TextStyle.paragraph, placeholder="PvP, PvE, строительство, торговля...", required=True, max_length=300)
    previous_guilds = TextInput(label="9. Поселения / гильдии на сервере", style=discord.TextStyle.short, placeholder="Если не было — напишите «нет»", required=True, max_length=300)
    other_projects = TextInput(label="10. Опыт в других проектах", style=discord.TextStyle.paragraph, placeholder="Перечислите проекты и опыт там", required=True, max_length=400)
    pvp_skill = TextInput(label="11. PvP-скилл (1–10)", style=discord.TextStyle.short, placeholder="Целое число от 1 до 10", required=True, max_length=2)
    mechanics_skill = TextInput(label="12. Знание механик сервера (1–10)", style=discord.TextStyle.short, placeholder="Целое число от 1 до 10", required=True, max_length=2)

    def __init__(self, part1_data: dict):
        super().__init__()
        self.part1_data = part1_data

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pvp = int(self.pvp_skill.value.strip())
            if not (1 <= pvp <= 10):
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ PvP-скилл: введите число от 1 до 10.", ephemeral=True)
            return

        try:
            mechanics = int(self.mechanics_skill.value.strip())
            if not (1 <= mechanics <= 10):
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Знание механик: введите число от 1 до 10.", ephemeral=True)
            return

        data = {**self.part1_data, "plans_season": self.plans_season.value, "activities": self.activities.value, "previous_guilds": self.previous_guilds.value, "other_projects": self.other_projects.value, "pvp_skill": pvp, "mechanics_skill": mechanics}
        view = MicrophoneView(data, interaction.user)
        await interaction.response.send_message("🎙️ **Последний шаг!**\nВыберите ответы на оставшиеся вопросы:", view=view, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        try:
            await interaction.response.send_message("❌ Ошибка. Попробуйте ещё раз.", ephemeral=True)
        except:
            pass


class AnketaModalPart1(Modal, title="Анкета — часть 1 из 2"):
    nickname = TextInput(label="1. Никнейм в игре", style=discord.TextStyle.short, placeholder="Ваш игровой ник", required=True, max_length=64)
    age = TextInput(label="2. Возраст", style=discord.TextStyle.short, placeholder="Введите ваш возраст", required=True, max_length=3)
    hours_per_day = TextInput(label="3. Часов в день на сервер?", style=discord.TextStyle.short, placeholder="Например: 3–5 часов", required=True, max_length=50)
    bans = TextInput(label="4. Были баны? Если да — за что?", style=discord.TextStyle.paragraph, placeholder="Если не было — напишите «нет»", required=True, max_length=500)
    season1 = TextInput(label="5. Играли на 1 сезоне? Достижения?", style=discord.TextStyle.paragraph, placeholder="Если не играли — напишите «нет»", required=True, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age_val = int(self.age.value.strip())
            if not (1 <= age_val <= 120):
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Возраст: введите целое число.", ephemeral=True)
            return

        part1_data = {"nickname": self.nickname.value, "age": age_val, "hours_per_day": self.hours_per_day.value, "bans": self.bans.value, "season1": self.season1.value}
        modal2 = AnketaModalPart2(part1_data)
        await interaction.response.send_modal(modal2)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        try:
            await interaction.response.send_message("❌ Ошибка. Попробуйте ещё раз.", ephemeral=True)
        except:
            pass


class MicrophoneView(View):
    def __init__(self, data: dict, user: discord.User):
        super().__init__(timeout=120)
        self.data = data
        self.user = user
        self.mic_value = None
        self.team_value = None

        mic_select = Select(placeholder="8. Наличие микрофона", options=[discord.SelectOption(label="Да", value="да", emoji="🎙️"), discord.SelectOption(label="Нет", value="нет", emoji="🔇")], custom_id="mic_select", row=0)
        mic_select.callback = self.mic_callback
        self.add_item(mic_select)

        team_select = Select(placeholder="13. Готовы играть в команде?", options=[discord.SelectOption(label="Да", value="да", emoji="🤝"), discord.SelectOption(label="Нет", value="нет", emoji="🚫")], custom_id="team_select", row=1)
        team_select.callback = self.team_callback
        self.add_item(team_select)

        submit_btn = Button(label="📨 Отправить анкету", style=discord.ButtonStyle.success, custom_id="submit_anketa", row=2)
        submit_btn.callback = self.submit_callback
        self.add_item(submit_btn)

    async def mic_callback(self, interaction: discord.Interaction):
        self.mic_value = interaction.data["values"][0]
        await interaction.response.defer()

    async def team_callback(self, interaction: discord.Interaction):
        self.team_value = interaction.data["values"][0]
        await interaction.response.defer()

    async def submit_callback(self, interaction: discord.Interaction):
        if self.mic_value is None or self.team_value is None:
            await interaction.response.send_message("⚠️ Выберите ответы на оба вопроса.", ephemeral=True)
            return
        self.data["microphone"] = self.mic_value
        self.data["team_ready"] = self.team_value
        await interaction.response.defer(ephemeral=True)
        await send_application(interaction, self.data)
        self.stop()


async def send_application(interaction: discord.Interaction, data: dict):
    channel = bot.get_channel(MODERATION_CHANNEL_ID)
    if channel is None:
        await interaction.followup.send("❌ Канал не найден.", ephemeral=True)
        return

    user = interaction.user
    mic_icon = "🎙️" if data["microphone"] == "да" else "🔇"
    team_icon = "✅" if data["team_ready"] == "да" else "❌"

    embed = discord.Embed(title="📋 Новая заявка на вступление", color=discord.Color.from_rgb(88, 166, 255), timestamp=discord.utils.utcnow())
    embed.set_author(name=f"{user.display_name} ({user})", icon_url=user.display_avatar.url)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="🎮 Никнейм", value=data["nickname"], inline=True)
    embed.add_field(name="🎂 Возраст", value=str(data["age"]), inline=True)
    embed.add_field(name="⏱️ Часов в день", value=data["hours_per_day"], inline=True)
    embed.add_field(name="🔨 Баны", value=data["bans"], inline=False)
    embed.add_field(name="🏆 1 Сезон", value=data["season1"], inline=False)
    embed.add_field(name="📅 Планы на сезон", value=data["plans_season"], inline=False)
    embed.add_field(name="⚔️ Деятельность", value=data["activities"], inline=False)
    embed.add_field(name=f"{mic_icon} Микрофон", value=data["microphone"].capitalize(), inline=True)
    embed.add_field(name=f"{team_icon} Команда", value=data["team_ready"].capitalize(), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="🏘️ Гильдии на сервере", value=data["previous_guilds"], inline=False)
    embed.add_field(name="🌐 Другие проекты", value=data["other_projects"], inline=False)
    embed.add_field(name="⚔️ PvP-скилл", value=f"`{'█' * data['pvp_skill']}{'░' * (10 - data['pvp_skill'])}` **{data['pvp_skill']}/10**", inline=True)
    embed.add_field(name="🔧 Знание механик", value=f"`{'█' * data['mechanics_skill']}{'░' * (10 - data['mechanics_skill'])}` **{data['mechanics_skill']}/10**", inline=True)
    embed.set_footer(text=f"ID: {user.id}")

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    try:
        await user.send("✅ **Заявка отправлена на рассмотрение!**\nМодераторы рассмотрят её в ближайшее время.")
        notify_text = "✅ Заявка отправлена! Уведомление отправлено в ЛС."
    except discord.Forbidden:
        notify_text = "✅ Заявка отправлена на рассмотрение!"

    await interaction.followup.send(notify_text, ephemeral=True)


class ApplyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Подать заявку", style=discord.ButtonStyle.success, custom_id="open_anketa")
    async def open_anketa(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(AnketaModalPart1())


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.content.strip().lower() == "!анкета":
        embed = discord.Embed(title="📋 Анкета на вступление", description="Хотите стать частью нашего сообщества?\n\nНажмите кнопку ниже, чтобы заполнить анкету.", color=discord.Color.green())
        embed.set_footer(text="Заполните все поля честно и подробно.")
        await message.channel.send(embed=embed, view=ApplyView())


@bot.event
async def on_ready():
    bot.add_view(ApplyView())
    print(f"✅ Бот запущен как {bot.user} (ID: {bot.user.id})")
    print(f"📢 Канал для заявок: {MODERATION_CHANNEL_ID}")


bot.run(TOKEN)
