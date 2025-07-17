import asyncio
import io
import json
import random
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
from discord import Embed, Interaction
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import ReturnDocument

uri = "mongodb+srv://leon020211:leon020211@light.vu55u7q.mongodb.net/?retryWrites=true&w=majority&appName=Light"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["Light"]  # nome do banco
players = db["players"]  # coleção players
reaction_roles = db["reaction_roles"]  # coleção reaction roles
TICKET_MESSAGE_ID = None  # Salvará o ID da mensagem de criar ticket

class MeuPrimeiroBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents)
        self.TICKET_CATEGORY_NAME = "Tickets"

    async def setup_hook(self):
        await self.tree.sync()
        print("Comandos sincronizados!")

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreateTicketButton())

class CreateTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🎫 Abrir Ticket",
            style=discord.ButtonStyle.green,
            custom_id="abrir_ticket"  # Adicionado para persistência
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing:
            await interaction.response.send_message("Você já tem um ticket aberto!", ephemeral=True)
            return

        category = discord.utils.get(guild.categories, name=self.TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(self.TICKET_CATEGORY_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        staff_role = discord.utils.get(guild.roles, name="Staff")
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{member.id}",
            category=category,
            overwrites=overwrites
        )

        view = CloseTicketView(member=member)
        await channel.send(f"{member.mention}, seu ticket foi aberto!", view=view)
        await interaction.response.send_message(f"Ticket criado: {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton(member))

class CloseTicketButton(discord.ui.Button):
    def __init__(self, member):
        super().__init__(
            label="Fechar Ticket",
            style=discord.ButtonStyle.red,
            custom_id=f"fechar_ticket_{member.id}"  # Precisa ter custom_id único
        )
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.member and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Você não pode fechar este ticket.", ephemeral=True)
            return

        await interaction.channel.delete(reason=f"Ticket fechado por {interaction.user}")

bot = MeuPrimeiroBot()

@bot.event
async def on_ready():
    print(f"{bot.user} está online.")
    bot.add_view(TicketView())  # Adiciona view para o botão mesmo após reiniciar

    guild = bot.get_guild(1393796041635139614)  # Coloque seu ID de servidor
    canal = guild.get_channel(1394042647693492318)  # Coloque seu ID de canal

    if canal:
        embed = discord.Embed(
            title="🎫 Abrir Ticket de Suporte",
            description="Clique no botão abaixo para abrir um ticket com a equipe.",
            color=discord.Color.green()
        )
        await canal.send(embed=embed, view=TicketView())
    else:
        print("Canal de ticket não encontrado.")
        bot.add_view(TicketView())  # Agora é persistente e não dará erro


# Comando /soma
@bot.tree.command(name="soma", description="Some dois números distintos")
@app_commands.describe(numero1="Primeiro número a somar",
                       numero2="Segundo número a somar")
async def somar(interaction: discord.Interaction, numero1: int, numero2: int):
    resultado = numero1 + numero2
    await interaction.response.send_message(f"O número somado é {resultado}.")


# Comando /kick
@bot.tree.command(name="kick", description="Expulsa um usuário do servidor")
@app_commands.describe(user="Usuário a ser expulso")
async def kick_user(interaction: discord.Interaction, user: discord.Member):
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Você não pode expulsar/banir alguém com cargo igual ou superior ao seu.", ephemeral=True)
        return
    if not isinstance(user, discord.Member):
        await interaction.response.send_message(
            "Esse usuário não está em um servidor, portanto não pode ser expulso.",
            ephemeral=True)
        return
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            "Você não tem permissão para usar este comando.", ephemeral=True)
        return
    await user.kick()
    await interaction.response.send_message(
        f"{user.mention} foi expulso do servidor.")


# Comando /ban
@bot.tree.command(name="ban", description="Bane um usuário do servidor")
@app_commands.describe(user="Usuário a ser banido")
async def ban_user(interaction: discord.Interaction, user: discord.Member):
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Você não pode expulsar/banir alguém com cargo igual ou superior ao seu.", ephemeral=True)
        return
    if not isinstance(user, discord.Member):
        await interaction.response.send_message(
            "Esse usuário não está em um servidor, portanto não pode ser banido.",
            ephemeral=True)
        return
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "Você não tem permissão para usar este comando.", ephemeral=True)
        return
    await user.ban()
    await interaction.response.send_message(
        f"{user.mention} foi banido do servidor.")


# Comando /setrole
@bot.tree.command(name="setrole", description="Atribui um cargo a um usuário")
@app_commands.describe(user="Usuário que vai receber o cargo", cargo="Cargo a ser atribuído")
async def atribuir_cargo(interaction: discord.Interaction, user: discord.Member, cargo: discord.Role):
    # Verifica se a interação aconteceu em um servidor
    if interaction.guild is None:
        await interaction.response.send_message(
            "Este comando só pode ser usado em um servidor.", ephemeral=True)
        return

    # Verifica se o cargo a ser atribuído é maior ou igual ao cargo do bot
    if cargo >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "Não posso atribuir um cargo igual ou maior que o meu.",
            ephemeral=True)
        return

    try:
        # Atribui o cargo ao usuário
        await user.add_roles(cargo)
        await interaction.response.send_message(
            f"{user.mention} recebeu o cargo {cargo.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message(
            "Permissão insuficiente para atribuir esse cargo.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Ocorreu um erro: {e}",
                                                ephemeral=True)


#Comando /clear
@bot.tree.command(name="clear",
                  description="Limpa uma quantidade de mensagens no chat")
@app_commands.describe(amount="Número de mensagens a apagar (máx. 100)")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.guild:
        await interaction.response.send_message(
            "Este comando só pode ser usado em servidores.", ephemeral=True)
        return

    member = interaction.guild.get_member(interaction.user.id)
    if not member or not member.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "Você não tem permissão para usar este comando.", ephemeral=True)
        return

    if amount < 1 or amount > 100:
        await interaction.response.send_message(
            "O número de mensagens deve estar entre 1 e 100.", ephemeral=True)
        return

    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message(
            "Este comando só pode ser usado em canais de texto.",
            ephemeral=True)
        return

    try:
        await interaction.response.defer(ephemeral=True)  # 👈 Adicionado
        deleted = await channel.purge(limit=amount)
        await interaction.followup.send(
            f"{len(deleted)} mensagens foram apagadas com sucesso.",
            ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(
            "Não tenho permissão para apagar mensagens neste canal.",
            ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Ocorreu um erro: {e}",
                                        ephemeral=True)


# /setplayerinfo
@bot.tree.command(name="setplayerinfo", description="Register your player info")
@app_commands.describe(
    name="Your in-game name",
    fruit="Your fruit",
    level="Your level (max 625)",
    platform="Your platform (PC, Mobile, Console...)",
    style="Your fighting style (Sword, Akuma, etc.)",
    origin="How did you find the crew? (Friend, YouTube, etc.)"
)
async def set_player_info(
    interaction: discord.Interaction,
    name: str,
    fruit: str,
    level: int,
    platform: str,
    style: str,
    origin: str
):
    user_id = str(interaction.user.id)

    existing_player = players.find_one({"id": user_id})
    if existing_player:
        await interaction.response.send_message("You already registered your info. Use /editplayerinfo to update it.", ephemeral=True)
        return

    if level > 625 or level < 1:
        await interaction.response.send_message("Level must be between 1 and 625.", ephemeral=True)
        return

    players.insert_one({
        "id": user_id,
        "name": name,
        "fruit": fruit,
        "level": level,
        "platform": platform,
        "style": style,
        "origin": origin
    })

    await interaction.response.send_message("Player info saved successfully!", ephemeral=True)

# /editplayerinfo
@bot.tree.command(name="editplayerinfo", description="Edit your player info")
@app_commands.describe(
    name="New name",
    fruit="New fruit",
    level="New level (max 625)",
    platform="New platform (PC, Mobile, Console...)",
    style="New fighting style",
    origin="New origin (how you found the crew)"
)
async def edit_player_info(
    interaction: discord.Interaction,
    name: str,
    fruit: str,
    level: int,
    platform: str,
    style: str,
    origin: str
):
    user_id = str(interaction.user.id)

    existing_player = players.find_one({"id": user_id})
    if not existing_player:
        await interaction.response.send_message("You haven't registered your info yet. Use /setplayerinfo.", ephemeral=True)
        return

    if level > 625 or level < 1:
        await interaction.response.send_message("Level must be between 1 and 625.", ephemeral=True)
        return

    players.update_one(
        {"id": user_id},
        {"$set": {
            "name": name,
            "fruit": fruit,
            "level": level,
            "platform": platform,
            "style": style,
            "origin": origin
        }}
    )

    await interaction.response.send_message("Player info updated successfully!", ephemeral=True)

# /playerinfo
@bot.tree.command(name="playerinfo", description="View another player's info")
@app_commands.describe(user="User to view player info from")
async def player_info(interaction: discord.Interaction, user: discord.Member):
    user_id = str(user.id)
    data = players.find_one({"id": user_id})

    if not data:
        await interaction.response.send_message("This user has not registered their player info yet.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"{user.display_name}'s Player Info",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Name", value=data.get("name", "N/A"), inline=True)
    embed.add_field(name="Fruit", value=data.get("fruit", "N/A"), inline=True)
    embed.add_field(name="Level", value=data.get("level", "N/A"), inline=True)
    embed.add_field(name="Platform", value=data.get("platform", "N/A"), inline=True)
    embed.add_field(name="Fighting Style", value=data.get("style", "N/A"), inline=True)
    embed.add_field(name="Crew Origin", value=data.get("origin", "N/A"), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="unmute", description="Desmuta um usuário")
@app_commands.describe(user="Usuário a ser desmutado")
async def unmute(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    cargo_mute = discord.utils.get(interaction.guild.roles, name="Muted")
    if not cargo_mute:
        await interaction.response.send_message(
            "❌ O cargo 'Muted' não foi encontrado.", ephemeral=True)
        return
    try:
        await user.remove_roles(cargo_mute,
                                reason=f"Desmutado por {interaction.user}")
        await interaction.response.send_message(
            f"🔊 {user.mention} foi desmutado.")
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não tenho permissão para atribuir/remover esse cargo.",
            ephemeral=True)


@bot.tree.command(name='sorteio', description='Inicia um sorteio')
@app_commands.describe(tempo="Tempo em minutos para o sorteio",
                       premio="Prêmio do sorteio")
async def sorteio(interaction: discord.Interaction, tempo: int, premio: str):
    tempo = tempo * 60  # Converte minutos para segundos
    await interaction.response.send_message(
        f"🎉 Sorteio iniciado por {interaction.user.mention}!\n🏆 Prêmio: **{premio}**\n⏳ Tempo: {tempo} minutos\n\nReaja com 🎉 para participar!",
        ephemeral=False)

    # Envia a mensagem de participação
    mensagem = await interaction.channel.send(
        "🎉 **PARTICIPE DO SORTEIO!** 🎉\nReaja com 🎉 para entrar no sorteio!")
    await mensagem.add_reaction("🎉")

    # Espera o tempo do sorteio
    await asyncio.sleep(tempo)

    # Atualiza a mensagem para pegar as reações
    mensagem = await interaction.channel.fetch_message(mensagem.id)
    usuarios = [
        user async for user in mensagem.reactions[0].users() if not user.bot
    ]

    if not usuarios:
        await interaction.channel.send("😢 Ninguém participou do sorteio.")
    else:
        vencedor = random.choice(usuarios)
        await interaction.channel.send(
            f"🎊 Parabéns {vencedor.mention}! Você ganhou **{premio}**!")
    
@bot.tree.command(name="embed", description="Envia uma mensagem em embed com o texto que você quiser.")
@app_commands.describe(
    titulo="Título da embed (opcional)",
    descricao="Descrição ou conteúdo da embed (use \\n para pular linha)"
)
async def embed(interaction: discord.Interaction, descricao: str, titulo: str = "📌 Mensagem"):
    descricao = descricao.replace("\\n", "\n")  # <- Isso converte texto "\n" em quebra real de linha
    embed = discord.Embed(title=titulo, description=descricao, color=discord.Color.blue())
    embed.set_footer(text=f"Enviado por {interaction.user.name}")
    await interaction.response.send_message(embed=embed)

# No comando /set_reaction_role e nos eventos, use a coleção reaction_roles (MongoDB)

@bot.tree.command(name="setreactionrole", description="Create a reaction role message")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="Channel to send the reaction role message",
    message="Message content",
    emoji="Emoji to react with",
    role="Role to assign when reacted"
)
async def set_reaction_role(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    emoji: str,
    role: discord.Role
):
    sent_message = await channel.send(message)
    await sent_message.add_reaction(emoji)

    # Salva no MongoDB
    reaction_roles.insert_one({
        "message_id": sent_message.id,
        "channel_id": channel.id,
        "emoji": emoji,
        "role_id": role.id
    })

    await interaction.response.send_message("Reaction role message sent and saved!", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member and payload.member.bot:
        return

    entry = reaction_roles.find_one({
        "message_id": payload.message_id,
        "emoji": str(payload.emoji)
    })

    if entry:
        guild = bot.get_guild(payload.guild_id)
        role = guild.get_role(entry["role_id"]) if guild else None
        member = guild.get_member(payload.user_id) if guild else None
        if role and member:
            await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    entry = reaction_roles.find_one({
        "message_id": payload.message_id,
        "emoji": str(payload.emoji)
    })

    if entry:
        guild = bot.get_guild(payload.guild_id)
        role = guild.get_role(entry["role_id"]) if guild else None
        member = guild.get_member(payload.user_id) if guild else None
        if role and member:
            await member.remove_roles(role)

@set_reaction_role.error
async def set_reaction_role_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You need to be an administrator to use this command!", ephemeral=True)

# Token do bot
bot.run(os.getenv("DISCORD_TOKEN"))

