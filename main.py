import discord
import os
from discord.ui import Button, View, Modal, TextInput, Select

TOKEN = os.environ["TOKEN"]
MODERATION_CHANNEL_ID = int(os.environ["MODERATION_CHANNEL_ID"])
APPLY_CHANNEL_ID = int(os.environ["APPLY_CHANNEL_ID"])

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)


class AnketaModal(Modal, title="Анкета на вступление"):
    nickname = TextInput(label="1. Никнейм в игре", style=discord.TextStyle.short, required=True, max_length=64)
    age = TextInput(label="2. Возраст", style=discord.TextStyle.short, required=True, max_length=3)
    hours_per_day = TextInput(label="3. Часов в день на сервер?", style=discord.TextStyle.short, required=True, max_length=50)
    bans = TextInput(label="4. Были баны? Если да — за что?", style=discord.TextStyle.paragraph, required=True, max_length=500)
    plans = TextInput(label="5. Планы и чем займётесь на сервере?", style=discord.TextStyle.paragraph, required=True, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age_val = int(self.age.value.strip())
            if not (1 <= age_val <= 120):
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Возраст: введите целое число.", ephemeral=True)
            return

        data = {
            "nickname": self.nickname.value,
            "age": age_val,
            "hours_per_day": self.hours_per_day.value,
            "bans": self.bans.value,
            "plans": self.plans.value,
        }
        view = Part2View(data)
        await interaction.response.send_message(
            "📋 **Часть 2 из 2** — выберите все пункты (заявка отправится автоматически после последнего выбора):",
            view=view,
            ephemeral=True,
        )


class Part2View(View):
    def __init__(self, data: dict):
        super().__init__(timeout=300)
        self.data = data
        self.mic_value = None
        self.team_value = None
        self.pvp_value = None
        self.experience_value = None

        mic_select = Select(placeholder="🎙️ Наличие микрофона", options=[
            discord.SelectOption(label="Да", value="да", emoji="🎙️"),
            discord.SelectOption(label="Нет", value="нет", emoji="🔇"),
        ], row=0)
        mic_select.callback = self.mic_callback
        self.add_item(mic_select)

        team_select = Select(placeholder="🤝 Готовы играть в команде?", options=[
            discord.SelectOption(label="Да", value="да", emoji="🤝"),
            discord.SelectOption(label="Нет", value="нет", emoji="🚫"),
        ], row=1)
        team_select.callback = self.team_callback
        self.add_item(team_select)

        pvp_select = Select(placeholder="⚔️ PvP-скилл и знание механик (1-10)", options=[
            discord.SelectOption(label=f"PvP: {i}, Механики: {i}", value=str(i)) for i in range(1, 11)
        ], row=2)
        pvp_select.callback = self.pvp_callback
        self.add_item(pvp_select)

        experience_select = Select(placeholder="🕐 Сколько времени на сервере?", options=[
            discord.SelectOption(label="Только зашёл", value="Только зашёл", emoji="🆕"),
            discord.SelectOption(label="Меньше недели", value="Меньше недели", emoji="📅"),
            discord.SelectOption(label="1–2 недели", value="1–2 недели", emoji="📆"),
            discord.SelectOption(label="1 месяц", value="1 месяц", emoji="🗓️"),
            discord.SelectOption(label="Несколько месяцев", value="Несколько месяцев", emoji="⏳"),
            discord.SelectOption(label="С 1 сезона", value="С 1 сезона", emoji="👑"),
        ], row=3)
        experience_select.callback = self.experience_callback
        self.add_item(experience_select)

    async def mic_callback(self, interaction: discord.Interaction):
        self.mic_value = interaction.data["values"][0]
        await interaction.response.defer()
        await self.check_complete(interaction)

    async def team_callback(self, interaction: discord.Interaction):
        self.team_value = interaction.data["values"][0]
        await interaction.response.defer()
        await self.check_complete(interaction)

    async def pvp_callback(self, interaction: discord.Interaction):
        self.pvp_value = int(interaction.data["values"][0])
        await interaction.response.defer()
        await self.check_complete(interaction)

    async def experience_callback(self, interaction: discord.Interaction):
        self.experience_value = interaction.data["values"][0]
        await interaction.response.defer()
        await self.check_complete(interaction)

    async def check_complete(self, interaction: discord.Interaction):
        if None in (self.mic_value, self.team_value, self.pvp_value, self.experience_value):
            return
        self.data["microphone"] = self.mic_value
        self.data["team_ready"] = self.team_value
        self.data["pvp_skill"] = self.pvp_value
        self.data["mechanics_skill"] = self.pvp_value
        self.data["experience"] = self.experience_value
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

    embed = discord.Embed(
        title="📋 Новая заявка на вступление",
        color=discord.Color.from_rgb(88, 166, 255),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=f"{user.display_name} ({user})", icon_url=user.display_avatar.url)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="🎮 Никнейм", value=data["nickname"], inline=True)
    embed.add_field(name="🎂 Возраст", value=str(data["age"]), inline=True)
    embed.add_field(name="⏱️ Часов в день", value=data["hours_per_day"], inline=True)
    embed.add_field(name="🔨 Баны", value=data["bans"], inline=False)
    embed.add_field(name="📅 Планы и деятельность", value=data["plans"], inline=False)
    embed.add_field(name="🕐 Опыт на сервере", value=data["experience"], inline=False)
    embed.add_field(name=f"{mic_icon} Микрофон", value=data["microphone"].capitalize(), inline=True)
    embed.add_field(name=f"{team_icon} Команда", value=data["team_ready"].capitalize(), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="⚔️ PvP-скилл", value=f"`{'█' * data['pvp_skill']}{'░' * (10 - data['pvp_skill'])}` **{data['pvp_skill']}/10**", inline=True)
    embed.add_field(name="🔧 Механики", value=f"`{'█' * data['mechanics_skill']}{'░' * (10 - data['mechanics_skill'])}` **{data['mechanics_skill']}/10**", inline=True)
    embed.set_footer(text=f"ID: {user.id}")

    await channel.send("@Житель новая заявка!")
    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    try:
        await user.send("✅ **Заявка отправлена!** Модераторы рассмотрят её в ближайшее время.")
        notify_text = "✅ Заявка отправлена! Уведомление отправлено в ЛС."
    except discord.Forbidden:
        notify_text = "✅ Заявка отправлена на рассмотрение!"

    await interaction.followup.send(notify_text, ephemeral=True)


class ApplyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Подать заявку", style=discord.ButtonStyle.success, custom_id="open_anketa")
    async def open_anketa(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(AnketaModal())


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.content.strip().lower() == "!анкета":
        embed = discord.Embed(
            title="📋 Анкета на вступление",
            description="Хотите стать частью нашего сообщества?\n\nНажмите кнопку ниже, чтобы заполнить анкету.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Заполните все поля честно и подробно.")
        await message.channel.send(embed=embed, view=ApplyView())


@bot.event
async def on_ready():
    bot.add_view(ApplyView())
    print(f"✅ Бот запущен как {bot.user} (ID: {bot.user.id})")
    print(f"📢 Канал для заявок: {MODERATION_CHANNEL_ID}")

    channel = bot.get_channel(APPLY_CHANNEL_ID)
    if channel:
        async for msg in channel.history(limit=20):
            if msg.author == bot.user:
                return
        embed = discord.Embed(
            title="📋 Анкета на вступление",
            description="Хотите стать частью нашего сообщества?\n\nНажмите кнопку ниже, чтобы заполнить анкету.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Заполните все поля честно и подробно.")
        await channel.send(embed=embed, view=ApplyView())


bot.run(TOKEN)
