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

# Cria ou abre o arquivo de banco de dados
db = TinyDB("database.json")

# Caminho do arquivo de dados
DATA_FILE = "players.json"
REACTION_FILE = "reaction_roles.json"

# Funções utilitárias para JSON


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


player_data = load_data()



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
        canal = guild.get_channel(1394042647693492318)
        embed = discord.Embed(
            title="🎫 Abrir Ticket de Suporte",
            description="Clique no emoji 🎫 abaixo para abrir um ticket com a Staff.",
            color=discord.Color.green()
        )
        msg = await canal.send(embed=embed)
        await msg.add_reaction("🎫")
        self.ticket_message_id = msg.id  # salva para usar no evento

        # Verifica se existe uma categoria para os tickets
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            # Se não existir, tenta criar a categoria
            try:
                print("Categoria 'Tickets' não encontrada. Criando...")
                category = await guild.create_category("Tickets")
                print("Categoria 'Tickets' criada com sucesso!")
            except discord.Forbidden:
                print("O bot não tem permissão para criar a categoria 'Tickets'.")
                return
            except Exception as e:
                print(f"Erro ao criar a categoria 'Tickets': {e}")
                return

        # Define permissões para o canal do ticket
        staff_role = discord.utils.get(guild.roles, name="Staff")
        if not staff_role:
            print("Cargo 'Staff' não encontrado!")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Adiciona o botão para fechar o ticket
        close_button = discord.ui.Button(label="Fechar ticket", style=discord.ButtonStyle.red)

        async def close_callback(interaction: discord.Interaction):
            await channel.delete(reason=f"Ticket fechado por {interaction.user}")

        close_button.callback = close_callback
        view = discord.ui.View()
        view.add_item(close_button)

        # Envia mensagem de boas-vindas no canal do ticket
        try:
            await channel.send(f"{member.mention} Obrigado por abrir o ticket! Um membro da staff irá te atender em breve.", view=view)
            print(f"Mensagem de boas-vindas enviada para {member.mention} no canal {channel_name}")
        except Exception as e:
            print(f"Erro ao enviar mensagem no canal do ticket: {e}")



    async def on_member_join(self, member: discord.Member):
        print(f"Novo membro entrou: {member}")

        canal_id = 1393807069999530084
        canal = member.guild.get_channel(canal_id)
        print(f"Canal obtido: {canal}")

        if canal is None:
            print(f"Canal com ID {canal_id} não encontrado no servidor {member.guild.name}")
            return

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
@app_commands.describe(user="Usuário que vai receber o cargo",
                       cargo="Cargo a ser atribuído")
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

# Comando /setplayerinfo
@bot.tree.command(name="setplayerinfo",
                  description="Define suas informações de jogador")
@app_commands.describe(nome="Seu nome",
                       fruta="Sua fruta",
                       level="Seu nível (até 625)")
async def set_player_info(interaction: discord.Interaction, nome: str,
                          fruta: str, level: int):
    user_id = str(interaction.user.id)
    if user_id in player_data:
        await interaction.response.send_message(
            "Você já cadastrou suas informações. Use /editarplayerinfo para atualizar.",
            ephemeral=True)
        return
    if level > 625 or level < 1:
        await interaction.response.send_message(
            "O nível deve estar entre 1 e 625.", ephemeral=True)
        return
    player_data[user_id] = {"nome": nome, "fruta": fruta, "level": level}
    save_data(player_data)
    await interaction.response.send_message("Informações salvas com sucesso!",
                                            ephemeral=True)
player_data = load_players()
save_players(player_data)
    


# Comando /editplayerinfo
@bot.tree.command(name="editplayerinfo",
                  description="Edita suas informações de jogador")
@app_commands.describe(nome="Novo nome",
                       fruta="Nova fruta",
                       level="Novo nível (até 625)")
async def editar_player_info(interaction: discord.Interaction, nome: str,
                             fruta: str, level: int):
    user_id = str(interaction.user.id)
    if user_id not in player_data:
        await interaction.response.send_message(
            "Você ainda não cadastrou suas informações. Use /setplayerinfo.",
            ephemeral=True)
        return
    if level > 625 or level < 1:
        await interaction.response.send_message(
            "O nível deve estar entre 1 e 625.", ephemeral=True)
        return
    player_data[user_id] = {"nome": nome, "fruta": fruta, "level": level}
    save_data(player_data)
    await interaction.response.send_message(
        "Informações atualizadas com sucesso!", ephemeral=True)
    player_data = load_players()
    save_players(player_data)


# Comando /playerinfo
@bot.tree.command(name="playerinfo",
                  description="Veja as informações de outro jogador")
@app_commands.describe(user="Usuário para ver as informações")
async def player_info(interaction: discord.Interaction, user: discord.Member):
    user_id = str(user.id)
    data = player_data.get(user_id)
    if not data:
        await interaction.response.send_message(
            "Este usuário ainda não cadastrou informações.", ephemeral=True)
        return
    embed = discord.Embed(title=f"Informações de {user.display_name}",
                          color=discord.Color.blue())
    embed.add_field(name="Nome", value=data["nome"], inline=False)
    embed.add_field(name="Fruta", value=data["fruta"], inline=False)
    embed.add_field(name="Level", value=data["level"], inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=False)


@bot.tree.command(name="recruit", description="chama os recrutadores")
async def recruit(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"@RECRUTADOR, {interaction.user.mention} quer se juntar a tripulação!",
        ephemeral=False)


@bot.tree.command(name="mute", description="Muta um usuário")
@app_commands.describe(user="Usuário a ser mutado",
                       tempo="Tempo de mute em minutos")
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

@bot.tree.command(name="reactionrole", description="Configura um sistema de reaction roles")
@app_commands.describe(
    message="ID da mensagem onde as reações serão usadas",
    emoji="Emoji para a reação",
    role="Cargo a ser atribuído")
async def reaction_role(interaction: discord.Interaction, message: str, emoji: str, role: discord.Role):

    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "Você não tem permissão para configurar reaction roles.", ephemeral=True)
        return

    try:
        # ✅ Corrigido: usa os arquivos corretos
        reaction_roles = load_reactions()
        if "reaction_roles" not in reaction_roles:
            reaction_roles["reaction_roles"] = []

        reaction_roles["reaction_roles"].append({
            "message_id": message,
            "emoji": emoji,
            "role_id": role.id
        })
        save_reactions(reaction_roles)
        await interaction.response.send_message(
            f"Reaction role configurado com sucesso! Quando alguém reagir com {emoji}, será atribuído o cargo {role.name}.",
            ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Erro ao configurar o reaction role: {e}", ephemeral=True)
    # Tenta adicionar o emoji automaticamente na mensagem
    canal = interaction.channel  # você pode melhorar isso se quiser pegar por ID
    try:
        mensagem = await canal.fetch_message(int(message))
        await mensagem.add_reaction(emoji)
    except Exception as e:
        await interaction.followup.send(f"⚠️ Erro ao adicionar o emoji na mensagem: {e}", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:  # Ignorar reações do bot
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member:
        return

    # 🎫 Sistema de Ticket
    if payload.message_id == bot.ticket_message_id and str(payload.emoji) == "🎫":
        channel_name = f"ticket-{member.name}".lower()
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await member.send(f"📩 Você já tem um ticket aberto: {existing_channel.mention}")
            return

        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        staff_role = discord.utils.get(guild.roles, name="Staff")
        if not staff_role:
            print("Cargo 'Staff' não encontrado!")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)

        close_button = discord.ui.Button(label="Fechar ticket", style=discord.ButtonStyle.red)

        async def close_callback(interaction: discord.Interaction):
            await channel.delete(reason=f"Ticket fechado por {interaction.user}")

        close_button.callback = close_callback
        view = discord.ui.View()
        view.add_item(close_button)

        await channel.send(f"{member.mention} Obrigado por abrir o ticket! Um membro da staff irá te atender em breve.", view=view)

    # 🎭 Reaction Roles
    reaction_roles = load_reactions()
    if "reaction_roles" in reaction_roles:
        for role_data in reaction_roles["reaction_roles"]:
            if str(payload.message_id) == str(role_data["message_id"]) and str(payload.emoji) == role_data["emoji"]:
                role = guild.get_role(role_data["role_id"])
                if role:
                    await member.add_roles(role, reason="Reaction role")
                    print(f"Cargo {role.name} atribuído a {member.name}.")


bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')


keep_alive()

# Token do bot
bot.run(os.getenv("DISCORD_TOKEN"))
