import discord
from discord import app_commands, Activity, ActivityType
from discord.ext import commands
from discord.ui import View, Button
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import random
import json
import os

# ---------------- CONFIG ----------------
TOKEN = "MTQ3MDAxMzEyNzI1MTk4ODcyNg.G5NQh8.qb6zMvHr5Y_q_vt2NzeTczBljqWY8KXM3moEbg"
GUILD_ID = 1424272770866614284

# VIP Auto-react
VIP_USER_IDS = [1372185084408627252, 1284827960452583457]
REACTION_EMOJI = "🦢"

# Giveaway
GIVEAWAY_ROLE_ID = 1470407858301698088
GIVEAWAY_CHANNEL_ID = 1424274109373747250

# Auto-image
AUTO_IMAGE_CHANNEL_ID = 1424272771722252409
AUTO_IMAGE_URL = "https://media.discordapp.net/attachments/1424274109373747250/1475476460646043688/divider.webp"

# Host command
HOST_ROLE_ID = 1470409748351422609
FARMING_CHANNEL_ID = 1470021596877164688
FAIR_CHANNEL_ID = 1470021635082817701

# Outfit of the Week
OOTW_CHANNEL_ID = 1475575043911057479

# Level system
LEVEL_CHANNEL_ID = 1475487411109892096
DATA_FILE = "levels.json"

# Currency system
CURRENCY_FILE = "moons.json"
SHOP_ITEMS = {
    "Pink Role": 100,
    "Blue Role": 200,
    "Gold Role": 500
}
ADMIN_ROLE_ID = 1475159178686234775

# Application system
APPLICATIONS_CHANNEL_ID = 1470769330164732149
STAFF_ROLE_ID           = 1475135854132461769

# ---------------- BOT SETUP ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- LEVEL DATA ----------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_levels():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_levels(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def xp_required(level):
    return 100 + (level * 50)

# ---------------- CURRENCY DATA ----------------
if not os.path.exists(CURRENCY_FILE):
    with open(CURRENCY_FILE, "w") as f:
        json.dump({}, f)

def load_currency():
    with open(CURRENCY_FILE, "r") as f:
        return json.load(f)

def save_currency(data):
    with open(CURRENCY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- APPLICATION SYSTEM ----------------
QUESTIONS = {
    "staff": [
        "What is your age?",
        "What is your timezone?",
        "How much experience do you have moderating Discord servers?",
        "Why do you want to be a moderator at Luna's Fashion?",
        "How many hours a week can you dedicate?",
        "Do you have any previous staff experience? If so, explain.",
        "Any additional information?",
    ],
    "outfit_uploader": [
        "What is your age?",
        "What is your Roblox username?",
        "How often do you plan on uploading outfits?",
        "What style of outfits do you specialize in?",
        "Do you have examples of outfits you've made? If so, share links or describe them.",
        "Why do you want to be an Outfit Uploader at Luna's Fashion?",
        "Any additional information?",
    ],
    "designer": [
        "What is your age?",
        "What is your Roblox username?",
        "What design software or tools do you use?",
        "Why do you want to be a designer at Luna's Fashion?",
        "Do you have a portfolio or examples of your work?",
        "How long have you been designing?",
        "Any additional information?",
    ],
}

APP_COLORS = {
    "staff":           discord.Color.from_rgb(114, 137, 218),
    "outfit_uploader": discord.Color.from_rgb(255, 182, 193),
    "designer":        discord.Color.from_rgb(138, 43, 226),
}

APP_TITLES = {
    "staff":           "🛡️ Staff / Moderator Application",
    "outfit_uploader": "👗 Outfit Uploader Application",
    "designer":        "🎨 Designer Application",
}

active_applicants = set()


async def run_application(interaction: discord.Interaction, role: str):
    user = interaction.user

    if user.id in active_applicants:
        await interaction.response.send_message(
            "You already have an application in progress! Check your DMs.", ephemeral=True
        )
        return

    active_applicants.add(user.id)
    await interaction.response.send_message(
        f"📬 Check your DMs! Your **{APP_TITLES[role]}** has started.", ephemeral=True
    )

    answers = []
    questions = QUESTIONS[role]

    try:
        dm = await user.create_dm()
        await dm.send(
            embed=discord.Embed(
                title=f"Starting: {APP_TITLES[role]}",
                description="Answer each question by typing in this DM.\nYou have **2 minutes** per question. Type `cancel` to cancel.",
                color=APP_COLORS[role],
            )
        )

        for i, question in enumerate(questions, 1):
            await dm.send(f"**Question {i}/{len(questions)}**\n{question}")

            def check(m):
                return m.author == user and isinstance(m.channel, discord.DMChannel)

            try:
                msg = await bot.wait_for("message", check=check, timeout=120)
            except asyncio.TimeoutError:
                await dm.send("⏰ Application timed out. Feel free to apply again!")
                active_applicants.discard(user.id)
                return

            if msg.content.lower() == "cancel":
                await dm.send("❌ Application cancelled.")
                active_applicants.discard(user.id)
                return

            answers.append(msg.content)

        result_embed = discord.Embed(
            title=f"New Application — {APP_TITLES[role]}",
            color=APP_COLORS[role],
        )
        result_embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        result_embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=False)

        for i, (q, a) in enumerate(zip(questions, answers), 1):
            result_embed.add_field(name=f"Q{i}: {q}", value=a or "No answer", inline=False)

        result_embed.set_footer(text=f"Role: {role.replace('_', ' ').capitalize()}")

        class ReviewView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success, custom_id=f"accept_{user.id}_{role}")
            async def accept(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                staff_role = btn_interaction.guild.get_role(STAFF_ROLE_ID)
                if staff_role not in btn_interaction.user.roles:
                    await btn_interaction.response.send_message("You don't have permission to do this.", ephemeral=True)
                    return
                result_embed.color = discord.Color.green()
                result_embed.add_field(name="Decision", value=f"✅ Accepted by {btn_interaction.user.mention}", inline=False)
                for child in self.children:
                    child.disabled = True
                await btn_interaction.message.edit(embed=result_embed, view=self)
                try:
                    await user.send(embed=discord.Embed(
                        title="Application Accepted! 🎉",
                        description=f"Congratulations! Your **{APP_TITLES[role]}** has been **accepted**!",
                        color=discord.Color.green()
                    ))
                except:
                    pass
                await btn_interaction.response.send_message("Accepted!", ephemeral=True)

            @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger, custom_id=f"deny_{user.id}_{role}")
            async def deny(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                staff_role = btn_interaction.guild.get_role(STAFF_ROLE_ID)
                if staff_role not in btn_interaction.user.roles:
                    await btn_interaction.response.send_message("You don't have permission to do this.", ephemeral=True)
                    return
                result_embed.color = discord.Color.red()
                result_embed.add_field(name="Decision", value=f"❌ Denied by {btn_interaction.user.mention}", inline=False)
                for child in self.children:
                    child.disabled = True
                await btn_interaction.message.edit(embed=result_embed, view=self)
                try:
                    await user.send(embed=discord.Embed(
                        title="Application Update",
                        description=f"Thank you for applying for **{APP_TITLES[role]}**. Unfortunately your application was **not accepted** this time. Feel free to apply again in the future!",
                        color=discord.Color.red()
                    ))
                except:
                    pass
                await btn_interaction.response.send_message("Denied.", ephemeral=True)

        apps_channel = bot.get_channel(APPLICATIONS_CHANNEL_ID)
        await apps_channel.send(embed=result_embed, view=ReviewView())
        await dm.send(embed=discord.Embed(
            title="✅ Application Submitted!",
            description="Your application has been sent to the team. We'll be in touch!",
            color=APP_COLORS[role]
        ))

    except discord.Forbidden:
        await interaction.followup.send("❌ I couldn't DM you! Please enable DMs from server members.", ephemeral=True)

    active_applicants.discard(user.id)

# ---------------- STATUS & READY ----------------
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user}")

    async def keep_status():
        while True:
            await bot.change_presence(
                activity=Activity(type=ActivityType.listening, name="Enjoying the Fashion Cafe ☕")
            )
            await asyncio.sleep(300)

    bot.loop.create_task(keep_status())

# ---------------- AUTO-REACT, AUTO-IMAGE & XP ----------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in VIP_USER_IDS:
        await message.add_reaction(REACTION_EMOJI)

    if message.channel.id == AUTO_IMAGE_CHANNEL_ID:
        await message.channel.send(AUTO_IMAGE_URL)

    levels = load_levels()
    uid = str(message.author.id)
    if uid not in levels:
        levels[uid] = {"xp": 0, "level": 1}

    gain = random.randint(5, 15)
    levels[uid]["xp"] += gain
    cur_level = levels[uid]["level"]
    req = xp_required(cur_level)
    if levels[uid]["xp"] >= req:
        levels[uid]["xp"] = 0
        levels[uid]["level"] += 1
        ch = bot.get_channel(LEVEL_CHANNEL_ID)
        if ch:
            await ch.send(f"✨ {message.author.mention} leveled up to **Level {levels[uid]['level']}**! Keep slaying 💖")
    save_levels(levels)

    await bot.process_commands(message)

# ---------------- RANK COMMAND ----------------
@bot.tree.command(name="rank", description="Check your level!", guild=discord.Object(id=GUILD_ID))
async def rank(interaction: discord.Interaction):
    levels = load_levels()
    uid = str(interaction.user.id)
    level = levels.get(uid, {"level": 1, "xp": 0})["level"]
    xp = levels.get(uid, {"level": 1, "xp": 0})["xp"]
    required = xp_required(level)
    embed = discord.Embed(
        title="💖 Your Rank",
        description=f"Level: **{level}**\nXP: **{xp}/{required}**",
        color=discord.Color.pink()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------- SHOP COMMAND ----------------
@bot.tree.command(name="shop", description="Buy items with Moons!", guild=discord.Object(id=GUILD_ID))
async def shop(interaction: discord.Interaction):
    moons_data = load_currency()
    uid = str(interaction.user.id)
    balance = moons_data.get(uid, {"moons": 0})["moons"]
    description = "\n".join([f"**{item}**: {cost} Moons" for item, cost in SHOP_ITEMS.items()])
    embed = discord.Embed(
        title="🛍️ Shop",
        description=f"Your balance: **{balance} Moons**\n\n{description}",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------- GIVEAWAY COMMAND ----------------
@bot.tree.command(name="giveaway", description="Start a giveaway! 🎉", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(prize="Prize", duration="Duration in seconds")
async def giveaway(interaction: discord.Interaction, prize: str, duration: int):
    if not any(role.id == GIVEAWAY_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ No permission!", ephemeral=True)
        return
    channel = bot.get_channel(GIVEAWAY_CHANNEL_ID)
    embed = discord.Embed(
        title="🎉 Giveaway 🎉",
        description=f"Prize: **{prize}**\nReact with 🎁 to enter!",
        color=discord.Color.purple()
    )
    msg = await channel.send(embed=embed)
    await msg.add_reaction("🎁")
    await interaction.response.send_message("✅ Giveaway started!", ephemeral=True)
    await asyncio.sleep(duration)
    msg = await channel.fetch_message(msg.id)
    users = [u async for u in msg.reactions[0].users() if not u.bot]
    if users:
        winner = random.choice(users)
        await channel.send(f"🎉 {winner.mention} won **{prize}**!")
    else:
        await channel.send("No one entered 😢")

# ---------------- HOST COMMAND ----------------
@bot.tree.command(name="host", description="Host a server!", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(type="farming or fair", link="Server link")
async def host(interaction: discord.Interaction, type: str, link: str):
    if not any(role.id == HOST_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ No permission!", ephemeral=True)
        return
    type_lower = type.lower()
    if type_lower == "farming":
        channel = bot.get_channel(FARMING_CHANNEL_ID)
        title = "🌾 Farming Server Hosted!"
        color = discord.Color.green()
    elif type_lower == "fair":
        channel = bot.get_channel(FAIR_CHANNEL_ID)
        title = "🎡 Fair Server Hosted!"
        color = discord.Color.orange()
    else:
        await interaction.response.send_message("❌ Use farming or fair.", ephemeral=True)
        return
    embed = discord.Embed(title=title, description=f"Link: {link}", color=color)
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Server hosted!", ephemeral=True)

# ---------------- OOTW ENTER ----------------
votes = defaultdict(dict)

class RatingView(View):
    def __init__(self, msg, max_stars=5):
        super().__init__(timeout=None)
        self.msg = msg
        self.max_stars = max_stars
        for i in range(1, max_stars + 1):
            button = Button(label=str(i), style=discord.ButtonStyle.primary)
            button.callback = self.make_callback(i)
            self.add_item(button)

    def make_callback(self, stars):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id in votes[self.msg.id]:
                await interaction.response.send_message("❌ Already voted!", ephemeral=True)
                return
            votes[self.msg.id][interaction.user.id] = stars
            avg = sum(votes[self.msg.id].values()) / len(votes[self.msg.id])
            embed = self.msg.embeds[0]
            embed.set_footer(text=f"⭐ {avg:.1f}/5")
            await self.msg.edit(embed=embed, view=self)
            await interaction.response.send_message(f"✅ You voted {stars} star(s)!", ephemeral=True)
        return callback

@bot.tree.command(name="enter", description="Enter Outfit of the Week!", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(roblox="Roblox username", discord_user="Discord name", image="Image URL")
async def enter(interaction: discord.Interaction, roblox: str, discord_user: str, image: str):
    channel = bot.get_channel(OOTW_CHANNEL_ID)
    embed = discord.Embed(
        title=f"OOTW Entry by {discord_user}",
        description=f"Roblox: {roblox}",
        color=discord.Color.purple()
    )
    embed.set_image(url=image)
    embed.set_footer(text="⭐ 0.0/5")
    msg = await channel.send(embed=embed)
    view = RatingView(msg)
    await msg.edit(view=view)
    await interaction.response.send_message("✅ OOTW entry posted!", ephemeral=True)

# ---------------- GIVE MOONS (ADMIN) ----------------
@bot.tree.command(name="givemoons", description="Give Moons to a user (admin only)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User to give Moons to", amount="Amount of Moons")
async def givemoons(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be > 0!", ephemeral=True)
        return
    uid = str(user.id)
    data = load_currency()
    if uid not in data:
        data[uid] = {"moons": 0}
    data[uid]["moons"] += amount
    save_currency(data)
    await interaction.response.send_message(f"✅ Gave {amount} Moons to {user.mention}!", ephemeral=True)

# ---------------- APPLICATION PANEL COMMAND ----------------
@bot.tree.command(name="panel", description="Post the application panel", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
async def panel(interaction: discord.Interaction):

    staff_embed = discord.Embed(
        title="🛡️ Staff / Moderator",
        description="Want to help keep Luna's Fashion safe and running smoothly? Apply to join our moderation team!",
        color=APP_COLORS["staff"]
    )
    outfit_embed = discord.Embed(
        title="👗 Outfit Uploader",
        description="Got a great sense of style? Apply to become an Outfit Uploader and share your looks with the community!",
        color=APP_COLORS["outfit_uploader"]
    )
    designer_embed = discord.Embed(
        title="🎨 Designer",
        description="Got a creative eye for fashion? Apply to join our design team and bring your vision to life!",
        color=APP_COLORS["designer"]
    )

    class StaffButton(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)
        @discord.ui.button(label="Apply for Staff", style=discord.ButtonStyle.blurple, custom_id="apply_staff")
        async def apply(self, i: discord.Interaction, b: discord.ui.Button):
            await run_application(i, "staff")

    class OutfitButton(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)
        @discord.ui.button(label="Apply for Outfit Uploader", style=discord.ButtonStyle.blurple, custom_id="apply_outfit_uploader")
        async def apply(self, i: discord.Interaction, b: discord.ui.Button):
            await run_application(i, "outfit_uploader")

    class DesignerButton(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)
        @discord.ui.button(label="Apply for Designer", style=discord.ButtonStyle.blurple, custom_id="apply_designer")
        async def apply(self, i: discord.Interaction, b: discord.ui.Button):
            await run_application(i, "designer")

    await interaction.channel.send(embed=staff_embed, view=StaffButton())
    await interaction.channel.send(embed=outfit_embed, view=OutfitButton())
    await interaction.channel.send(embed=designer_embed, view=DesignerButton())
    await interaction.response.send_message("✅ Panel posted!", ephemeral=True)

# ---------------- RUN BOT ----------------
bot.run(TOKEN)