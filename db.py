from tinydb import TinyDB, Query

db = TinyDB("db.json")

Players = db.table("players")
ReactionRoles = db.table("reaction_roles")
PlayerQuery = Query()
RoleQuery = Query()

def salvar_jogador(user_id, nome, fruta, level):
    Players.upsert({
        "user_id": str(user_id),
        "nome": nome,
        "fruta": fruta,
        "level": level
    }, PlayerQuery.user_id == str(user_id))

def buscar_jogador(user_id):
    result = Players.search(PlayerQuery.user_id == str(user_id))
    return result[0] if result else None

def deletar_jogador(user_id):
    Players.remove(PlayerQuery.user_id == str(user_id))

def adicionar_reaction_role(message_id, emoji, role_id):
    ReactionRoles.insert({
        "message_id": str(message_id),
        "emoji": emoji,
        "role_id": int(role_id)
    })

def listar_reaction_roles():
    return ReactionRoles.all()

def buscar_reaction_roles_por_mensagem(message_id):
    return ReactionRoles.search(RoleQuery.message_id == str(message_id))
