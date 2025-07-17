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
from keep_alive import keep_alive
from tinydb import TinyDB, Query
from tinydb.operations import set

DATA_FILE = "players_db.json"
REACTION_FILE = "reaction_roles_db.json"

players_db = TinyDB(DATA_FILE)
reaction_roles_db = TinyDB(REACTION_FILE)

reaction_db = TinyDB("reaction_db.json")

Player = Query()

class MeuPrimeiroBot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.ticket_message_id = None  # inicializa aqui

    async def setup_hook(self):
        await self.tree.sync()

async def on_ready(self):
        print(f"O Bot {self.user} foi ligado com sucesso.")
        guild = self.get_guild(1393796041635139614)
        if not guild:
            print("Guilda não encontrada")
            return
        canal = guild.get_channel(1394042647693492318)
        if not canal:
            print("Canal não encontrado")
            return

        # Envia ou pega mensagem do ticket
        # Se quiser mandar só 1x, faça um controle para evitar spam
        embed = discord.Embed(
            title="🎫 Abrir Ticket de Suporte",
            description="Clique no emoji 🎫 abaixo para abrir um ticket com a Staff.",
            color=discord.Color.green()
        )
        msg = await canal.send(embed=embed)
        await msg.add_reaction("🎫")
        self.ticket_message_id = msg.id

        # Cria categoria Tickets se não existir
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            try:
                category = await guild.create_category("Tickets")
                print("Categoria Tickets criada.")
            except Exception as e:
                print(f"Erro criando categoria Tickets: {e}")

async def on_raw_reaction_add(self, payload):
        # Ignora bots
        if payload.user_id == self.user.id:
            return

        # Só reage se for a mensagem do ticket e emoji correto
        if payload.message_id == self.ticket_message_id and str(payload.emoji) == "🎫":
            guild = self.get_guild(payload.guild_id)
            if not guild:
                return
            member = guild.get_member(payload.user_id)
            if not member:
                return

            # Checa se já tem canal aberto
            existing_channel = discord.utils.get(guild.channels, name=f"ticket-{member.name.lower()}")
            if existing_channel:
                try:
                    await member.send("Você já tem um ticket aberto!")
                except:
                    pass
                return

            # Pega categoria Tickets
            category = discord.utils.get(guild.categories, name="Tickets")
            if not category:
                # Se não tiver, cria
                category = await guild.create_category("Tickets")

            # Permissões
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                discord.utils.get(guild.roles, name="Staff"): discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # Cria canal
            channel = await guild.create_text_channel(f"ticket-{member.name}", category=category, overwrites=overwrites)

            # Cria botão fechar ticket
            close_button = discord.ui.Button(label="Fechar ticket", style=discord.ButtonStyle.red)

            async def close_callback(interaction: discord.Interaction):
                if interaction.user != member and not interaction.user.guild_permissions.manage_channels:
                    await interaction.response.send_message("Você não pode fechar este ticket.", ephemeral=True)
                    return
                await channel.delete(reason=f"Ticket fechado por {interaction.user}")

            close_button.callback = close_callback
            view = discord.ui.View()
            view.add_item(close_button)

            await channel.send(f"{member.mention} seu ticket foi aberto! Um staff irá te ajudar em breve.", view=view)




async def on_member_join(self, member: discord.Member):
    print(f"Novo membro entrou: {member}")

    canal_id = 1393807069999530084  # Canal fixo de boas-vindas
    canal = member.guild.get_channel(canal_id)
    print(f"Canal obtido: {canal}")

    if canal is None:
        print(f"Canal com ID {canal_id} não encontrado no servidor {member.guild.name}")
    else:
        if isinstance(canal, discord.TextChannel):
            try:
                await canal.send(f"👋 Seja bem-vindo(a) ao servidor, {member.mention}!")
                print(f"Mensagem de boas-vindas enviada para {member.name}")
            except Exception as e:
                print(f"Erro ao enviar mensagem no canal de boas-vindas: {e}")

    cargo = discord.utils.get(member.guild.roles, name="Visitant")
    if cargo:
        try:
            await member.add_roles(cargo)
            print(f"{member} recebeu o cargo {cargo.name} automaticamente.")
        except Exception as e:
            print(f"Erro ao adicionar cargo: {e}")

# Instancia o bot
bot = MeuPrimeiroBot()

def load_players():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_players(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_reactions():
    if os.path.exists(REACTION_FILE):
        with open(REACTION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_reactions(data):
    with open(REACTION_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Comando /soma
@bot.tree.command(name="soma", description="Some dois números distintos")
@app_commands.describe(numero1="Primeiro número a somar",
                       numero2="Segundo número a somar")
await interaction.response.defer(thinking=True, ephemeral=True)
async def somar(interaction: discord.Interaction, numero1: int, numero2: int):
    resultado = numero1 + numero2
    await interaction.response.send_message(f"O número somado é {resultado}.")


# Comando /kick
@bot.tree.command(name="kick", description="Expulsa um usuário do servidor")
@app_commands.describe(user="Usuário a ser expulso")
await interaction.response.defer(thinking=True, ephemeral=True)
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
@app_commands.describe(user="Usuário que vai receber o cargo",
                       cargo="Cargo a ser atribuído")
await interaction.response.defer(thinking=True, ephemeral=True)
async def atribuir_cargo(interaction: discord.Interaction,
                         user: discord.Member, cargo: discord.Role):
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
await interaction.response.defer(thinking=True, ephemeral=True)
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
await interaction.response.defer(thinking=True, ephemeral=True)
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

    if players_db.contains(Player.id == user_id):
        await interaction.response.send_message("You already registered your info. Use /editplayerinfo to update it.", ephemeral=True)
        return

    if level > 625 or level < 1:
        await interaction.response.send_message("Level must be between 1 and 625.", ephemeral=True)
        return

    players_db.insert({
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
await interaction.response.defer(thinking=True, ephemeral=True)
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

    if not players_db.contains(Player.id == user_id):
        await interaction.response.send_message("You haven't registered your info yet. Use /setplayerinfo.", ephemeral=True)
        return

    if level > 625 or level < 1:
        await interaction.response.send_message("Level must be between 1 and 625.", ephemeral=True)
        return

    players_db.update({
        "name": name,
        "fruit": fruit,
        "level": level,
        "platform": platform,
        "style": style,
        "origin": origin
    }, Player.id == user_id)

    await interaction.response.send_message("Player info updated successfully!", ephemeral=True)

# /playerinfo
@bot.tree.command(name="playerinfo", description="View another player's info")
@app_commands.describe(user="User to view player info from")
async def player_info(interaction: discord.Interaction, user: discord.Member):
    user_id = str(user.id)
    data = players_db.get(Player.id == user_id)

    if not data:
        await interaction.response.send_message("This user has not registered their player info yet.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"{user.display_name}'s Player Info",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Name", value=data["name"], inline=True)
    embed.add_field(name="Fruit", value=data["fruit"], inline=True)
    embed.add_field(name="Level", value=data["level"], inline=True)
    embed.add_field(name="Platform", value=data["platform"], inline=True)
    embed.add_field(name="Fighting Style", value=data["style"], inline=True)
    embed.add_field(name="Crew Origin", value=data["origin"], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="recruit", description="chama os recrutadores")
await interaction.response.defer(thinking=True, ephemeral=True)
async def recruit(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"@RECRUTADOR, {interaction.user.mention} quer se juntar a tripulação!",
        ephemeral=False)

@bot.tree.command(name="mute", description="Muta um usuário")
@app_commands.describe(user="Usuário a ser mutado",
                       tempo="Tempo de mute em minutos")
await interaction.response.defer(thinking=True, ephemeral=True)
async def mute(interaction: discord.Interaction, user: discord.Member,
               tempo: int):
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
        await user.add_roles(
            cargo_mute,
            reason=f"Mutado por {tempo} minutos por {interaction.user}")
        await interaction.response.send_message(
            f"🔇 {user.mention} foi mutado por {tempo} minutos.")
        await asyncio.sleep(tempo * 60)
        await user.remove_roles(cargo_mute, reason="Tempo de mute expirado")
        await interaction.followup.send(
            f"🔊 {user.mention} foi desmutado automaticamente.")
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não tenho permissão para atribuir/remover esse cargo.",
            ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ocorreu um erro: {e}",
                                                ephemeral=True)


@bot.tree.command(name="unmute", description="Desmuta um usuário")
await interaction.response.defer(thinking=True, ephemeral=True)
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

# No comando /set_reaction_role e nos eventos, use reaction_roles_db, por exemplo:

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

    # Salva no banco correto
    reaction_roles_db.insert({
        "message_id": sent_message.id,
        "channel_id": channel.id,
        "emoji": emoji,
        "role_id": role.id
    })

    await interaction.response.send_message("Reaction role message sent and saved!", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        return

    for entry in reaction_db:
        if (entry["message_id"] == payload.message_id and entry["emoji"] == str(payload.emoji)):
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(entry["role_id"])
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.add_roles(role)
            break

@bot.event
async def on_raw_reaction_remove(payload):
    for entry in reaction_db:
        if (entry["message_id"] == payload.message_id and entry["emoji"] == str(payload.emoji)):
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(entry["role_id"])
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.remove_roles(role)
            break

@set_reaction_role.error
async def set_reaction_role_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You need to be an administrator to use this command!", ephemeral=True)

keep_alive()

# Token do bot
bot.run(os.getenv("DISCORD_TOKEN"))
