import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import asyncio
from datetime import datetime, timezone
from flask import Flask
import threading

app = Flask('')
@app.route('/')
def home(): return "Bot Online"

def run(): app.run(host='0.0.0.0', port=8080)
threading.Thread(target=run).start()

# ============================================================
#  CONFIGURACION - Carga el token seguro desde Render
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"

# ============================================================
#  BASE DE DATOS (JSON simple, sin necesidad de SQL)
# ============================================================
DB_FILE = "db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_user(db, user_id):
    uid = str(user_id)
    if uid not in db["users"]:
        return None
    return db["users"][uid]

def create_user(db, user_id, display_name):
    uid = str(user_id)
    db["users"][uid] = {
        "name": display_name,
        "coins": 1000,
        "figures": [],       # lista de figuras que posee (pueden repetirse)
        "team": [None, None, None],  # equipo de 3 posiciones
        "wins": 0,
        "losses": 0,
        "level": 1,
        "xp": 0
    }
    save_db(db)
    return db["users"][uid]

# ============================================================
#  FIGURAS
#  image: URL pública de la imagen (Imgur, Discord CDN, etc.)
# ============================================================
FIGURES = {
    "gamer64": {
        "name": "Gamer64",
        "emoji": "🤖",
        "rarity": "raro",
        "price": 640,
        "hp": 142,
        "attack": 34,
        "defense": 38,
        "speed": 41,
        "image": "https://i.imgur.com/gl2UZZ3.png",  # Pon la URL pública de GamerNew.png aquí
    },
    "sonic": {
        "name": "Sonic",
        "emoji": "🦔",
        "rarity": "épico",
        "price": 1991,
        "hp": 200,
        "attack": 40,
        "defense": 42,
        "speed": 60,
        "image": "https://preview.redd.it/my-first-fanart-drew-the-sonic-adventure-pose-v0-ca4ogp5vra4c1.jpg?width=1080&crop=smart&auto=webp&s=34f3148da3adadf91ecfdfc4d2c218a137a0213f",
    },
    "alex": {
        "name": "Alex",
        "emoji": "<:sketch1778366830925:1503043086564069497>",
        "rarity": "legendario",
        "price": 215,
        "hp": 250,
        "attack": 14,
        "defense": 30,
        "speed": 50,
        "image": "https://i.imgur.com/iJctAhj.png",  # Pon la URL aquí
    },
    "ringmaster": {
        "name": "Caine",
        "emoji": "🦷",
        "rarity": "legendario",
        "price": 1998,
        "hp": 230,
        "attack": 35,
        "defense": 40,
        "speed": 30,
        "image": "https://preview.redd.it/caine-villain-or-misunderstood-v0-covbmlxtsnqg1.png?width=860&format=png&auto=webp&s=8a3b7c21e6aa8adb851d88643994bd495064ca97",
        "passive": "torment",   # Pasiva: WHY DO YOU PEOPLE TORMENT ME
    },
    "michibug": {
        "name": "MichiBug",
        "emoji": "🦊",
        "rarity": "legendario",
        "price": 900,
        "hp": 170,
        "attack": 22,
        "defense": -2,
        "speed": 8,
        "image": "https://i.imgur.com/gPMrvOs.png",
    },
    "tails": {
        "name": "Tails",
        "emoji": "🦊",
        "rarity": "épico",
        "price": 1992,
        "hp": 140,
        "attack": 23,
        "defense": 20,
        "speed": 20,
        "image": "https://static.wikia.nocookie.net/sstp/images/6/6a/Tails.png/revision/latest?cb=20130319112956",
    },
    "hatred": {
        "name": "1x1x1x1",
        "emoji": "🤬",
        "rarity": "legendario",
        "price": 1250,
        "hp": 245,
        "attack": 30,
        "defense": 25,
        "speed": 25,
        "image": "https://pbs.twimg.com/media/Gxe4SOdWcAArEZN.jpg",
    },
    "chicken": {
        "name": "Shedletsky",
        "emoji": "🐔",
        "rarity": "legendario",
        "price": 2006,
        "hp": 210,
        "attack": 45,
        "defense": 30,
        "speed": 30,
        "image": "https://i.namu.wiki/i/uQrQ4Z8Ff1fNhIln9_uMjuG2-ehRjdvFjBoNQso5fohpP8WclZo-YF4QpQIfjqj6Y6hhYDmTlR-xatYm2PFNOg.webp",
    },
    "blackout": {
        "name": "Black Impostor",
        "emoji": "🔪",
        "rarity": "legendario",
        "price": 2021,
        "hp": 235,
        "attack": 40,
        "defense": 30,
        "speed": 25,
        "image": "https://static.wikia.nocookie.net/the-ultimate-evil/images/b/bc/Black_Impostor_FINALE_V4.png/revision/latest/scale-to-width/360?cb=20230309224128",
    },
    "lobster": {
        "name": "Lobster",
        "emoji": "🦞",
        "rarity": "común",
        "price": 0,        # Solo se obtiene con /lobster
        "hp": 1,
        "attack": 1,
        "defense": 1,
        "speed": 1,
        "image": "https://images.contentstack.io/v3/assets/bltcedd8dbd5891265b/blt6f01003267cbf97f/664cbd77d94e39430f4c7cd1/lobster-guide-hero.jpg?q=70&width=3840&auto=webp",
    },
    "agustoloco": {
        "name": "AgustoLoco",
        "emoji": "🚬",
        "rarity": "común",
        "price": 1,
        "hp": 30,
        "attack": 1,
        "defense": 0,
        "speed": 1,
        "image": "https://i.imgur.com/ZEPFJmF.png",  # Pon la URL aquí
    },
    "007n7": {
        "name": "007n7",
        "emoji": "🍔",
        "rarity": "epico",
        "price": 500,
        "hp": 210,
        "attack": 21,
        "defense": 32,
        "speed": 30,
        "image": "https://i.redd.it/b5tes4g0w75f1.jpeg",
    },
    "kidd": {
        "name": "c00lkidd",
        "emoji": "😎",
        "rarity": "legendario",
        "price": 900,
        "hp": 220,
        "attack": 40,
        "defense": 30,
        "speed": 52,
        "image": "https://media.printables.com/media/prints/42d1eb40-be5b-4dbe-aebf-e11a8c2538b9/images/11589036_18ec24f9-1577-4fac-94f1-e62f2d551df7_12dfa319-2d71-4dfc-a36b-85c25efc5e83/thumbs/inside/1280x960/jpg/artworks-ugygzb9kdqny96ww-9vz6cq-t1080x1080.webp",
    },
    "twotime": {
        "name": "Two Time",
        "emoji": "🗡️",
        "rarity": "epico",
        "price": 500,
        "hp": 170,
        "attack": 25,
        "defense": 25,
        "speed": 30,
        "image": "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000da84d1891be46091133c6e496f49",
    },
    "noli": {
        "name": "Noli",
        "emoji": "✨",
        "rarity": "legendario",
        "price": 1100,
        "hp": 211,
        "attack": 25,
        "defense": 20,
        "speed": 30,
        "image": "https://static.wikia.nocookie.net/forsaken2024/images/2/26/NoliChangedRender.png/revision/latest?cb=20260423180748",
        "passive": "hallucinations",
    },
    "guest1337": {
        "name": "Guest1337",
        "emoji": "👊",
        "rarity": "epico",
        "price": 500,
        "hp": 215,
        "attack": 30,
        "defense": 25,
        "speed": 30,
        "image": "https://static.wikia.nocookie.net/forsaken2024/images/thumb/f/f2/Guest_1337_Render.png/220px-Guest_1337_Render.png",
    },
    "noob": {
        "name": "Noob",
        "emoji": "😃",
        "rarity": "raro",
        "price": 450,
        "hp": 200,
        "attack": 20,
        "defense": 20,
        "speed": 20,
        "image": "https://static.wikia.nocookie.net/forsaken2024/images/7/7c/Noobnewest.png/revision/latest?cb=20260417122231",
    },
    "chance": {
        "name": "Chance",
        "emoji": "🔫",
        "rarity": "legendario",
        "price": 777,
        "hp": 200,
        "attack": 27,
        "defense": 37,
        "speed": 37,
        "image": "https://static.wikia.nocookie.net/lgbt-characters/images/b/bd/Chance_%28Forsaken%29.png/revision/latest/thumbnail/width/360/height/450?cb=20260320010117",
    },
    "johndoe": {
        "name": "John Doe",
        "emoji": "💢",
        "rarity": "legendario",
        "price": 1120,
        "hp": 202,
        "attack": 30,
        "defense": 40,
        "speed": 30,
        "image": "https://i.redd.it/p5y051gk6mve1.jpeg",
    },
    "janedoe": {
        "name": "Jane Doe",
        "emoji": "🪓",
        "rarity": "epico",
        "price": 800,
        "hp": 170,
        "attack": 35,
        "defense": 30,
        "speed": 35,
        "image": "https://static.wikia.nocookie.net/forsaken2024/images/4/4e/JaneDoerender.png/revision/latest/smart/width/300/height/300?cb=20260308103449",
    },
}

RARITY_COLOR = {
    "común": 0x95a5a6,
    "raro": 0x3498db,
    "épico": 0x9b59b6,
    "epico": 0x9b59b6,
    "legendario": 0xf1c40f,
    "Legendario": 0xf1c40f,
    "mítico": 0xff0000,
}

RARITY_STARS = {
    "común": "⚪",
    "raro": "🔵",
    "épico": "🟣",
    "epico": "🟣",
    "legendario": "🌟",
    "Legendario": "🌟",
    "mítico": "🔱",
}

XP_PER_WIN = 50
XP_PER_LOSS = 15
COINS_WIN = 100
COINS_LOSS = 20

def xp_to_level_up(level):
    return 100 * level

def apply_level_bonus(base_stat, level):
    """Aplica un bonus de stats según el nivel de la figura (+5% por nivel)"""
    if base_stat < 0:
        return base_stat  # No aplicar bonus a stats negativos (ej: defensa negativa de MichiBug)
    return int(base_stat * (1 + (level - 1) * 0.05))

def get_figure_level(figure_data):
    return figure_data.get("level", 1)

def get_figure_xp(figure_data):
    return figure_data.get("xp", 0)

# ============================================================
#  BOT SETUP
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ============================================================
# ============================================================
#  HABILIDADES POR FIGURA
#  Tipos: "damage" | "heal" | "drain" | "drain_fill" (Segunda Fase)
#  stun: True = aturde al rival 1 turno (no puede actuar)
#  team_heal: True = cura también a los compañeros
#  no_heal: True = Gamer64 no puede recuperar HP hasta el fin de la batalla
#  fill_bar: True = llena la barra de energía completamente
# ============================================================
# ============================================================
#  HABILIDADES POR FIGURA
#  Tipos: "damage" | "heal" | "drain" | "drain_fill"
#  Efectos especiales:
#    stun: True              → aturde al rival 1 turno
#    aoe: True               → daña a todo el equipo rival
#    aoe_secondary_power: N  → daño a los otros 2 rivales (no al activo)
#    team_heal: True         → cura también a compañeros
#    team_heal_power: N      → HP que cura a cada compañero
#    bar_bonus: N            → energía extra ganada (drain)
#    no_heal: True           → el usuario no puede curarse hasta el final
#    fill_bar: True          → llena la barra al máximo
#    dmg_enemy: N            → daño adicional al rival (drain_fill)
#    force_switch: True      → fuerza al rival a no poder usar esa figura por N turnos
#    force_switch_turns: N   → cuántos turnos dura el bloqueo
# ============================================================
FIGURE_SKILLS = {
    "gamer64": [
        {
            "name": "Heroic Pose",
            "cost": 30,
            "type": "team_atk_buff",
            "power": 0,
            "atk_buff": 10,            # +10 daño a todas las habilidades aliadas, acumulable
            "team_buff": True,
            "desc": "Gamer64 hace una pose heroica, dando +10 de daño a todas las habilidades de las figuras aliadas. ¡Acumulable!",
        },
        {
            "name": "Cannon Arm",
            "cost": 60,
            "type": "damage",
            "power": 15,
            "stun": True,
            "desc": "Transforma su brazo en un cañón y dispara un misil. Aturde al oponente 1 turno.",
        },
        {
            "name": "Regeneración",
            "cost": 100,
            "type": "heal",
            "power": 10,
            "team_heal": True,
            "team_heal_power": 12,
            "desc": "Cura a Gamer64 y a sus compañeros de batalla.",
        },
    ],
    "alex": [
        {
            "name": "Parry",
            "cost": 30,
            "type": "parry",        # Tipo especial: contraataca si el rival ataca este turno
            "power": 0,             # Sin daño directo
            "parry_flat_bonus": 10, # Contraataca con el daño del ataque + 10
            "desc": "Alex hace un parry. Si el rival ataca este turno, lo contraataca con su propio daño +10.",
        },
        {
            "name": "Carga Estelar",
            "cost": 60,
            "type": "buff",         # Tipo buff: potencia el siguiente ataque
            "power": 0,
            "atk_buff": 15,         # Suma 15 de ATK temporal al siguiente golpe
            "desc": "La estrella de Alex brilla y carga su poder. Su próximo golpe hará más daño.",
        },
        {
            "name": "Esfera Luminosa",
            "cost": 100,
            "type": "damage",
            "power": 14,
            "force_switch": True,
            "force_switch_turns": 2,  # Ciega al rival 2 turnos
            "desc": "Alex lanza una esfera de luz que explota, cegando al rival por 2 turnos y haciéndole daño.",
        },
    ],
    "ringmaster": [
        {
            "name": "Grab a Bite",
            "cost": 30,
            "type": "damage",
            "power": 10,
            "stun": True,
            "stun_turns": 2,           # stun extendido 2 turnos
            "self_heal": 5,            # Caine se cura 5 HP (mitad del daño)
            "desc": "Caine abre la boca, muerde al rival, se cura 5 HP y lo aturde 2 turnos.",
        },
        {
            "name": "Digital Hallucinations",
            "cost": 60,
            "type": "damage",
            "power": 25,
            "force_switch": True,
            "force_switch_turns": 3,   # fuerza cambio de figura
            "desc": "Caine finge que son alucinaciones digitales, daña al rival y lo fuerza a cambiar de figura.",
        },
        {
            "name": "Retributional Ringmaster",
            "cost": 100,
            "type": "retribution",     # contraataca con la mitad del daño recibido durante 1 turno
            "power": 0,
            "retrib_turns": 1,
            "desc": "Caine recibe el daño de una figura y luego libera su enfado devolviendo la mitad.",
        },
    ],
    "michibug": [
        {
            "name": "Counter",
            "cost": 30,
            "type": "michi_counter",   # parry especial: devuelve mitad del daño, 20% de que el rival no ataque
            "power": 0,
            "evade_chance": 20,        # 20% de que el rival pierda su turno
            "desc": "Michi se pone en pose defensiva. Si el rival ataca, devuelve la mitad del daño. 20% de que el rival ni ataque.",
        },
        {
            "name": "Glitch Manipulation",
            "cost": 60,
            "type": "glitch_dmg",      # daño aleatorio 2-45
            "power": 0,
            "min_dmg": 2,
            "max_dmg": 45,
            "desc": "Michi canaliza su poder glitch y lanza un objeto aleatorio al oponente. Daño: 2 a 45.",
        },
        {
            "name": "Corruption",
            "cost": 100,
            "type": "corruption",      # copia una habilidad aleatoria del juego y la ejecuta
            "power": 0,
            "desc": "Michi acumula poder glitch y ejecuta una habilidad aleatoria de cualquier figura del juego.",
        },
    ],
    "tails": [
        {
            "name": "Robot Buddy",
            "cost": 30,
            "type": "dot",
            "power": 10,
            "dot_turns": 3,
            "dot_stackable": True,
            "desc": "Tails lanza un robot al oponente. Hace 10 de daño cada turno por 3 turnos.",
        },
        {
            "name": "Intelectual",
            "cost": 60,
            "type": "team_atk_buff",
            "power": 0,
            "atk_buff": 10,
            "team_buff": True,
            "desc": "Tails usa su intelecto para dar +10 ATK a todas las figuras aliadas. ¡Acumulable!",
        },
        {
            "name": "Fly Away",
            "cost": 100,
            "type": "fly_away",        # Tails y el rival quedan bloqueados 3 turnos
            "power": 0,
            "fly_turns": 3,
            "desc": "Tails agarra al rival y lo lleva volando. Ambas figuras quedan bloqueadas 3 turnos.",
        },
    ],
    "hatred": [
        {
            "name": "Mass Infection",
            "cost": 30,
            "type": "damage",
            "power": 30,
            "dot": True,
            "dot_power": 8,
            "dot_turns": 4,
            "desc": "1x se acerca y aplica Mass Infection: daño normal + veneno por 4 turnos.",
        },
        {
            "name": "Entanglement",
            "cost": 60,
            "type": "damage",
            "power": 10,
            "stun": True,
            "stun_turns": 2,
            "entangle": True,      # el equipo aliado hace más daño a esta figura
            "desc": "1x lanza su Entanglement: atrae al enemigo, lo stunea 2 turnos y las figuras aliadas le hacen más daño.",
        },
        {
            "name": "Rejuvenate the Rotten",
            "cost": 100,
            "type": "revive_team",  # revive figuras aliadas muertas con stats fijos
            "power": 20,            # daño propio
            "revive_hp": 20,
            "revive_atk": 10,
            "revive_def": 15,
            "revive_poison": True,  # las figuras revividas envenenan al atacar
            "desc": "1x se clava sus espadas (-20 HP) y revive a todos los aliados caídos con 20HP/10ATK/15DEF. Los revividos envenenan al atacar.",
        },
    ],
    "chicken": [
        {
            "name": "Chicken Leg",
            "cost": 30,
            "type": "heal_self_small",  # cura solo a Shedletsky
            "power": 0,
            "heal_min": 20,
            "heal_max": 25,
            "desc": "Shedletsky saca una pierna de pollo a medio comer, y le pega un mordisco rápido, curándose rápidamente.",
        },
        {
            "name": "Slash",
            "cost": 60,
            "type": "slash",         # usa la espada activa y aplica su efecto
            "power": 50,
            "desc": "Shedletsky ataca aplicando el efecto de su espada actual.",
        },
        {
            "name": "Chicken Legs",
            "cost": 100,
            "type": "heal_team_self", # +25 aliados, +30 a sí mismo
            "power": 30,              # curación propia
            "team_heal_power": 25,
            "desc": "Shedletsky saca una cubeta de pollo y cura +30 HP propio y +25 a todos los aliados.",
        },
    ],
    "blackout": [
        {
            "name": "Chase Up",
            "cost": 30,
            "type": "drain",
            "power": 10,           # se daña 10 HP
            "bar_bonus": 30,       # recarga la barra extra
            "desc": "El Impostor recarga su barra de carga a costa de 10 HP.",
        },
        {
            "name": "Fast Kill",
            "cost": 60,
            "type": "fast_kill",   # requiere 3 usos seguidos
            "power": 50,
            "charges_needed": 3,
            "desc": "El Impostor se acerca y clava su cuchillo. Úsalo 3 turnos seguidos para activarlo.",
        },
        {
            "name": "Consumed By Fury",
            "cost": 100,
            "type": "consumed_fury",  # mata activa + 15 a otras + impostor muere
            "power": 0,
            "splash_dmg": 15,
            "desc": "El Impostor se avalanza, mata a la figura activa enemiga, hace 15 a las otras 2 y luego explota.",
        },
    ],
    "lobster": [
        {
            "name": "LOBSTER",
            "cost": 30,
            "type": "lobster",     # No hace nada... o sí?
            "power": 0,
            "desc": "La langosta te mira fijamente. No pasa nada. O casi nada.",
        },
        {
            "name": "LOBSTER",
            "cost": 60,
            "type": "lobster",
            "power": 0,
            "desc": "La langosta te mira fijamente. No pasa nada. O casi nada.",
        },
        {
            "name": "LOBSTER",
            "cost": 100,
            "type": "lobster",
            "power": 0,
            "desc": "La langosta te mira fijamente. No pasa nada. O casi nada.",
        },
    ],
    "agustoloco": [
        {
            "name": "Fumada",
            "cost": 30,
            "type": "gamble",       # 50/50: cura hasta 150 HP O baja a 1 HP y reduce ATK
            "power": 0,
            "gamble_heal": 150,     # Si sale bien: HP sube a 150 (nuevo máximo temporal)
            "gamble_atk_debuff": 5, # Si sale mal: ATK baja 5 puntos
            "desc": "50/50: O AgustoLoco se cura hasta 150 HP (¡nuevo máximo!) o cae a 1 HP y pierde ATK.",
        },
        {
            "name": "Mechero",
            "cost": 60,
            "type": "gamble_fire",  # Probabilidad bajísima (<1%) de hacer daño enorme. Falla casi siempre.
            "power": 0,
            "fire_dmg": 80,         # Daño si el mechero funciona
            "fire_chance": 1,       # 1% de probabilidad
            "fire_immune_check": True,  # No funciona si el rival es inmune al fuego
            "desc": "El mechero tiene menos del 1% de funcionar. Si lo hace, deja muy herido al rival.",
        },
        {
            "name": "Peso",
            "cost": 100,
            "type": "damage",
            "power": 30,
            "desc": "AgustoLoco lanza su único peso con toda su fuerza.",
        },
    ],
    "sonic": [
        {
            "name": "Spindash",
            "cost": 30,
            "type": "damage",
            "power": 25,                 # daño al activo rival
            "aoe": True,                 # golpea a todo el equipo rival
            "aoe_secondary_power": 20,   # daño a los otros 2
            "desc": "Sonic agarra velocidad y hace un Spindash hacia el frente, dañando a todos los enemigos.",
        },
        {
            "name": "Homing Attack",
            "cost": 60,
            "type": "damage",
            "power": 30,
            "desc": "Sonic salta y se lanza directamente al enemigo, dándole un golpe fuerte y certero.",
        },
        {
            "name": "Speed Power",
            "cost": 100,
            "type": "damage",
            "power": 50,
            "force_switch": True,        # fuerza cambio de figura en el rival
            "force_switch_turns": 3,     # no puede volver a esa figura por 3 turnos
            "desc": "Sonic corre a máxima velocidad y golpea al rival, dejándolo fuera de combate por 3 turnos.",
        },
    ],
    # ─── NUEVAS FIGURAS ───────────────────────────────────────────
    "007n7": [
        {
            "name": "Switch Clone Type",
            "cost": 30,
            "type": "clone_switch",  # cambia entre def/atk/heal
            "power": 0,
            "desc": "007n7 cambia el tipo de clon que usará: DEF (bloquea 2 golpes), ATK (parry con mitad del daño), HEAL (cura según el daño recibido).",
        },
        {
            "name": "Clone",
            "cost": 60,
            "type": "clone_action",  # ejecuta según tipo activo
            "power": 0,
            "desc": "007n7 lanza un clon. Su comportamiento depende del tipo activo (def/atk/heal).",
        },
        {
            "name": "Teleport",
            "cost": 100,
            "type": "teleport_007",  # cede turno, se cura 10/turno, vuelve al tener HP lleno o si aliado muere
            "power": 0,
            "desc": "007n7 se teletransporta lejos, cede sus turnos y se cura 10HP por turno hasta tener vida llena.",
        },
    ],
    "kidd": [
        {
            "name": "Fling Brick",
            "cost": 30,
            "type": "fling_brick",   # daño + reduce ATK rival, 20% de forzar cambio
            "power": 10,
            "desc": "c00lkidd lanza un ladrillo. Reduce el ATK del rival. 20% de mandarlo a volar (fuerza cambio).",
        },
        {
            "name": "Walkspeed Override",
            "cost": 60,
            "type": "damage",
            "power": 40,
            "dot": True,
            "dot_power": 8,
            "dot_turns": 3,
            "desc": "c00lkidd carga hacia el oponente, haciéndole daño e inflingiéndole quemadura (8 daño/turno x3).",
        },
        {
            "name": "Minions",
            "cost": 100,
            "type": "minion_shield",  # escudo de 2 golpes; si atacan con minions activos, el rival recibe 10 + quemadura
            "power": 0,
            "desc": "c00lkidd invoca minions: escudo de 2 golpes. Si atacan con minions activos, el rival recibe 10 daño + quemadura.",
        },
    ],
    "twotime": [
        {
            "name": "Spawnpoint",
            "cost": 30,
            "type": "spawnpoint",    # coloca punto de respawn; pasiva: 4 backstabs = revive con 50% HP
            "power": 0,
            "desc": "Two Time coloca un punto de respawn. Si acumula 4 backstabs con barra llena, puede revivir con 50% HP.",
        },
        {
            "name": "Backstab",
            "cost": 60,
            "type": "backstab",      # 15 daño + stun 1 turno + recarga barra
            "power": 15,
            "stun": True,
            "bar_bonus": 20,
            "desc": "Two Time se acerca y da un backstab. Aturde al rival 1 turno y recarga su barra.",
        },
        {
            "name": "Crouch",
            "cost": 100,
            "type": "crouch",        # reduce daño recibido este turno, buff ATK 2 turnos
            "power": 0,
            "desc": "Two Time se agacha, reduciendo el daño recibido y aumentando su daño por 2 turnos.",
        },
    ],
    "noli": [
        {
            "name": "Voidstar",
            "cost": 30,
            "type": "voidstar",      # 10 daño + atrae (próximo ataque hace más daño)
            "power": 10,
            "desc": "Noli lanza su voidstar, dañando al rival y preparando el próximo ataque para hacer +15 daño.",
        },
        {
            "name": "Voidrush",
            "cost": 60,
            "type": "voidrush",      # 25 daño, +15 si rival tiene alucinaciones
            "power": 25,
            "desc": "Noli hace un Voidrush. Si el rival tiene alucinaciones, hace +15 daño extra.",
        },
        {
            "name": "Observant",
            "cost": 100,
            "type": "observant",     # desaparece 5 turnos, pone figura sustituta; al volver hace daño masivo
            "power": 0,
            "desc": "Noli desaparece 5 turnos generando alucinaciones. Al volver hace daño masivo al enemigo activo.",
        },
    ],
    "guest1337": [
        {
            "name": "Block",
            "cost": 30,
            "type": "guest_block",   # bloquea el siguiente ataque + gana carga para Punch
            "power": 0,
            "desc": "Guest bloquea el siguiente ataque y gana una carga para usar Punch.",
        },
        {
            "name": "Charge",
            "cost": 60,
            "type": "damage",
            "power": 25,
            "dot": True,
            "dot_power": 5,
            "dot_turns": 2,
            "desc": "Guest se lanza hacia el oponente, haciéndole daño y alejándolo (reduce su daño 2 turnos).",
        },
        {
            "name": "Punch",
            "cost": 100,
            "type": "guest_punch",   # requiere carga de Block; 55 daño + stun 2 turnos
            "power": 55,
            "stun": True,
            "stun_turns": 2,
            "desc": "Requiere una carga de Block. Guest lanza un golpe masivo que aturde al rival 2 turnos.",
        },
    ],
    "noob": [
        {
            "name": "Bloxy Cola",
            "cost": 30,
            "type": "bloxy_cola",    # incrementa la ganancia de energía por 2 turnos
            "power": 0,
            "desc": "Noob toma una Bloxy Cola. Gana +15 de energía extra por turno durante 2 turnos.",
        },
        {
            "name": "Slateskin",
            "cost": 60,
            "type": "slateskin",     # se vuelve de piedra: recibe mitad del daño y devuelve mitad
            "power": 0,
            "desc": "Noob toma poción de slateskin. El próximo ataque que reciba hace mitad de daño y devuelve mitad al rival.",
        },
        {
            "name": "GhostBurger",
            "cost": 100,
            "type": "ghostburger",   # evasión aumentada + cura 10 HP/turno por 4 turnos
            "power": 0,
            "desc": "Noob come una GhostBurger. Mayor evasión y se cura 10 HP por turno durante 4 turnos.",
        },
    ],
    "chance": [
        {
            "name": "Coin Flip",
            "cost": 30,
            "type": "coin_flip",     # cara = gana carga (max 3); sello = próximo ataque le hace más daño
            "power": 0,
            "desc": "Chance gira su moneda. Cara = gana una carga (máx 3). Sello = el siguiente ataque le hará más daño.",
        },
        {
            "name": "Gun Shot",
            "cost": 60,
            "type": "gun_shot",      # 1 carga=40% stun, 2=70%, 3=100%; resto puede explotar en la cara
            "power": 0,
            "desc": "Chance dispara su revólver. A más cargas, más probabilidad de stunear al rival.",
        },
        {
            "name": "Reload Stats",
            "cost": 100,
            "type": "reload_stats",  # cambia HP de Chance aleatoriamente entre 150-250
            "power": 0,
            "desc": "Chance recarga su revólver y cambia sus stats aleatoriamente: nueva vida entre 150 y 250.",
        },
    ],
    "johndoe": [
        {
            "name": "Spikes",
            "cost": 30,
            "type": "spikes",        # daño al rival + bloquea 2 ataques + John pierde 20 HP
            "power": 15,
            "desc": "John cubre el campo de espinas. Daña al rival, bloquea los siguientes 2 ataques, pero John pierde 20 HP.",
        },
        {
            "name": "Error 404",
            "cost": 60,
            "type": "error404",      # John pierde 10 HP, barra llena + buff ATK +20 por 4 turnos
            "power": 0,
            "desc": "John se arranca el ojo (-10 HP). Su barra de energía se llena y gana +20 ATK por 4 turnos.",
        },
        {
            "name": "Traps",
            "cost": 100,
            "type": "traps",         # 3 usos: al 3ro atrapa al rival con 20 daño/turno por 3 turnos
            "power": 0,
            "desc": "Úsala 3 veces para atrapar al rival en una trampa que hace 20 daño por turno durante 3 turnos.",
        },
    ],
    "janedoe": [
        {
            "name": "Crystal Type",
            "cost": 30,
            "type": "crystal_switch",  # cambia entre tipo daño y tipo curación
            "power": 0,
            "desc": "Jane cambia el tipo de cristal: DAÑO (stuned + 20 daño) o CURACIÓN (cura al aliado con menos HP + inmunidad).",
        },
        {
            "name": "Crystal Throw",
            "cost": 60,
            "type": "crystal_throw",   # ejecuta según tipo activo
            "power": 20,
            "desc": "Jane lanza un cristal. Si es de daño: 20 daño + stun 3 turnos. Si es curación: cura al aliado con menos HP + inmunidad 3 turnos.",
        },
        {
            "name": "Hatchet",
            "cost": 100,
            "type": "damage",
            "power": 45,
            "dot": True,
            "dot_power": 8,
            "dot_turns": 4,
            "desc": "Jane lanza su hacha hacia el enemigo, haciéndole daño y aplicando Resonancia (8 daño/turno x4).",
        },
    ],
}


# ============================================================
#  SISTEMA DE BATALLAS NUEVO (3 figuras + barra de energía)
# ============================================================
active_battles = {}
pending_pvp = {}

ENERGY_PER_TURN = 20
ENERGY_MAX = 100

def make_fighter(fig_key, owner_fig_data, hp_mult=1.0, atk_mult=1.0, energy_bonus=0):
    """Crea un luchador con HP, energía y habilidades listas.
    hp_mult/atk_mult: multiplicadores para jefes más difíciles.
    energy_bonus: energía extra por turno para jefes más difíciles.
    """
    fig = FIGURES[fig_key]
    lvl = owner_fig_data.get("level", 1)
    base_hp  = int(apply_level_bonus(fig["hp"],     lvl) * hp_mult)
    base_atk = int(apply_level_bonus(fig["attack"],  lvl) * atk_mult)
    fighter = {
        "key":          fig_key,
        "name":         fig["name"],
        "emoji":        fig["emoji"],
        "hp":           base_hp,
        "max_hp":       base_hp,
        "atk":          base_atk,
        "defense":      apply_level_bonus(fig["defense"], lvl),
        "level":        lvl,
        "energy":       0,
        "energy_bonus": energy_bonus,   # energía extra por turno
        "skills":       FIGURE_SKILLS.get(fig_key, FIGURE_SKILLS["gamer64"]),
        "image":        fig.get("image", ""),
    }
    # Pasiva de Gamer64: revive una vez con el 80% de su HP máximo
    if fig_key == "gamer64":
        fighter["passive_revive"] = True

    # Pasiva de Caine: WHY DO YOU PEOPLE TORMENT ME
    # Cuando HP < 30%: daño x4 pero muere en 5 turnos
    if fig_key == "ringmaster":
        fighter["passive_torment_active"] = False
        fighter["passive_torment_turns"] = 0
    return fighter

class BattleState:
    def __init__(self, p1_id, p2_id, p1_team_keys, p2_team_keys,
                 p1_figs_data, p2_figs_data, is_bot=False):
        self.p1 = p1_id
        self.p2 = p2_id
        self.is_bot = is_bot

        # Equipos: lista de fighters
        self.p1_team = [make_fighter(k, next((f for f in p1_figs_data if f["key"]==k), {"level":1})) for k in p1_team_keys]
        self.p2_team = [make_fighter(
            k,
            next((f for f in p2_figs_data if f["key"]==k), {"level":1}),
            hp_mult=next((f for f in p2_figs_data if f["key"]==k), {}).get("hp_mult", 1.0),
            atk_mult=next((f for f in p2_figs_data if f["key"]==k), {}).get("atk_mult", 1.0),
            energy_bonus=next((f for f in p2_figs_data if f["key"]==k), {}).get("energy_bonus", 0)
        ) for k in p2_team_keys]

        self.p1_active = 0   # índice del luchador activo
        self.p2_active = 0

        # Claves para recompensas
        self.p1_team_keys = p1_team_keys
        self.p2_team_keys = p2_team_keys

        self.turn = 1
        self.log = []
        self.message = None
        self.p1_name = "Jugador 1"   # se sobreescribe desde pvpbot/retar
        self.p2_name = "Jugador 2"

    def current_p1(self): return self.p1_team[self.p1_active]
    def current_p2(self): return self.p2_team[self.p2_active]

    def hp_bar(self, current, maximum):
        ratio = max(0, current / maximum)
        filled = int(ratio * 10)
        return "🟩" * filled + "⬛" * (10 - filled) + f" {current}/{maximum}"

    def energy_bar(self, energy, color="blue"):
        """color="blue" para el jugador, color="red" para el enemigo."""
        filled_block = "🟦" if color == "blue" else "🟥"
        bar = ""
        for i in range(10):
            pos = (i + 1) * 10
            if pos <= energy:
                if pos == 30:   bar += "🟡"
                elif pos == 60: bar += "🟠"
                elif pos == 100:bar += "🔴"
                else:           bar += filled_block
            else:
                bar += "⬛"
        return bar + f" {energy}/100"

    def calc_damage(self, atk, defense, power):
        raw = int(atk * (power / 100)) + random.randint(-3, 8)
        return max(1, raw - (defense // 4))

    def alive_team(self, team):
        return [f for f in team if f["hp"] > 0]

    def next_alive(self, team, current_idx):
        # Busca la siguiente figura viva y no bloqueada
        for i in range(current_idx + 1, len(team)):
            if team[i]["hp"] > 0 and not team[i].get("force_locked", 0) > 0:
                return i
        # Si todas están bloqueadas, busca al menos una viva
        for i in range(current_idx + 1, len(team)):
            if team[i]["hp"] > 0:
                return i
        return None

    def tick_locks(self):
        """Reduce el contador force_locked de todas las figuras al inicio de cada turno."""
        for fig in self.p1_team + self.p2_team:
            if fig.get("force_locked", 0) > 0:
                fig["force_locked"] -= 1

    def get_embed(self, title="⚔️ BATALLA"):
        f1 = self.current_p1()
        f2 = self.current_p2()
        embed = discord.Embed(title=title, color=0xe74c3c)

        p1_label = self.p1_name
        p2_label = self.p2_name

        # --- Equipo jugador 1 ---
        team1_str = ""
        for i, f in enumerate(self.p1_team):
            active_mark = " ◀ EN COMBATE" if i == self.p1_active else ""
            if f["hp"] <= 0:
                team1_str += f"💀 ~~{f['emoji']} {f['name']}~~{active_mark}\n"
            else:
                team1_str += (
                    f"{f['emoji']} **{f['name']}**{active_mark}\n"
                    f"Vida: {self.hp_bar(f['hp'], f['max_hp'])}\n"
                )
        embed.add_field(name=f"👤 {p1_label}", value=team1_str, inline=True)

        # --- Equipo jugador 2 ---
        team2_str = ""
        for i, f in enumerate(self.p2_team):
            active_mark = " ◀ EN COMBATE" if i == self.p2_active else ""
            if f["hp"] <= 0:
                team2_str += f"💀 ~~{f['emoji']} {f['name']}~~{active_mark}\n"
            else:
                team2_str += (
                    f"{f['emoji']} **{f['name']}**{active_mark}\n"
                    f"Vida: {self.hp_bar(f['hp'], f['max_hp'])}\n"
                )
        embed.add_field(name=f"👤 {p2_label}", value=team2_str, inline=True)

        embed.add_field(name="\u200b", value="\u200b", inline=False)

        # --- Figura activa P1: vida + energía (azul) + habilidades ---
        type_emoji = {"damage":"⚔️","heal":"💚","drain":"⚡","drain_fill":"🔴","parry":"🛡️","buff":"⭐","gamble":"🎲","gamble_fire":"🔥","team_atk_buff":"⭐","dot":"💣","bad_update":"🔳","ban_hammer":"🔨"}
        skill_info = ""
        for sk in f1["skills"]:
            can = f1["energy"] >= sk["cost"]
            lock = "✅" if can else "🔒"
            t = type_emoji.get(sk["type"], "⚡")
            skill_info += f"{lock} {t} **{sk['name']}** `[{sk['cost']}⚡]`\n"

        embed.add_field(
            name=f"🔵 {p1_label} — {f1['emoji']} {f1['name']}",
            value=(
                f"**Vida:** {self.hp_bar(f1['hp'], f1['max_hp'])}\n"
                f"**Energía (tuya):** {self.energy_bar(f1['energy'], 'blue')}\n"
                f"─────────────────\n"
                f"{skill_info}"
            ),
            inline=False
        )

        # --- Figura activa P2: energía visible (roja) ---
        embed.add_field(
            name=f"🔴 {p2_label} — {f2['emoji']} {f2['name']}",
            value=(
                f"**Vida:** {self.hp_bar(f2['hp'], f2['max_hp'])}\n"
                f"**Energía (rival):** {self.energy_bar(f2['energy'], 'red')}\n"
            ),
            inline=False
        )

        if self.log:
            embed.add_field(name="📜 Último turno", value="\n".join(self.log[-4:]), inline=False)

        if self.turn == 1:
            embed.set_footer(text=f"🎮 Turno de {p1_label} — elige una habilidad (✅ = disponible)")
        else:
            embed.set_footer(text=f"🎮 Turno de {p2_label}...")

        if f1.get("image"):
            embed.set_thumbnail(url=f1["image"])

        return embed

class BattleView(discord.ui.View):
    """View de batalla sin expiración."""
    def __init__(self, battle: BattleState):
        super().__init__(timeout=None)
        self.battle = battle

def get_battle_view(battle: BattleState):
    """Genera los botones de habilidad según la energía actual del luchador activo."""
    view = BattleView(battle)
    cur_team = battle.p1_team if battle.turn == 1 else battle.p2_team
    cur_idx   = battle.p1_active if battle.turn == 1 else battle.p2_active
    f = cur_team[cur_idx]

    # Fila 0: Atacar + Cambiar figura
    atk_btn = discord.ui.Button(
        label="⚔️ Atacar (gratis)",
        style=discord.ButtonStyle.success,
        custom_id="basic_attack",
        row=0
    )
    atk_btn.callback = make_skill_callback(-2, battle)
    view.add_item(atk_btn)

    # Botón cambiar figura (solo si hay otra figura viva y no bloqueada)
    switchable = [i for i, fig in enumerate(cur_team)
                  if i != cur_idx and fig["hp"] > 0 and not fig.get("force_locked", 0) > 0]
    if switchable:
        sw_btn = discord.ui.Button(
            label="🔄 Cambiar figura",
            style=discord.ButtonStyle.primary,
            custom_id="switch_figure",
            row=0
        )
        sw_btn.callback = make_switch_callback(battle, switchable, cur_team)
        view.add_item(sw_btn)

    # Botón especial Switch Swords si Shedletsky está activo
    if f.get("key") == "chicken":
        swords = ["linked","firebrand","venomshank","windforce","darkheart","illumina","ghostwalker","ice_dagger"]
        sword_names = {"linked":"Linked Sword","firebrand":"Firebrand 🔥","venomshank":"Venomshank ☠️",
                       "windforce":"Windforce 🌪️","darkheart":"Darkheart 🖤","illumina":"Illumina ✨",
                       "ghostwalker":"Ghostwalker 👻","ice_dagger":"Ice Dagger 🧊"}
        current_sword = f.get("active_sword", "linked")
        options = [discord.SelectOption(
            label=sword_names[s],
            value=s,
            default=(s == current_sword)
        ) for s in swords]
        sword_select = discord.ui.Select(placeholder=f"🗡️ Espada actual: {sword_names[current_sword]}", options=options, row=2)
        async def sword_cb(inter: discord.Interaction, fig=f):
            if inter.user.id not in (battle.p1, battle.p2):
                await inter.response.send_message("❌ No eres parte de esta batalla.", ephemeral=True)
                return
            chosen = sword_select.values[0]
            prev = fig.get("active_sword", "linked")
            fig["active_sword"] = chosen
            # Resetear cargas de Ice Dagger si cambia de espada
            if prev != chosen and prev == "ice_dagger":
                fig["ice_dagger_charges"] = 0
                battle.log = [f"🗡️ **{fig['name']}** cambia a **{sword_names[chosen]}**! ❄️ Carga de Ice Dagger perdida."]
            else:
                battle.log = [f"🗡️ **{fig['name']}** equipa **{sword_names[chosen]}**!"]
            await inter.response.edit_message(embed=battle.get_embed(), view=get_battle_view(battle))
        sword_select.callback = sword_cb
        view.add_item(sword_select)

    # Fila 1: Habilidades especiales
    type_emoji = {"damage":"⚔️","heal":"💚","drain":"⚡","drain_fill":"🔴","parry":"🛡️",
                  "buff":"⭐","gamble":"🎲","gamble_fire":"🔥","team_atk_buff":"⭐",
                  "dot":"💣","bad_update":"🔳","ban_hammer":"🔨","fly_away":"✈️"}
    for i, skill in enumerate(f["skills"]):
        can_use = f["energy"] >= skill["cost"]
        t_emoji = type_emoji.get(skill["type"], "⚡")
        style = discord.ButtonStyle.danger if can_use else discord.ButtonStyle.secondary
        btn = discord.ui.Button(
            label=f"{t_emoji} {skill['name']} [{skill['cost']}⚡]",
            style=style,
            disabled=not can_use,
            custom_id=f"skill_{i}",
            row=1
        )
        btn.callback = make_skill_callback(i, battle)
        view.add_item(btn)

    return view

def make_switch_callback(battle: BattleState, switchable: list, cur_team: list):
    """Muestra un selector de figura en el canal y ejecuta el cambio (cuesta el turno)."""
    async def callback(interaction: discord.Interaction):
        uid = interaction.user.id
        if battle.turn == 1 and uid != battle.p1:
            await interaction.response.send_message("❌ No es tu turno.", ephemeral=True)
            return
        if battle.turn == 2 and not battle.is_bot and uid != battle.p2:
            await interaction.response.send_message("❌ No es tu turno.", ephemeral=True)
            return

        options = []
        for i in switchable:
            fig = cur_team[i]
            options.append(discord.SelectOption(
                label=f"{fig['name']} (HP: {fig['hp']}/{fig['max_hp']})",
                value=str(i),
                emoji=fig["emoji"],
                description=f"Nv.{fig.get('level',1)} | ATK:{fig['atk']} DEF:{fig['defense']}"
            ))

        select = discord.ui.Select(placeholder="¿A qué figura cambias?", options=options)

        async def select_cb(inter: discord.Interaction):
            if inter.user.id != uid:
                await inter.response.send_message("❌ No es tu selección.", ephemeral=True)
                return

            chosen = int(select.values[0])
            old_fig = cur_team[battle.p1_active if battle.turn == 1 else battle.p2_active]
            if battle.turn == 1:
                battle.p1_active = chosen
            else:
                battle.p2_active = chosen
            new_fig = cur_team[chosen]
            battle.log = [
                f"🔄 **{old_fig['name']}** sale. ¡Entra **{new_fig['emoji']} {new_fig['name']}**!",
                "   (Cambio de figura — el rival ataca este turno)"
            ]

            # El cambio cuesta el turno: pasa al rival
            battle.turn = 2 if battle.turn == 1 else 1
            channel_id = inter.channel_id

            # Editar el mensaje del selector con el estado actualizado de la batalla
            # (el mensaje de batalla original nunca fue tocado)
            if battle.is_bot and battle.turn == 2:
                await inter.response.edit_message(embed=battle.get_embed(), view=None)
                # Sincronizar battle.message con este mensaje para que bot_turn pueda editarlo
                battle.message = await inter.original_response()
                await asyncio.sleep(1.2)
                await bot_turn(inter, battle, channel_id)
            else:
                await inter.response.edit_message(embed=battle.get_embed(), view=get_battle_view(battle))
                battle.message = await inter.original_response()

        select.callback = select_cb
        sw_view = discord.ui.View(timeout=120)
        sw_view.add_item(select)

        # Enviar el selector como mensaje NUEVO (sin tocar el mensaje de batalla)
        # y actualizar battle.message para que apunte a este nuevo mensaje
        await interaction.response.send_message(
            embed=battle.get_embed(title="🔄 Elige tu figura de reemplazo"),
            view=sw_view
        )
        battle.message = await interaction.original_response()

    return callback

def make_skill_callback(skill_idx, battle: BattleState):
    async def callback(interaction: discord.Interaction):
        uid = interaction.user.id
        channel_id = interaction.channel_id

        if channel_id not in active_battles:
            await interaction.response.send_message("❌ No hay batalla activa.", ephemeral=True)
            return
        if battle.turn == 1 and uid != battle.p1:
            await interaction.response.send_message("❌ No es tu turno.", ephemeral=True)
            return
        if battle.turn == 2 and not battle.is_bot and uid != battle.p2:
            await interaction.response.send_message("❌ No es tu turno.", ephemeral=True)
            return

        await execute_action(interaction, battle, skill_idx, channel_id)
    return callback

async def execute_action(interaction, battle: BattleState, skill_idx: int, channel_id: int):
    """Ejecuta la acción del jugador activo."""
    attacker = battle.current_p1() if battle.turn == 1 else battle.current_p2()
    defender = battle.current_p2() if battle.turn == 1 else battle.current_p1()
    atk_team = battle.p1_team if battle.turn == 1 else battle.p2_team
    battle.log = []

    # Reducir contadores de bloqueo
    battle.tick_locks()

    # Pasiva de Caine: WHY DO YOU PEOPLE TORMENT ME
    if attacker.get("passive_torment_active"):
        attacker["passive_torment_turns"] -= 1
        if attacker["passive_torment_turns"] <= 0:
            attacker["hp"] = 0
            battle.log.append(f"💀 **{attacker['emoji']} {attacker['name']}**: **¡¿PORQUE SIEMPRE ME ATORMENTAN?! ¡HUMANOS INSOLENTES!**")
            battle.log.append(f"   ...y cae derrotado por su propia furia.")
    elif attacker.get("key") == "ringmaster":
        hp_pct = attacker["hp"] / attacker["max_hp"]
        if hp_pct < 0.30 and not attacker.get("passive_torment_active"):
            attacker["passive_torment_active"] = True
            attacker["passive_torment_turns"] = 5
            attacker["atk"] = attacker["atk"] * 4   # daño x4
            battle.log.append(f"😡 **{attacker['emoji']} {attacker['name']}**: **¡¿POR QUÉ ME ATORMENTAN?!**")
            battle.log.append(f"   ¡Su daño se CUADRUPLICA... pero morirá en 5 turnos!")

    # Aplicar daño DOT (veneno/bomba) al atacante al inicio de su turno
    if attacker.get("dots"):
        total_dot = 0
        remaining = []
        for dot in attacker["dots"]:
            attacker["hp"] = max(0, attacker["hp"] - dot["dmg"])
            total_dot += dot["dmg"]
            dot["turns"] -= 1
            if dot["turns"] > 0:
                remaining.append(dot)
        attacker["dots"] = remaining
        battle.log.append(f"☠️ **{attacker['name']}** recibe **{total_dot}** de daño de veneno/bomba!")
        if attacker["hp"] <= 0:
            def_team = battle.p1_team if battle.turn == 1 else battle.p2_team
            def_idx_attr = "p1_active" if battle.turn == 1 else "p2_active"
            current_idx = getattr(battle, def_idx_attr)
            next_idx = battle.next_alive(def_team, current_idx)
            if next_idx is not None:
                setattr(battle, def_idx_attr, next_idx)
                battle.log.append(f"💀 **{attacker['name']}** murió por el veneno!")
            else:
                await end_battle(interaction, battle, channel_id, winner_turn=2 if battle.turn==1 else 1)
                return

    # Verificar si está aturdido (con soporte de stun_turns)
    if attacker.get("stun_turns", 0) > 0:
        attacker["stun_turns"] -= 1
        battle.log.append(f"😵 **{attacker['name']}** está aturdido y pierde su turno! ({attacker['stun_turns']} turnos restantes)")
        # El turno VUELVE al rival (quien aturdo), no avanza
        battle.turn = 2 if battle.turn == 1 else 1
        await finish_turn(interaction, battle, channel_id)
        return
    elif attacker.get("stunned"):
        attacker["stunned"] = False
        battle.log.append(f"😵 **{attacker['name']}** está aturdido y pierde su turno!")
        # El turno VUELVE al rival (quien aturdo), no avanza
        battle.turn = 2 if battle.turn == 1 else 1
        await finish_turn(interaction, battle, channel_id)
        return

    # Siempre subir energía al inicio del turno
    attacker["energy"] = min(ENERGY_MAX, attacker["energy"] + ENERGY_PER_TURN)

    if skill_idx == -2:
        # Resetear fast_kill si usa ataque básico
        if attacker.get("fast_kill_charges", 0) > 0:
            attacker["fast_kill_charges"] = 0
            battle.log.append(f"   ⚠️ **{attacker['name']}** interrumpió la carga de **Fast Kill**!")
        # Ataque básico — gana 20 de energía + daño = mitad del power máximo de la figura
        attacker["energy"] = min(ENERGY_MAX, attacker["energy"] + ENERGY_PER_TURN)
        bonus_atk = attacker.pop("atk_buff", 0)
        effective_atk = attacker["atk"] + bonus_atk
        # Daño = mitad del power de la habilidad más fuerte (skill cost 100), mínimo 1
        max_power = max((sk.get("power", 0) for sk in attacker["skills"]), default=20)
        base_dmg = max(1, round(max_power / 2))
        dmg = max(1, base_dmg + (bonus_atk // 2) + random.randint(-2, 3) - (defender["defense"] // 6))
        defender["hp"] = max(0, defender["hp"] - dmg)
        buff_txt = f" (⭐+{bonus_atk} ATK)" if bonus_atk else ""
        battle.log.append(f"⚔️ **{attacker['emoji']} {attacker['name']}** ataca{buff_txt} → **{dmg}** daño! (+20⚡)")
        # Parry check
        if defender.get("parrying"):
            defender["parrying"] = False
            if defender.get("parry_flat_bonus") is not None:
                # Alex: devuelve el daño recibido + flat bonus
                counter_dmg = max(1, dmg + defender["parry_flat_bonus"])
                defender.pop("parry_flat_bonus", None)
                attacker["hp"] = max(0, attacker["hp"] - counter_dmg)
                battle.log.append(f"   ⚡ **{defender['emoji']} {defender['name']}** hace **PARRY** y devuelve **{counter_dmg}** daño (tu daño +10)!")
            else:
                pct = defender.get("parry_dmg_pct", 25)
                counter_dmg = int(defender["max_hp"] * pct / 100)
                attacker["hp"] = max(0, attacker["hp"] - counter_dmg)
                battle.log.append(f"   ⚡ **{defender['emoji']} {defender['name']}** hace **COUNTER** y devuelve **{counter_dmg}** daño!")
    else:
        skill = attacker["skills"][skill_idx]
        if attacker["energy"] < skill["cost"]:
            await interaction.response.send_message("❌ No tienes suficiente energía.", ephemeral=True)
            return

        # Si no usa fast_kill, resetea los cargos acumulados
        if skill["type"] != "fast_kill" and attacker.get("fast_kill_charges", 0) > 0:
            attacker["fast_kill_charges"] = 0
            battle.log.append(f"   ⚠️ **{attacker['name']}** interrumpió la carga de **Fast Kill**!")

        attacker["energy"] -= skill["cost"]
        stype = skill["type"]

        if stype == "damage":
            # Aplicar buff de ATK temporal si existe (Carga Estelar de Alex)
            bonus_atk = attacker.pop("atk_buff", 0)
            # Bonus si el defensor está enredado
            entangle_bonus = 15 if defender.get("entangled") else 0
            effective_atk = attacker["atk"] + bonus_atk + entangle_bonus
            dmg = battle.calc_damage(effective_atk, defender["defense"], skill["power"])
            defender["hp"] = max(0, defender["hp"] - dmg)
            buff_txt = f" (⭐+{bonus_atk} ATK)" if bonus_atk else ""
            battle.log.append(f"⚔️ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**{buff_txt} → **{dmg}** daño!")
            battle.log.append(f"   _{skill['desc']}_")
            # revive_poisoner: figura revivida por 1x envenena al atacar
            if attacker.get("revive_poisoner"):
                if "dots" not in defender: defender["dots"] = []
                defender["dots"].append({"dmg": 6, "turns": 3})
                battle.log.append(f"   ☠️ ¡**{attacker['name']}** (revivida) envenena a **{defender['name']}**! (6 daño/turno x3)")

            # self_heal: Caine se cura al hacer daño
            if skill.get("self_heal") and not attacker.get("no_heal"):
                heal_amt = skill["self_heal"]
                attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + heal_amt)
                battle.log.append(f"   💚 **{attacker['name']}** se cura **{heal_amt}** HP!")

            # ¿El defensor está en parry o retribución? → contraataca
            if defender.get("retributing"):
                retrib_dmg = max(1, dmg // 2)
                attacker["hp"] = max(0, attacker["hp"] - retrib_dmg)
                defender["retrib_turns"] = defender.get("retrib_turns", 1) - 1
                if defender["retrib_turns"] <= 0:
                    defender["retributing"] = False
                battle.log.append(f"   🦷 **{defender['emoji']} {defender['name']}** devuelve **{retrib_dmg}** daño (¡Retribución!)!")

            if defender.get("parrying"):
                defender["parrying"] = False
                if defender.get("parry_return_half"):
                    defender.pop("parry_return_half", None)
                    counter_dmg = max(1, dmg // 2)
                    attacker["hp"] = max(0, attacker["hp"] - counter_dmg)
                    battle.log.append(f"   🦊 **{defender['emoji']} {defender['name']}** hace **COUNTER** y devuelve **{counter_dmg}** daño (mitad del recibido)!")
                elif defender.get("parry_flat_bonus") is not None:
                    counter_dmg = max(1, dmg + defender["parry_flat_bonus"])
                    defender.pop("parry_flat_bonus", None)
                    attacker["hp"] = max(0, attacker["hp"] - counter_dmg)
                    battle.log.append(f"   ⚡ **{defender['emoji']} {defender['name']}** hace **PARRY** y devuelve **{counter_dmg}** daño (tu daño +10)!")
                else:
                    pct = defender.get("parry_dmg_pct", 25)
                    counter_dmg = int(defender["max_hp"] * pct / 100)
                    attacker["hp"] = max(0, attacker["hp"] - counter_dmg)
                    battle.log.append(f"   ⚡ **{defender['emoji']} {defender['name']}** hace **COUNTER** y devuelve **{counter_dmg}** daño ({pct}% HP)!")

            # Entangle: la figura queda enredada (aliados le hacen más daño)
            if skill.get("entangle"):
                defender["entangled"] = True
                battle.log.append(f"   🕸️ ¡**{defender['name']}** queda enredado! Los aliados le harán +15 daño!")

            # Efecto stun (con soporte de stun_turns extendido)
            if skill.get("stun") and not defender.get("stun_immune"):
                stun_t = skill.get("stun_turns", 1)
                if stun_t > 1:
                    defender["stun_turns"] = stun_t
                    battle.log.append(f"   😵 ¡**{defender['name']}** queda aturdido {stun_t} turnos!")
                else:
                    defender["stunned"] = True
                    battle.log.append(f"   😵 ¡**{defender['name']}** queda aturdido 1 turno!")

            # Dot inline (Mass Infection de 1x1x1x1)
            if skill.get("dot"):
                if "dots" not in defender: defender["dots"] = []
                defender["dots"].append({"dmg": skill.get("dot_power", 8), "turns": skill.get("dot_turns", 4)})
                battle.log.append(f"   ☠️ ¡**{defender['name']}** infectado! ({skill.get('dot_power',8)} daño/turno x{skill.get('dot_turns',4)})")

            # Efecto AOE — daña a todo el equipo rival
            if skill.get("aoe"):
                def_team = battle.p2_team if battle.turn == 1 else battle.p1_team
                sec_power = skill.get("aoe_secondary_power", skill["power"])
                hit = []
                for fig in def_team:
                    if fig is not defender and fig["hp"] > 0:
                        sec_dmg = battle.calc_damage(attacker["atk"], fig["defense"], sec_power)
                        fig["hp"] = max(0, fig["hp"] - sec_dmg)
                        hit.append(f"{fig['emoji']} {fig['name']} -{sec_dmg}HP")
                if hit:
                    battle.log.append(f"   💥 AOE: {' | '.join(hit)}")

            # Efecto force_switch — bloquea la figura golpeada N turnos
            if skill.get("force_switch"):
                turns = skill.get("force_switch_turns", 3)
                def_team = battle.p2_team if battle.turn == 1 else battle.p1_team
                for fig in def_team:
                    if fig is defender:
                        fig["force_locked"] = turns
                        break
                # Forzar cambio al siguiente disponible no bloqueado
                def_idx_attr = "p2_active" if battle.turn == 1 else "p1_active"
                current_idx = getattr(battle, def_idx_attr)
                for i, fig in enumerate(def_team):
                    if fig["hp"] > 0 and not fig.get("force_locked", 0) > 0 and i != current_idx:
                        setattr(battle, def_idx_attr, i)
                        battle.log.append(f"   🔒 ¡**{defender['name']}** bloqueada {turns} turnos! Entra **{fig['emoji']} {fig['name']}**!")
                        break
                else:
                    battle.log.append(f"   🔒 ¡**{defender['name']}** bloqueada {turns} turnos!")

        elif stype == "heal":
            # Respetar no_heal
            if attacker.get("no_heal"):
                battle.log.append(f"❌ **{attacker['name']}** no puede recuperar vida hasta el fin de la batalla!")
            else:
                heal = int(skill["power"] + random.randint(-2, 5))
                attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + heal)
                battle.log.append(f"💚 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → +**{heal}** HP!")
            # Curación a compañeros
            if skill.get("team_heal"):
                t_heal = skill.get("team_heal_power", 10)
                healed = []
                for ally in atk_team:
                    if ally is not attacker and ally["hp"] > 0:
                        ally["hp"] = min(ally["max_hp"], ally["hp"] + t_heal)
                        healed.append(f"{ally['emoji']} {ally['name']} +{t_heal}HP")
                if healed:
                    battle.log.append(f"   💚 Compañeros curados: {', '.join(healed)}")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "drain":
            self_dmg = skill["power"]
            bar_bonus = skill.get("bar_bonus", 20)
            attacker["hp"] = max(1, attacker["hp"] - self_dmg)
            attacker["energy"] = min(ENERGY_MAX, attacker["energy"] + bar_bonus)
            battle.log.append(f"⚡ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   -{self_dmg} HP propio | +{bar_bonus}⚡ extra! _{skill['desc']}_")

        elif stype == "drain_fill":
            self_dmg = skill["power"]
            enemy_dmg = skill.get("dmg_enemy", 0)
            attacker["hp"] = max(1, attacker["hp"] - self_dmg)
            if skill.get("no_heal"):
                attacker["no_heal"] = True
            if skill.get("fill_bar"):
                attacker["energy"] = ENERGY_MAX
            if enemy_dmg > 0:
                defender["hp"] = max(0, defender["hp"] - enemy_dmg)
            battle.log.append(f"🔴 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   -{self_dmg} HP propio (¡irrecuperable!) | -{enemy_dmg} al rival | ¡Barra al máximo!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "team_atk_buff":
            # Heroic Pose — buff de ATK acumulable al equipo completo
            buff = skill.get("atk_buff", 15)
            for ally in atk_team:
                if ally["hp"] > 0:
                    ally["atk_buff"] = ally.get("atk_buff", 0) + buff
            battle.log.append(f"⭐ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   Todo el equipo gana +{buff} ATK (acumulable, se consume al atacar)!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "dot":
            # Throwable Bomb — daño por turnos acumulable
            dot_dmg = skill["power"]
            dot_turns = skill.get("dot_turns", 3)
            if "dots" not in defender:
                defender["dots"] = []
            defender["dots"].append({"dmg": dot_dmg, "turns": dot_turns})
            battle.log.append(f"💣 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   ¡{dot_dmg} de daño por turno durante {dot_turns} turnos! (¡Acumulable!)")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "bad_update":
            # Roblox — daño aleatorio a enemigos + cura aliados
            def_team = battle.p2_team if battle.turn == 1 else battle.p1_team
            dmg_roll = random.choice([4, 6, 8])
            heal_roll = dmg_roll // 2
            dmg_hits = []
            for fig in def_team:
                if fig["hp"] > 0:
                    fig["hp"] = max(0, fig["hp"] - dmg_roll)
                    dmg_hits.append(f"{fig['emoji']} -{dmg_roll}HP")
            heal_hits = []
            for ally in atk_team:
                if ally["hp"] > 0 and not ally.get("no_heal"):
                    ally["hp"] = min(ally["max_hp"], ally["hp"] + heal_roll)
                    heal_hits.append(f"{ally['emoji']} +{heal_roll}HP")
            battle.log.append(f"🔳 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** (daño: {dmg_roll})!")
            if dmg_hits: battle.log.append(f"   💥 Enemigos: {' | '.join(dmg_hits)}")
            if heal_hits: battle.log.append(f"   💚 Aliados: {' | '.join(heal_hits)}")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "fly_away":
            # Tails — bloquea a Tails y al rival 3 turnos, entran sustitutos
            turns = skill.get("fly_turns", 3)
            attacker["force_locked"] = turns
            defender["force_locked"] = turns
            battle.log.append(f"🦊 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   ✈️ ¡**{attacker['name']}** y **{defender['name']}** vuelan lejos {turns} turnos!")
            # Forzar cambio de figura del atacante
            atk_idx_attr = "p1_active" if battle.turn == 1 else "p2_active"
            cur_atk_idx = getattr(battle, atk_idx_attr)
            next_atk = battle.next_alive(atk_team, cur_atk_idx)
            if next_atk is not None:
                setattr(battle, atk_idx_attr, next_atk)
                new_atk = atk_team[next_atk]
                battle.log.append(f"   🔄 Entra **{new_atk['emoji']} {new_atk['name']}** por tu equipo!")
            # Forzar cambio de figura del defensor
            def_team_fw = battle.p2_team if battle.turn == 1 else battle.p1_team
            def_idx_attr_fw = "p2_active" if battle.turn == 1 else "p1_active"
            cur_def_idx = getattr(battle, def_idx_attr_fw)
            next_def = battle.next_alive(def_team_fw, cur_def_idx)
            if next_def is not None:
                setattr(battle, def_idx_attr_fw, next_def)
                new_def = def_team_fw[next_def]
                battle.log.append(f"   🔄 Entra **{new_def['emoji']} {new_def['name']}** por el equipo rival!")
            elif battle.next_alive(def_team_fw, -1) is None:
                # Todo el equipo rival bloqueado = victoria
                await end_battle(interaction, battle, channel_id, winner_turn=battle.turn)
                return

        elif stype == "retribution":
            # Caine — Retributional Ringmaster: devuelve mitad del daño recibido 1 turno
            attacker["retributing"] = True
            attacker["retrib_turns"] = skill.get("retrib_turns", 1)
            battle.log.append(f"🦷 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   ¡Caine está listo para devolver la mitad del daño que reciba!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "michi_counter":
            # MichiBug — Counter: devuelve mitad del daño, 20% de que el rival no ataque
            evade = skill.get("evade_chance", 20)
            if random.randint(1, 100) <= evade:
                # El rival pierde su turno
                defender["stunned"] = True
                battle.log.append(f"🦊 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
                battle.log.append(f"   ✨ ¡**{defender['name']}** ni siquiera llega a atacar! Pierde su turno.")
            else:
                # Funciona como parry normal: devuelve mitad del daño del rival
                attacker["parrying"] = True
                attacker["parry_return_half"] = True   # flag especial: devuelve mitad del dmg recibido
                battle.log.append(f"🦊 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** y espera el ataque...")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "glitch_dmg":
            # MichiBug — Glitch Manipulation: daño aleatorio 2-45
            lo = skill.get("min_dmg", 2)
            hi = skill.get("max_dmg", 45)
            raw_dmg = random.randint(lo, hi)
            dmg = max(1, raw_dmg - (defender["defense"] // 4))
            defender["hp"] = max(0, defender["hp"] - dmg)
            battle.log.append(f"🌀 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → **{dmg}** daño! (roll: {raw_dmg})")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "corruption":
            # MichiBug — Corruption: copia habilidad aleatoria de cualquier figura
            all_skills = [(fig_key, sk) for fig_key, skills in FIGURE_SKILLS.items()
                          for sk in skills
                          if sk["type"] not in ("corruption",)]  # no puede copiarse a sí misma
            if all_skills:
                copied_fig_key, copied_skill = random.choice(all_skills)
                copied_fig_name = FIGURES.get(copied_fig_key, {}).get("name", copied_fig_key)
                battle.log.append(f"🌑 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
                battle.log.append(f"   ✨ ¡Copia **{copied_skill['name']}** de **{copied_fig_name}**!")
                # Ejecutar la habilidad copiada (recursión controlada)
                fake_skill = copied_skill.copy()
                # Reutilizar la lógica ejecutando inline el tipo copiado
                cstype = fake_skill["type"]
                if cstype == "damage":
                    dmg = battle.calc_damage(attacker["atk"], defender["defense"], fake_skill.get("power", 20))
                    defender["hp"] = max(0, defender["hp"] - dmg)
                    battle.log.append(f"   ⚔️ Daño copiado: **{dmg}**!")
                    if fake_skill.get("aoe"):
                        def_team_c = battle.p2_team if battle.turn == 1 else battle.p1_team
                        sec = fake_skill.get("aoe_secondary_power", fake_skill.get("power", 10))
                        for fig in def_team_c:
                            if fig is not defender and fig["hp"] > 0:
                                sd = battle.calc_damage(attacker["atk"], fig["defense"], sec)
                                fig["hp"] = max(0, fig["hp"] - sd)
                                battle.log.append(f"   💥 AOE → {fig['emoji']} -{sd}HP")
                elif cstype == "heal":
                    if not attacker.get("no_heal"):
                        heal = max(1, int(fake_skill.get("power", 20) + random.randint(-3, 5)))
                        attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + heal)
                        battle.log.append(f"   💚 Curación copiada: +**{heal}** HP!")
                elif cstype == "dot":
                    if "dots" not in defender: defender["dots"] = []
                    defender["dots"].append({"dmg": fake_skill.get("power", 10), "turns": fake_skill.get("dot_turns", 3)})
                    battle.log.append(f"   💣 DOT copiado: {fake_skill.get('power',10)} daño/turno x{fake_skill.get('dot_turns',3)}")
                elif cstype == "team_atk_buff":
                    buff = fake_skill.get("atk_buff", 10)
                    for ally in atk_team:
                        if ally["hp"] > 0:
                            ally["atk_buff"] = ally.get("atk_buff", 0) + buff
                    battle.log.append(f"   ⭐ Buff copiado: +{buff} ATK al equipo!")
                elif cstype == "drain_fill":
                    f_dmg = fake_skill.get("power", 15)
                    attacker["hp"] = max(1, attacker["hp"] - f_dmg)
                    if fake_skill.get("fill_bar"): attacker["energy"] = ENERGY_MAX
                    e_dmg = fake_skill.get("dmg_enemy", 0)
                    if e_dmg: defender["hp"] = max(0, defender["hp"] - e_dmg)
                    battle.log.append(f"   🔴 Drain copiado: -{f_dmg}HP propio, -{e_dmg} al rival!")
                elif cstype == "glitch_dmg":
                    raw = random.randint(fake_skill.get("min_dmg",2), fake_skill.get("max_dmg",45))
                    dmg = max(1, raw - (defender["defense"] // 4))
                    defender["hp"] = max(0, defender["hp"] - dmg)
                    battle.log.append(f"   🌀 Glitch copiado: **{dmg}** daño!")
                elif cstype == "bad_update":
                    dr = random.choice([4, 6, 8])
                    hr = dr // 2
                    def_team_c = battle.p2_team if battle.turn == 1 else battle.p1_team
                    for fig in def_team_c:
                        if fig["hp"] > 0: fig["hp"] = max(0, fig["hp"] - dr)
                    for ally in atk_team:
                        if ally["hp"] > 0 and not ally.get("no_heal"):
                            ally["hp"] = min(ally["max_hp"], ally["hp"] + hr)
                    battle.log.append(f"   🔳 Bad Update copiado: -{dr} a todos los rivales, +{hr} a aliados!")
                else:
                    # Para tipos complejos o raros, hace daño básico
                    dmg = max(1, attacker["atk"] - (defender["defense"] // 4) + random.randint(-2, 5))
                    defender["hp"] = max(0, defender["hp"] - dmg)
                    battle.log.append(f"   ⚔️ Efecto copiado (daño base): **{dmg}**!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "fast_kill":
            # Requiere 3 usos seguidos — al 3ro dispara
            charges = attacker.get("fast_kill_charges", 0) + 1
            needed = skill.get("charges_needed", 3)
            attacker["fast_kill_charges"] = charges
            if charges >= needed:
                attacker["fast_kill_charges"] = 0
                dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
                defender["hp"] = max(0, defender["hp"] - dmg)
                battle.log.append(f"🔪 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → ¡**{dmg}** DAÑO MASIVO!")
                battle.log.append(f"   _{skill['desc']}_")
            else:
                remaining = needed - charges
                battle.log.append(f"🔪 **{attacker['emoji']} {attacker['name']}** prepara **{skill['name']}**... ({charges}/{needed})")
                battle.log.append(f"   ¡{remaining} turno(s) más para activar!")

        elif stype == "revive_team":
            # 1x1x1x1 — se daña a sí mismo y revive figuras aliadas caídas
            self_dmg = skill["power"]
            attacker["hp"] = max(1, attacker["hp"] - self_dmg)
            revive_hp  = skill.get("revive_hp", 20)
            revive_atk = skill.get("revive_atk", 10)
            revive_def = skill.get("revive_def", 15)
            revived = []
            for ally in atk_team:
                if ally["hp"] <= 0 and ally is not attacker:
                    ally["hp"] = revive_hp
                    ally["atk"] = revive_atk
                    ally["defense"] = revive_def
                    ally["energy"] = 0
                    if skill.get("revive_poison"):
                        ally["revive_poisoner"] = True  # envenena al atacar
                    revived.append(f"{ally['emoji']} {ally['name']}")
            battle.log.append(f"⚔️ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** (-{self_dmg} HP propio)!")
            if revived:
                battle.log.append(f"   💀➡️💚 ¡Reviven: {', '.join(revived)}! (HP:{revive_hp} ATK:{revive_atk} DEF:{revive_def})")
                battle.log.append(f"   ☠️ ¡Las figuras revividas envenenarán al atacar!")
            else:
                battle.log.append(f"   No había figuras caídas que revivir.")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "heal_self_small":
            # Shedletsky — Chicken Leg: cura solo a sí mismo 20-25 HP
            heal_amt = random.randint(skill.get("heal_min", 20), skill.get("heal_max", 25))
            if not attacker.get("no_heal"):
                attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + heal_amt)
            battle.log.append(f"🍗 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   💚 {attacker['name']} se cura +{heal_amt}HP")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "heal_team_self":
            # Shedletsky — Chicken Legs: +30 propio, +25 aliados
            self_heal = skill["power"]
            team_heal = skill.get("team_heal_power", 25)
            if not attacker.get("no_heal"):
                attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + self_heal)
            healed = []
            for ally in atk_team:
                if ally is not attacker and ally["hp"] > 0 and not ally.get("no_heal"):
                    ally["hp"] = min(ally["max_hp"], ally["hp"] + team_heal)
                    healed.append(f"{ally['emoji']} {ally['name']} +{team_heal}HP")
            battle.log.append(f"🍗 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   💚 {attacker['name']} +{self_heal}HP | {' | '.join(healed) if healed else 'sin aliados vivos'}")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "switch_sword":
            # Shedletsky — muestra menú de espadas (se maneja en get_battle_view)
            # Este tipo no hace nada directamente — la selección se hace via botón especial
            battle.log.append(f"🐔 **{attacker['emoji']} {attacker['name']}** guarda su espada actual...")
            battle.log.append(f"   _(Elige tu espada en el menú)_")

        elif stype == "slash":
            # Shedletsky — ataca con la espada activa y aplica su efecto
            sword = attacker.get("active_sword", "linked")
            dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
            SWORD_NAMES = {
                "linked":      "Linked Sword",
                "firebrand":   "Firebrand 🔥",
                "venomshank":  "Venomshank ☠️",
                "windforce":   "Windforce 🌪️",
                "darkheart":   "Darkheart 🖤",
                "illumina":    "Illumina ✨",
                "ghostwalker": "Ghostwalker 👻",
                "ice_dagger":  "Ice Dagger 🧊",
            }
            sword_name = SWORD_NAMES.get(sword, "Linked Sword")
            defender["hp"] = max(0, defender["hp"] - dmg)
            battle.log.append(f"⚔️ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** con {sword_name} → **{dmg}** daño!")

            # Efectos de espada
            if sword == "linked":
                pass  # sin efecto extra
            elif sword == "firebrand":
                attacker["fire_immune"] = True
                # Carga de fuego: daño extra al lanzarse
                dash_dmg = battle.calc_damage(attacker["atk"], defender["defense"], 20)
                defender["hp"] = max(0, defender["hp"] - dash_dmg)
                battle.log.append(f"   🔥 ¡{attacker['name']} se lanza con Firebrand! +{dash_dmg} daño extra!")
                battle.log.append(f"   🔥 ¡{attacker['name']} es inmune a Ice Dagger!")
                # Si Shedletsky tiene menos del 30% HP → +30 ATK a aliados
                hp_pct = attacker["hp"] / attacker["max_hp"]
                if hp_pct < 0.30:
                    for ally in atk_team:
                        if ally is not attacker and ally["hp"] > 0:
                            ally["atk_buff"] = ally.get("atk_buff", 0) + 30
                    battle.log.append(f"   🔥 ¡Shedletsky a baja vida! +30 ATK a todos los aliados!")
            elif sword == "venomshank":
                if "dots" not in defender: defender["dots"] = []
                defender["dots"].append({"dmg": 8, "turns": 3})
                battle.log.append(f"   ☠️ ¡{defender['name']} envenenado! (8 daño/turno x3)")
            elif sword == "windforce":
                defender["stunned"] = True
                battle.log.append(f"   🌪️ ¡{defender['name']} empujado y aturdido 1 turno!")
            elif sword == "darkheart":
                lifesteal = max(1, int(dmg * 0.4))
                attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + lifesteal)
                battle.log.append(f"   🖤 Robo de vida: +{lifesteal} HP a {attacker['name']}!")
            elif sword == "illumina":
                illumina_dmg = battle.calc_damage(attacker["atk"], defender["defense"], 80)
                defender["hp"] = max(0, defender["hp"] - illumina_dmg)
                battle.log.append(f"   ✨ ¡Illumina hace daño masivo adicional! -{illumina_dmg} HP!")
            elif sword == "ghostwalker":
                kills = attacker.get("ghostwalker_kills", 0)
                bonus = kills * 5
                attacker["atk"] = attacker["atk"] + bonus if bonus > 0 else attacker["atk"]
                battle.log.append(f"   👻 Ghostwalker: +{bonus} ATK acumulado ({kills} kills)")
            elif sword == "ice_dagger":
                if not defender.get("fire_immune"):
                    ice_charges = attacker.get("ice_dagger_charges", 0) + 1
                    attacker["ice_dagger_charges"] = ice_charges
                    if ice_charges >= 3:
                        attacker["ice_dagger_charges"] = 0
                        ice_dmg = 120  # daño fijo al 3er toque
                        defender["hp"] = max(0, defender["hp"] - ice_dmg)
                        battle.log.append(f"   🧊❄️ ¡ICE DAGGER CARGADA! **{ice_dmg}** daño masivo de hielo!")
                    else:
                        battle.log.append(f"   🧊 Ice Dagger cargando... ({ice_charges}/3 — mantén la espada equipada!)")
                else:
                    attacker["ice_dagger_charges"] = 0
                    battle.log.append(f"   🧊 Ice Dagger bloqueada por Firebrand!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "consumed_fury":
            # 50 daño al activo + 15 splash + impostor pierde 50% vida
            dmg_fury = 50
            defender["hp"] = max(0, defender["hp"] - dmg_fury)
            def_team_fury = battle.p2_team if battle.turn == 1 else battle.p1_team
            splash = skill.get("splash_dmg", 15)
            hit = []
            for fig in def_team_fury:
                if fig is not defender and fig["hp"] > 0:
                    fig["hp"] = max(0, fig["hp"] - splash)
                    hit.append(f"{fig['emoji']} {fig['name']} -{splash}HP")
            # El impostor pierde 50% de su vida en lugar de morir
            self_dmg = max(1, attacker["max_hp"] // 2)
            attacker["hp"] = max(1, attacker["hp"] - self_dmg)
            battle.log.append(f"💥 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   💥 **{defender['name']}** recibe **{dmg_fury}** daño!")
            if hit:
                battle.log.append(f"   💥 Explosión: {' | '.join(hit)}")
            battle.log.append(f"   😵 **{attacker['name']}** pierde el 50% de su vida por la explosión!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "lobster":
            # 0.01% de probabilidad de matar a TODAS las figuras del oponente
            roll = random.randint(1, 10000)
            def_team = battle.p2_team if battle.turn == 1 else battle.p1_team
            if roll == 1:
                for fig in def_team:
                    fig["hp"] = 0
                battle.log.append(f"🦞 **Lobster** usa **LOBSTER**...")
                battle.log.append(f"   ...")
                battle.log.append(f"   🦞 **¡LA LANGOSTA LO HA HECHO! ¡TODAS LAS FIGURAS ENEMIGAS ESTÁN MUERTAS!** 🦞")
            else:
                battle.log.append(f"🦞 **Lobster** usa **LOBSTER**...")
                battle.log.append(f"   ...")
                battle.log.append(f"   No pasa nada. (Como siempre)")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "ban_hammer":
            # Roblox — 50/50: mata al enemigo activo O a un aliado
            roll = random.randint(1, 2)
            if roll == 1:
                defender["hp"] = 0
                battle.log.append(f"🔨 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
                battle.log.append(f"   💀 ¡**{defender['name']}** fue BANEADO! HP = 0!")
            else:
                alive_allies = [f for f in atk_team if f["hp"] > 0 and f is not attacker]
                if alive_allies:
                    victim = random.choice(alive_allies)
                    victim["hp"] = 0
                    battle.log.append(f"🔨 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**...")
                    battle.log.append(f"   💀 ¡El martillo se fue de lado y mató a **{victim['name']}** aliado! 😂")
                else:
                    # Solo queda Roblox — se auto-daña 40 HP
                    attacker["hp"] = max(1, attacker["hp"] - 40)
                    battle.log.append(f"🔨 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**...")
                    battle.log.append(f"   💥 ¡El martillo rebota contra sí mismo! **-40 HP** a Roblox!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "parry":
            # Alex — contraataca si el rival ataca en su siguiente turno
            attacker["parrying"] = True
            if "parry_flat_bonus" in skill:
                attacker["parry_flat_bonus"] = skill["parry_flat_bonus"]
                attacker.pop("parry_dmg_pct", None)
            else:
                attacker["parry_dmg_pct"] = skill.get("parry_dmg_pct", 25)
            battle.log.append(f"🛡️ **{attacker['emoji']} {attacker['name']}** se prepara para un **Parry**!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "buff":
            # Alex — Carga Estelar: potencia el próximo ataque
            attacker["atk_buff"] = skill.get("atk_buff", 15)
            battle.log.append(f"⭐ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   Su próximo ataque tendrá +{skill.get('atk_buff',15)} ATK!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "gamble":
            # AgustoLoco — Fumada: 50/50
            roll = random.randint(1, 2)
            if roll == 1:
                # Buena suerte: HP sube a 150, max temporal
                new_max = skill.get("gamble_heal", 150)
                attacker["max_hp"] = max(attacker["max_hp"], new_max)
                attacker["hp"] = new_max
                battle.log.append(f"🍀 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → ¡SUERTE! HP sube a {new_max}!")
            else:
                # Mala suerte: cae a 1 HP y pierde ATK
                attacker["hp"] = 1
                debuff = skill.get("gamble_atk_debuff", 5)
                attacker["atk"] = max(1, attacker["atk"] - debuff)
                battle.log.append(f"💀 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → ¡MAL VIAJE! Cae a 1 HP y pierde {debuff} ATK!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "gamble_fire":
            # AgustoLoco — Mechero: <1% de chance
            is_immune = defender.get("fire_immune", False)
            if is_immune:
                battle.log.append(f"🔥 **{attacker['emoji']} {attacker['name']}** intenta el **{skill['name']}**...")
                battle.log.append(f"   ❌ ¡El rival es **inmune al fuego**! No pasa nada.")
            else:
                chance = skill.get("fire_chance", 1)
                roll = random.randint(1, 100)
                if roll <= chance:
                    fire_dmg = skill.get("fire_dmg", 80)
                    defender["hp"] = max(0, defender["hp"] - fire_dmg)
                    battle.log.append(f"🔥🔥🔥 **¡EL MECHERO FUNCIONÓ!** **{attacker['name']}** quema al rival por **{fire_dmg}** daño!")
                else:
                    battle.log.append(f"🔥 **{attacker['emoji']} {attacker['name']}** intenta encender el mechero...")
                    battle.log.append(f"   💨 ...no funciona. (Como siempre)")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "clone_switch":
            # 007n7 — cambia tipo de clon
            types = ["def", "atk", "heal"]
            current = attacker.get("clone_type", "def")
            idx = types.index(current)
            nxt = types[(idx + 1) % 3]
            attacker["clone_type"] = nxt
            labels = {"def": "🛡️ DEF (bloquea 2 golpes)", "atk": "⚔️ ATK (parry mitad del daño)", "heal": "💚 HEAL (cura según daño recibido)"}
            battle.log.append(f"🔄 **{attacker['emoji']} {attacker['name']}** cambia tipo de clon → **{labels[nxt]}**!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "clone_action":
            # 007n7 — ejecuta según tipo activo
            ctype = attacker.get("clone_type", "def")
            if ctype == "def":
                attacker["clone_shield"] = 2
                battle.log.append(f"🍔 **{attacker['emoji']} {attacker['name']}** invoca un **Clon DEF**: ¡absorberá los próximos 2 golpes!")
            elif ctype == "atk":
                attacker["parrying"] = True
                attacker["parry_return_half"] = True
                battle.log.append(f"🍔 **{attacker['emoji']} {attacker['name']}** invoca un **Clon ATK**: ¡hará parry devolviendo mitad del daño!")
            elif ctype == "heal":
                attacker["clone_heal_on_hit"] = True
                battle.log.append(f"🍔 **{attacker['emoji']} {attacker['name']}** invoca un **Clon HEAL**: ¡se curará según el daño del próximo golpe!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "teleport_007":
            # 007n7 — se teletransporta, cede turnos, se cura 10/turno
            attacker["teleporting"] = True
            attacker["teleport_heals"] = 10
            battle.log.append(f"🌀 **{attacker['emoji']} {attacker['name']}** se **teletransporta** lejos, cediendo sus turnos!")
            battle.log.append(f"   Se curará 10 HP por turno hasta tener vida completa.")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "fling_brick":
            # c00lkidd — daño + reduce ATK rival, 20% fuerza cambio
            dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
            defender["hp"] = max(0, defender["hp"] - dmg)
            atk_reduction = 5
            defender["atk"] = max(1, defender.get("atk", 10) - atk_reduction)
            battle.log.append(f"🧱 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → **{dmg}** daño! ATK rival -{atk_reduction}!")
            if random.randint(1, 100) <= 20:
                def_team = battle.p2_team if battle.turn == 1 else battle.p1_team
                def_idx_attr = "p2_active" if battle.turn == 1 else "p1_active"
                current_idx = getattr(battle, def_idx_attr)
                next_idx = battle.next_alive(def_team, current_idx)
                if next_idx is not None and next_idx != current_idx:
                    setattr(battle, def_idx_attr, next_idx)
                    battle.log.append(f"   💥 ¡El ladrillo manda a volar a **{defender['name']}**! Entra **{def_team[next_idx]['emoji']} {def_team[next_idx]['name']}**!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "minion_shield":
            # c00lkidd — escudo de 2 golpes con contraataque
            attacker["minion_shield"] = 2
            battle.log.append(f"😎 **{attacker['emoji']} {attacker['name']}** invoca sus **Minions**: ¡escudo de 2 golpes!")
            battle.log.append(f"   Si el rival ataca, recibirá 10 daño + quemadura!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "backstab":
            # Two Time — daño + stun + recarga barra
            dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
            defender["hp"] = max(0, defender["hp"] - dmg)
            battle.log.append(f"🗡️ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → **{dmg}** daño!")
            if not defender.get("stun_immune"):
                defender["stunned"] = True
                battle.log.append(f"   😵 ¡**{defender['name']}** queda aturdido 1 turno!")
            bonus_bar = skill.get("bar_bonus", 20)
            attacker["energy"] = min(100, attacker["energy"] + bonus_bar)
            battle.log.append(f"   ⚡ **{attacker['name']}** recarga +{bonus_bar} energía!")
            # Contar backstabs para pasiva de revive
            attacker["backstab_count"] = attacker.get("backstab_count", 0) + 1
            if attacker.get("spawnpoint_active") and attacker["backstab_count"] >= 4 and attacker["energy"] >= 100:
                attacker["can_revive"] = True
                battle.log.append(f"   ⚡ ¡**{attacker['name']}** ha acumulado 4 backstabs con barra llena! **¡Pasiva de Respawn lista!**")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "spawnpoint":
            # Two Time — coloca punto de respawn
            attacker["spawnpoint_active"] = True
            attacker["backstab_count"] = attacker.get("backstab_count", 0)
            battle.log.append(f"🗡️ **{attacker['emoji']} {attacker['name']}** clava su daga y coloca un **Spawnpoint**!")
            battle.log.append(f"   Pasiva activa: 4 Backstabs con barra llena = revive con 50% HP.")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "crouch":
            # Two Time — se agacha: reduce daño recibido, buff ATK 2 turnos
            attacker["crouching"] = True
            attacker["atk_buff"] = attacker.get("atk_buff", 0) + 15
            battle.log.append(f"🗡️ **{attacker['emoji']} {attacker['name']}** se agacha (menos daño recibido este turno, +15 ATK por 2 turnos)!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "voidstar":
            # Noli — daño + prepara próximo ataque para +15
            dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
            defender["hp"] = max(0, defender["hp"] - dmg)
            attacker["voidstar_charged"] = True
            battle.log.append(f"✨ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → **{dmg}** daño! ¡Próximo ataque +15!")
            # Pasiva de alucinaciones: 20% de que rival falle
            if attacker.get("key") == "noli" or attacker.get("hallucination_aura"):
                defender["hallucinated"] = True
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "voidrush":
            # Noli — daño, +15 si rival tiene alucinaciones
            bonus = 15 if defender.get("hallucinated") else 0
            total_power = skill["power"] + bonus
            dmg = battle.calc_damage(attacker["atk"], defender["defense"], total_power)
            defender["hp"] = max(0, defender["hp"] - dmg)
            bonus_txt = f" (¡+15 Alucinaciones!)" if bonus else ""
            battle.log.append(f"✨ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**{bonus_txt} → **{dmg}** daño!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "observant":
            # Noli — desaparece 5 turnos, genera alucinaciones
            attacker["observant_turns"] = 5
            attacker["observant_dmg_ready"] = False
            defender["hallucinated"] = True
            battle.log.append(f"✨ **{attacker['emoji']} {attacker['name']}** **desaparece** entre alucinaciones por 5 turnos!")
            battle.log.append(f"   🌀 El rival queda alucinado. Al volver, Noli hará daño masivo.")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "guest_block":
            # Guest1337 — bloquea próximo ataque + gana carga
            attacker["blocking"] = True
            attacker["punch_charges"] = attacker.get("punch_charges", 0) + 1
            battle.log.append(f"👊 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**: ¡bloqueará el próximo ataque!")
            battle.log.append(f"   Cargas de Punch: {attacker['punch_charges']}")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "guest_punch":
            # Guest1337 — requiere carga, 55 daño + stun 2 turnos
            if not attacker.get("punch_charges", 0) > 0:
                battle.log.append(f"❌ **{attacker['name']}**: ¡Necesitas una carga de **Block** para usar Punch!")
            else:
                attacker["punch_charges"] -= 1
                dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
                defender["hp"] = max(0, defender["hp"] - dmg)
                stun_t = skill.get("stun_turns", 2)
                defender["stun_turns"] = stun_t
                battle.log.append(f"👊 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → **{dmg}** daño! ¡Stun {stun_t} turnos!")
                battle.log.append(f"   _{skill['desc']}_")

        elif stype == "bloxy_cola":
            # Noob — +15 energía extra por turno por 2 turnos
            attacker["energy_bonus_temp"] = attacker.get("energy_bonus_temp", 0) + 15
            attacker["energy_bonus_turns"] = 2
            battle.log.append(f"😃 **{attacker['emoji']} {attacker['name']}** bebe la **Bloxy Cola**: +15 energía/turno por 2 turnos!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "slateskin":
            # Noob — próximo golpe recibido: mitad daño + devuelve mitad
            attacker["slateskin"] = True
            battle.log.append(f"😃 **{attacker['emoji']} {attacker['name']}** toma la **Slateskin**: ¡el próximo ataque hará mitad del daño y lo devolverá!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "ghostburger":
            # Noob — evasión aumentada + 10 HP/turno por 4 turnos
            attacker["ghostburger_turns"] = 4
            attacker["evade_chance"] = attacker.get("evade_chance", 0) + 30
            battle.log.append(f"😃 **{attacker['emoji']} {attacker['name']}** come la **GhostBurger**: ¡+30% evasión y se curará 10 HP/turno x4!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "coin_flip":
            # Chance — cara = carga, sello = rival hace más daño
            roll = random.randint(1, 2)
            if roll == 1:
                charges = min(3, attacker.get("coin_charges", 0) + 1)
                attacker["coin_charges"] = charges
                battle.log.append(f"🔫 **{attacker['emoji']} {attacker['name']}** gira la moneda → **¡CARA!** Cargas: {charges}/3")
            else:
                attacker["coin_debuff"] = True
                battle.log.append(f"🔫 **{attacker['emoji']} {attacker['name']}** gira la moneda → **SELLO**. El próximo ataque le hará más daño!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "gun_shot":
            # Chance — dispara con prob según cargas
            charges = attacker.get("coin_charges", 0)
            if charges == 0:
                battle.log.append(f"🔫 **{attacker['emoji']} {attacker['name']}** intenta disparar... sin cargas. ¡Nada!")
            else:
                prob = {1: 40, 2: 70, 3: 100}.get(charges, 40)
                roll = random.randint(1, 100)
                if roll <= prob:
                    attacker["coin_charges"] = 0
                    dmg = battle.calc_damage(attacker["atk"], defender["defense"], 60)
                    defender["hp"] = max(0, defender["hp"] - dmg)
                    stun_t = 2
                    defender["stun_turns"] = stun_t
                    battle.log.append(f"🔫 **{attacker['emoji']} {attacker['name']}** **DISPARA** → **{dmg}** daño! ¡Stun {stun_t} turnos! ({prob}% probabilidad)")
                elif charges < 3 and random.randint(1, 100) <= 30:
                    attacker["coin_charges"] = 0
                    self_dmg = 20
                    attacker["hp"] = max(1, attacker["hp"] - self_dmg)
                    battle.log.append(f"💥 **¡La pistola de {attacker['name']} explotó en su cara!** -{self_dmg} HP!")
                else:
                    battle.log.append(f"🔫 **{attacker['emoji']} {attacker['name']}** dispara... ¡Falla! ({100-prob}% sin disparo)")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "reload_stats":
            # Chance — cambia su vida aleatoriamente
            new_hp = random.randint(150, 250)
            old_hp = attacker["hp"]
            attacker["max_hp"] = new_hp
            attacker["hp"] = min(attacker["hp"], new_hp) if attacker["hp"] > new_hp else new_hp
            attacker["coin_charges"] = 0  # también recarga el revólver
            battle.log.append(f"🔫 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   ¡Nueva vida máxima: **{new_hp}** HP! (tenía {old_hp}) ¡Revólver recargado!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "spikes":
            # John Doe — daño + bloquea 2 ataques + John pierde 20 HP
            self_cost = 20
            attacker["hp"] = max(1, attacker["hp"] - self_cost)
            dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
            defender["hp"] = max(0, defender["hp"] - dmg)
            attacker["spike_shield"] = 2
            battle.log.append(f"💢 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → **{dmg}** daño + escudo 2 golpes! (-{self_cost} HP propio)")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "error404":
            # John Doe — -10 HP propio, barra llena, +20 ATK 4 turnos
            self_cost = 10
            attacker["hp"] = max(1, attacker["hp"] - self_cost)
            attacker["energy"] = 100
            attacker["atk_buff_turns"] = 4
            attacker["atk_buff_amount"] = 20
            attacker["atk"] = attacker["atk"] + 20
            battle.log.append(f"💢 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** (-{self_cost} HP)!")
            battle.log.append(f"   ⚡ ¡Barra llena! +20 ATK por 4 turnos!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "traps":
            # John Doe — requiere 3 usos
            charges = attacker.get("trap_charges", 0) + 1
            attacker["trap_charges"] = charges
            if charges >= 3:
                attacker["trap_charges"] = 0
                if "dots" not in defender: defender["dots"] = []
                for _ in range(3):
                    defender["dots"].append({"dmg": 20, "turns": 1})
                battle.log.append(f"💢 **{attacker['emoji']} {attacker['name']}** activa la **TRAMPA**! ¡20 daño/turno x3!")
            else:
                battle.log.append(f"💢 **{attacker['emoji']} {attacker['name']}** coloca una trampa... ({charges}/3)")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "crystal_switch":
            # Jane Doe — cambia tipo de cristal
            current = attacker.get("crystal_type", "damage")
            nxt = "heal" if current == "damage" else "damage"
            attacker["crystal_type"] = nxt
            labels = {"damage": "⚔️ DAÑO (stun + 20 daño)", "heal": "💚 CURACIÓN (cura aliado con menos HP + inmunidad)"}
            battle.log.append(f"🪓 **{attacker['emoji']} {attacker['name']}** cambia cristal → **{labels[nxt]}**!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "crystal_throw":
            # Jane Doe — ejecuta según tipo activo
            ctype = attacker.get("crystal_type", "damage")
            if ctype == "damage":
                dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
                defender["hp"] = max(0, defender["hp"] - dmg)
                defender["stun_turns"] = 3
                battle.log.append(f"🪓 **{attacker['emoji']} {attacker['name']}** lanza **Cristal de Daño** → **{dmg}** daño + stun 3 turnos!")
                # Pasiva Resonancia
                defender["resonance"] = defender.get("resonance", 0) + 1
                res = defender["resonance"]
                defender["atk"] = max(1, defender["atk"] - 3)
                battle.log.append(f"   💜 Resonancia x{res}: ATK rival -3, daño recibido aumentado!")
            else:
                # Cura al aliado con menos HP
                ally_team = atk_team
                weakest = min((f for f in ally_team if f["hp"] > 0), key=lambda f: f["hp"], default=None)
                if weakest:
                    heal_amt = 20
                    weakest["hp"] = min(weakest["max_hp"], weakest["hp"] + heal_amt)
                    weakest["immune_turns"] = 3
                    battle.log.append(f"🪓 **{attacker['emoji']} {attacker['name']}** lanza **Cristal de Curación** → **{weakest['emoji']} {weakest['name']}** +{heal_amt} HP + inmunidad 3 turnos!")
                else:
                    battle.log.append(f"🪓 No hay aliados que curar.")
            battle.log.append(f"   _{skill['desc']}_")

    # ¿Cayó el defensor?
    if defender["hp"] <= 0:
        # Pasiva de Gamer64: revive una vez con 80% HP
        if defender.get("passive_revive"):
            defender["passive_revive"] = False   # ya usó la pasiva
            revive_hp = max(1, int(defender["max_hp"] * 0.80))
            defender["hp"] = revive_hp
            defender["energy"] = 0
            battle.log.append(f"💫 **{defender['emoji']} {defender['name']}** se cansó de rodeos, ¡se arranca el brazo y entra a su **Fase 2**!")
            battle.log.append(f"   Se levanta con **{revive_hp} HP** (80% de su vida máxima)!")
            battle.turn = 2 if battle.turn == 1 else 1
            await finish_turn(interaction, battle, channel_id)
            return

        def_team = battle.p2_team if battle.turn == 1 else battle.p1_team
        def_idx_attr = "p2_active" if battle.turn == 1 else "p1_active"
        current_def_idx = getattr(battle, def_idx_attr)
        next_idx = battle.next_alive(def_team, current_def_idx)

        if next_idx is not None:
            setattr(battle, def_idx_attr, next_idx)
            new_fig = def_team[next_idx]
            battle.log.append(f"💀 **{defender['name']}** fue derrotado!")
            battle.log.append(f"🔄 ¡Entra **{new_fig['emoji']} {new_fig['name']}**!")
            battle.turn = 2 if battle.turn == 1 else 1
            await finish_turn(interaction, battle, channel_id)
            return
        else:
            await end_battle(interaction, battle, channel_id, winner_turn=battle.turn)
            return

    # Cambiar turno
    battle.turn = 2 if battle.turn == 1 else 1
    await finish_turn(interaction, battle, channel_id)

async def finish_turn(interaction, battle: BattleState, channel_id: int):
    """Actualiza el embed y, si toca el bot, ejecuta su turno."""
    if battle.is_bot and battle.turn == 2:
        embed = battle.get_embed()
        await interaction.response.edit_message(embed=embed, view=None)
        await asyncio.sleep(1.2)
        await bot_turn(interaction, battle, channel_id)
        return

    view = get_battle_view(battle)
    embed = battle.get_embed()
    await interaction.response.edit_message(embed=embed, view=view)

async def bot_turn(interaction, battle: BattleState, channel_id: int):
    """IA del bot: ataque básico siempre disponible + habilidades cuando hay energía."""
    f = battle.current_p2()
    p1_fig = battle.current_p1()
    battle.log = []

    # Filtrar habilidades disponibles
    available = [i for i, sk in enumerate(f["skills"]) if f["energy"] >= sk["cost"]]

    # Prioridad: curación si HP < 40%
    chosen_idx = None
    hp_ratio = f["hp"] / f["max_hp"]
    if hp_ratio < 0.4:
        heal_skills = [i for i in available if f["skills"][i]["type"] in ("heal",)]
        if heal_skills:
            chosen_idx = heal_skills[-1]

    # Si hay habilidad disponible y no eligió curar, usarla con 60% de probabilidad
    if chosen_idx is None and available and random.random() < 0.6:
        chosen_idx = max(available, key=lambda i: f["skills"][i]["cost"])

    if chosen_idx is not None:
        # Usar habilidad especial
        skill = f["skills"][chosen_idx]
        f["energy"] -= skill["cost"]
        stype = skill["type"]

        if stype == "damage":
            dmg = battle.calc_damage(f["atk"], p1_fig["defense"], skill["power"])
            p1_fig["hp"] = max(0, p1_fig["hp"] - dmg)
            battle.log.append(f"🤖 **{f['emoji']} {f['name']}** usa **{skill['name']}** → **{dmg}** daño!")
            if skill.get("stun"):
                stun_t = skill.get("stun_turns", 1)
                if stun_t > 1:
                    p1_fig["stun_turns"] = stun_t
                else:
                    p1_fig["stunned"] = True
                battle.log.append(f"   😵 ¡**{p1_fig['name']}** queda aturdido!")
            if skill.get("aoe"):
                sec = skill.get("aoe_secondary_power", skill["power"])
                for fig in battle.p1_team:
                    if fig is not p1_fig and fig["hp"] > 0:
                        sd = battle.calc_damage(f["atk"], fig["defense"], sec)
                        fig["hp"] = max(0, fig["hp"] - sd)
                        battle.log.append(f"   💥 AOE → {fig['emoji']} {fig['name']} -{sd}HP")
            if skill.get("force_switch"):
                turns = skill.get("force_switch_turns", 3)
                p1_fig["force_locked"] = turns
                next_idx = battle.next_alive(battle.p1_team, battle.p1_active)
                if next_idx:
                    battle.p1_active = next_idx
                    battle.log.append(f"   🔒 **{p1_fig['name']}** bloqueada {turns} turnos!")

        elif stype == "heal":
            heal = max(1, int(skill["power"] + random.randint(-3, 5)))
            if not f.get("no_heal"):
                f["hp"] = min(f["max_hp"], f["hp"] + heal)
                battle.log.append(f"🤖 **{f['emoji']} {f['name']}** usa **{skill['name']}** → +**{heal}** HP!")
            if skill.get("team_heal"):
                th = skill.get("team_heal_power", 10)
                for ally in battle.p2_team:
                    if ally is not f and ally["hp"] > 0:
                        ally["hp"] = min(ally["max_hp"], ally["hp"] + th)

        elif stype == "drain":
            f["hp"] = max(1, f["hp"] - skill["power"])
            bonus = skill.get("bar_bonus", 20)
            f["energy"] = min(ENERGY_MAX, f["energy"] + bonus)
            battle.log.append(f"🤖 **{f['emoji']} {f['name']}** usa **{skill['name']}**! (+{bonus}⚡)")

        elif stype == "drain_fill":
            f["hp"] = max(1, f["hp"] - skill["power"])
            if skill.get("fill_bar"): f["energy"] = ENERGY_MAX
            if skill.get("no_heal"): f["no_heal"] = True
            ed = skill.get("dmg_enemy", 0)
            if ed > 0:
                p1_fig["hp"] = max(0, p1_fig["hp"] - ed)
            battle.log.append(f"🤖 **{f['emoji']} {f['name']}** usa **{skill['name']}**! (-{skill['power']}HP propio, -{ed} al rival)")

        elif stype == "dot":
            if "dots" not in p1_fig: p1_fig["dots"] = []
            p1_fig["dots"].append({"dmg": skill["power"], "turns": skill.get("dot_turns", 3)})
            battle.log.append(f"🤖 **{f['emoji']} {f['name']}** usa **{skill['name']}**! ({skill['power']} daño/turno x{skill.get('dot_turns',3)})")

        elif stype == "team_atk_buff":
            buff = skill.get("atk_buff", 15)
            for ally in battle.p2_team:
                if ally["hp"] > 0:
                    ally["atk_buff"] = ally.get("atk_buff", 0) + buff
            battle.log.append(f"🤖 **{f['emoji']} {f['name']}** usa **{skill['name']}**! (Todo el equipo +{buff} ATK)")

        elif stype == "bad_update":
            dmg_roll = random.choice([4, 6, 8])
            heal_roll = dmg_roll // 2
            for fig in battle.p1_team:
                if fig["hp"] > 0:
                    fig["hp"] = max(0, fig["hp"] - dmg_roll)
            for ally in battle.p2_team:
                if ally["hp"] > 0 and not ally.get("no_heal"):
                    ally["hp"] = min(ally["max_hp"], ally["hp"] + heal_roll)
            battle.log.append(f"🤖 **{f['emoji']} {f['name']}** usa **{skill['name']}**! ({dmg_roll} a todos los rivales, +{heal_roll} a aliados)")

        elif stype == "fast_kill":
            # Requiere 3 usos seguidos — al 3ro dispara
            charges = attacker.get("fast_kill_charges", 0) + 1
            needed = skill.get("charges_needed", 3)
            attacker["fast_kill_charges"] = charges
            if charges >= needed:
                attacker["fast_kill_charges"] = 0
                dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
                defender["hp"] = max(0, defender["hp"] - dmg)
                battle.log.append(f"🔪 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** → ¡**{dmg}** DAÑO MASIVO!")
                battle.log.append(f"   _{skill['desc']}_")
            else:
                remaining = needed - charges
                battle.log.append(f"🔪 **{attacker['emoji']} {attacker['name']}** prepara **{skill['name']}**... ({charges}/{needed})")
                battle.log.append(f"   ¡{remaining} turno(s) más para activar!")

        elif stype == "revive_team":
            # 1x1x1x1 — se daña a sí mismo y revive figuras aliadas caídas
            self_dmg = skill["power"]
            attacker["hp"] = max(1, attacker["hp"] - self_dmg)
            revive_hp  = skill.get("revive_hp", 20)
            revive_atk = skill.get("revive_atk", 10)
            revive_def = skill.get("revive_def", 15)
            revived = []
            for ally in atk_team:
                if ally["hp"] <= 0 and ally is not attacker:
                    ally["hp"] = revive_hp
                    ally["atk"] = revive_atk
                    ally["defense"] = revive_def
                    ally["energy"] = 0
                    if skill.get("revive_poison"):
                        ally["revive_poisoner"] = True  # envenena al atacar
                    revived.append(f"{ally['emoji']} {ally['name']}")
            battle.log.append(f"⚔️ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** (-{self_dmg} HP propio)!")
            if revived:
                battle.log.append(f"   💀➡️💚 ¡Reviven: {', '.join(revived)}! (HP:{revive_hp} ATK:{revive_atk} DEF:{revive_def})")
                battle.log.append(f"   ☠️ ¡Las figuras revividas envenenarán al atacar!")
            else:
                battle.log.append(f"   No había figuras caídas que revivir.")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "heal_self_small":
            # Shedletsky — Chicken Leg: cura solo a sí mismo 20-25 HP
            heal_amt = random.randint(skill.get("heal_min", 20), skill.get("heal_max", 25))
            if not attacker.get("no_heal"):
                attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + heal_amt)
            battle.log.append(f"🍗 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   💚 {attacker['name']} se cura +{heal_amt}HP")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "heal_team_self":
            # Shedletsky — Chicken Legs: +30 propio, +25 aliados
            self_heal = skill["power"]
            team_heal = skill.get("team_heal_power", 25)
            if not attacker.get("no_heal"):
                attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + self_heal)
            healed = []
            for ally in atk_team:
                if ally is not attacker and ally["hp"] > 0 and not ally.get("no_heal"):
                    ally["hp"] = min(ally["max_hp"], ally["hp"] + team_heal)
                    healed.append(f"{ally['emoji']} {ally['name']} +{team_heal}HP")
            battle.log.append(f"🍗 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   💚 {attacker['name']} +{self_heal}HP | {' | '.join(healed) if healed else 'sin aliados vivos'}")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "switch_sword":
            # Shedletsky — muestra menú de espadas (se maneja en get_battle_view)
            # Este tipo no hace nada directamente — la selección se hace via botón especial
            battle.log.append(f"🐔 **{attacker['emoji']} {attacker['name']}** guarda su espada actual...")
            battle.log.append(f"   _(Elige tu espada en el menú)_")

        elif stype == "slash":
            # Shedletsky — ataca con la espada activa y aplica su efecto
            sword = attacker.get("active_sword", "linked")
            dmg = battle.calc_damage(attacker["atk"], defender["defense"], skill["power"])
            SWORD_NAMES = {
                "linked":      "Linked Sword",
                "firebrand":   "Firebrand 🔥",
                "venomshank":  "Venomshank ☠️",
                "windforce":   "Windforce 🌪️",
                "darkheart":   "Darkheart 🖤",
                "illumina":    "Illumina ✨",
                "ghostwalker": "Ghostwalker 👻",
                "ice_dagger":  "Ice Dagger 🧊",
            }
            sword_name = SWORD_NAMES.get(sword, "Linked Sword")
            defender["hp"] = max(0, defender["hp"] - dmg)
            battle.log.append(f"⚔️ **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}** con {sword_name} → **{dmg}** daño!")

            # Efectos de espada
            if sword == "linked":
                pass  # sin efecto extra
            elif sword == "firebrand":
                attacker["fire_immune"] = True
                # Carga de fuego: daño extra al lanzarse
                dash_dmg = battle.calc_damage(attacker["atk"], defender["defense"], 20)
                defender["hp"] = max(0, defender["hp"] - dash_dmg)
                battle.log.append(f"   🔥 ¡{attacker['name']} se lanza con Firebrand! +{dash_dmg} daño extra!")
                battle.log.append(f"   🔥 ¡{attacker['name']} es inmune a Ice Dagger!")
                # Si Shedletsky tiene menos del 30% HP → +30 ATK a aliados
                hp_pct = attacker["hp"] / attacker["max_hp"]
                if hp_pct < 0.30:
                    for ally in atk_team:
                        if ally is not attacker and ally["hp"] > 0:
                            ally["atk_buff"] = ally.get("atk_buff", 0) + 30
                    battle.log.append(f"   🔥 ¡Shedletsky a baja vida! +30 ATK a todos los aliados!")
            elif sword == "venomshank":
                if "dots" not in defender: defender["dots"] = []
                defender["dots"].append({"dmg": 8, "turns": 3})
                battle.log.append(f"   ☠️ ¡{defender['name']} envenenado! (8 daño/turno x3)")
            elif sword == "windforce":
                defender["stunned"] = True
                battle.log.append(f"   🌪️ ¡{defender['name']} empujado y aturdido 1 turno!")
            elif sword == "darkheart":
                lifesteal = max(1, int(dmg * 0.4))
                attacker["hp"] = min(attacker["max_hp"], attacker["hp"] + lifesteal)
                battle.log.append(f"   🖤 Robo de vida: +{lifesteal} HP a {attacker['name']}!")
            elif sword == "illumina":
                illumina_dmg = battle.calc_damage(attacker["atk"], defender["defense"], 80)
                defender["hp"] = max(0, defender["hp"] - illumina_dmg)
                battle.log.append(f"   ✨ ¡Illumina hace daño masivo adicional! -{illumina_dmg} HP!")
            elif sword == "ghostwalker":
                kills = attacker.get("ghostwalker_kills", 0)
                bonus = kills * 5
                attacker["atk"] = attacker["atk"] + bonus if bonus > 0 else attacker["atk"]
                battle.log.append(f"   👻 Ghostwalker: +{bonus} ATK acumulado ({kills} kills)")
            elif sword == "ice_dagger":
                if not defender.get("fire_immune"):
                    ice_charges = attacker.get("ice_dagger_charges", 0) + 1
                    attacker["ice_dagger_charges"] = ice_charges
                    if ice_charges >= 3:
                        attacker["ice_dagger_charges"] = 0
                        ice_dmg = 120  # daño fijo al 3er toque
                        defender["hp"] = max(0, defender["hp"] - ice_dmg)
                        battle.log.append(f"   🧊❄️ ¡ICE DAGGER CARGADA! **{ice_dmg}** daño masivo de hielo!")
                    else:
                        battle.log.append(f"   🧊 Ice Dagger cargando... ({ice_charges}/3 — mantén la espada equipada!)")
                else:
                    attacker["ice_dagger_charges"] = 0
                    battle.log.append(f"   🧊 Ice Dagger bloqueada por Firebrand!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "consumed_fury":
            # 50 daño al activo + 15 splash + impostor pierde 50% vida
            dmg_fury = 50
            defender["hp"] = max(0, defender["hp"] - dmg_fury)
            def_team_fury = battle.p2_team if battle.turn == 1 else battle.p1_team
            splash = skill.get("splash_dmg", 15)
            hit = []
            for fig in def_team_fury:
                if fig is not defender and fig["hp"] > 0:
                    fig["hp"] = max(0, fig["hp"] - splash)
                    hit.append(f"{fig['emoji']} {fig['name']} -{splash}HP")
            # El impostor pierde 50% de su vida en lugar de morir
            self_dmg = max(1, attacker["max_hp"] // 2)
            attacker["hp"] = max(1, attacker["hp"] - self_dmg)
            battle.log.append(f"💥 **{attacker['emoji']} {attacker['name']}** usa **{skill['name']}**!")
            battle.log.append(f"   💥 **{defender['name']}** recibe **{dmg_fury}** daño!")
            if hit:
                battle.log.append(f"   💥 Explosión: {' | '.join(hit)}")
            battle.log.append(f"   😵 **{attacker['name']}** pierde el 50% de su vida por la explosión!")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "lobster":
            # 0.01% de probabilidad de matar a TODAS las figuras del oponente
            roll = random.randint(1, 10000)
            def_team = battle.p2_team if battle.turn == 1 else battle.p1_team
            if roll == 1:
                for fig in def_team:
                    fig["hp"] = 0
                battle.log.append(f"🦞 **Lobster** usa **LOBSTER**...")
                battle.log.append(f"   ...")
                battle.log.append(f"   🦞 **¡LA LANGOSTA LO HA HECHO! ¡TODAS LAS FIGURAS ENEMIGAS ESTÁN MUERTAS!** 🦞")
            else:
                battle.log.append(f"🦞 **Lobster** usa **LOBSTER**...")
                battle.log.append(f"   ...")
                battle.log.append(f"   No pasa nada. (Como siempre)")
            battle.log.append(f"   _{skill['desc']}_")

        elif stype == "ban_hammer":
            if random.randint(1,2) == 1:
                p1_fig["hp"] = 0
                battle.log.append(f"🤖🔨 **¡BAN HAMMER!** **{p1_fig['name']}** eliminada!")
            else:
                alive = [fig for fig in battle.p2_team if fig["hp"] > 0 and fig is not f]
                if alive:
                    v = random.choice(alive)
                    v["hp"] = 0
                    battle.log.append(f"🤖🔨 Ban Hammer sale mal... ¡mata a **{v['name']}** aliada! 😂")

        elif stype in ("parry", "buff", "gamble", "gamble_fire"):
            # Para estos tipos el bot simplemente ataca normal
            chosen_idx = None

    if chosen_idx is None:
        # Ataque básico — siempre disponible, gana 20 energía
        f["energy"] = min(ENERGY_MAX, f["energy"] + ENERGY_PER_TURN + f.get("energy_bonus", 0))
        bonus_atk = f.pop("atk_buff", 0)
        max_power = max((sk.get("power", 0) for sk in f["skills"]), default=20)
        base_dmg = max(1, round(max_power / 2))
        dmg = max(1, base_dmg + (bonus_atk // 2) + random.randint(-2, 3) - (p1_fig["defense"] // 6))
        p1_fig["hp"] = max(0, p1_fig["hp"] - dmg)
        buff_txt = f" (+{bonus_atk} ATK)" if bonus_atk else ""
        battle.log.append(f"🤖 **{f['emoji']} {f['name']}** ataca básico{buff_txt} → **{dmg}** daño! (+20⚡)")
        if p1_fig.get("retributing"):
            retrib_dmg = max(1, dmg // 2)
            f["hp"] = max(0, f["hp"] - retrib_dmg)
            p1_fig["retrib_turns"] = p1_fig.get("retrib_turns", 1) - 1
            if p1_fig["retrib_turns"] <= 0:
                p1_fig["retributing"] = False
            battle.log.append(f"   🦷 **{p1_fig['name']}** devuelve **{retrib_dmg}** daño (¡Retribución!)!")
        if p1_fig.get("parrying"):
            p1_fig["parrying"] = False
            pct = p1_fig.get("parry_dmg_pct", 25)
            cdmg = int(p1_fig["max_hp"] * pct / 100)
            f["hp"] = max(0, f["hp"] - cdmg)
            battle.log.append(f"   ⚡ **{p1_fig['name']}** hace COUNTER y devuelve **{cdmg}** daño!")

    # ¿Cayó alguna figura del jugador?
    if p1_fig["hp"] <= 0:
        # Pasiva de Gamer64: revive una vez con 80% HP
        if p1_fig.get("passive_revive"):
            p1_fig["passive_revive"] = False
            revive_hp = max(1, int(p1_fig["max_hp"] * 0.80))
            p1_fig["hp"] = revive_hp
            p1_fig["energy"] = 0
            battle.log.append(f"💫 **{p1_fig['emoji']} {p1_fig['name']}** se cansó de rodeos, ¡se arranca el brazo y entra a su **Fase 2**!")
            battle.log.append(f"   Se levanta con **{revive_hp} HP** (80% de su vida máxima)!")
        else:
            next_idx = battle.next_alive(battle.p1_team, battle.p1_active)
            if next_idx is not None:
                battle.p1_active = next_idx
                new_fig = battle.p1_team[next_idx]
                battle.log.append(f"💀 **{p1_fig['name']}** fue derrotado!")
                battle.log.append(f"🔄 ¡Entra **{new_fig['emoji']} {new_fig['name']}**!")
            else:
                await end_battle(interaction, battle, channel_id, winner_turn=2)
                return

    if battle.current_p1()["hp"] <= 0:
        next_idx = battle.next_alive(battle.p1_team, battle.p1_active)
        if next_idx is None:
            await end_battle(interaction, battle, channel_id, winner_turn=2)
            return

    battle.turn = 1
    view = get_battle_view(battle)
    await interaction.message.edit(embed=battle.get_embed(), view=view)

async def end_battle(interaction, battle: BattleState, channel_id: int, winner_turn: int):
    """Cierra la batalla y da recompensas."""
    p1_won = (winner_turn == 1)
    winner_id = battle.p1 if p1_won else battle.p2
    loser_id  = battle.p2 if p1_won else battle.p1

    # Asegurarse de que los HP queden en 0
    for f in battle.p1_team + battle.p2_team:
        f["hp"] = max(0, f["hp"])

    embed = battle.get_embed(title="🏆 ¡FIN DE LA BATALLA!")

    if p1_won:
        win_text = f"🎉 ¡<@{winner_id}> ganó con su equipo!"
    else:
        win_text = f"🤖 ¡El BOT ganó!" if battle.is_bot else f"🎉 ¡<@{winner_id}> ganó con su equipo!"
    embed.add_field(name="🏆 GANADOR", value=win_text, inline=False)

    db = load_db()
    # Recompensas al ganador
    if p1_won or not battle.is_bot:
        winner_data = get_user(db, winner_id)
        if winner_data:
            winner_data["wins"] = winner_data.get("wins", 0) + 1
            winner_data["coins"] = winner_data.get("coins", 0) + COINS_WIN
            winner_data["xp"] = winner_data.get("xp", 0) + XP_PER_WIN
            while winner_data["xp"] >= xp_to_level_up(winner_data["level"]):
                winner_data["xp"] -= xp_to_level_up(winner_data["level"])
                winner_data["level"] += 1
            # XP a las figuras del equipo ganador — con sistema de stat_up
            team_keys = battle.p1_team_keys if p1_won else battle.p2_team_keys
            leveled_figs = []
            for fig_data in winner_data["figures"]:
                if fig_data["key"] in team_keys:
                    if fig_data.get("level", 1) < FIGURE_LEVEL_MAX:
                        fig_data["xp"] = fig_data.get("xp", 0) + XP_PER_WIN // 3
                        if check_figure_levelup(fig_data):
                            leveled_figs.append(fig_data)
            if leveled_figs:
                fig_names = [FIGURES.get(fd["key"], {}).get("name", fd["key"]) for fd in leveled_figs]
                embed.add_field(name="⬆️ ¡Level Up!", value=f"{'  '.join(fig_names)} subieron de nivel. Usa `/subirstat` para elegir tu mejora.", inline=False)

    # Recompensas al perdedor
    if not battle.is_bot or not p1_won:
        loser_data = get_user(db, loser_id)
        if loser_data:
            loser_data["losses"] = loser_data.get("losses", 0) + 1
            loser_data["coins"] = loser_data.get("coins", 0) + COINS_LOSS
    elif battle.is_bot and not p1_won:
        p1_data = get_user(db, battle.p1)
        if p1_data:
            p1_data["losses"] = p1_data.get("losses", 0) + 1
            p1_data["coins"] = p1_data.get("coins", 0) + COINS_LOSS

    save_db(db)
    embed.add_field(name="💰 Recompensas", value=f"Ganador: +{COINS_WIN}🪙 +{XP_PER_WIN}XP | Perdedor: +{COINS_LOSS}🪙", inline=False)

    # Dar ingrediente al ganador si tiene suerte
    if random.randint(1, 100) <= BATTLE_INGREDIENT_DROP_CHANCE:
        db2 = load_db()
        winner_data2 = get_user(db2, winner_id)
        if winner_data2:
            ing = give_battle_ingredient(winner_data2)
            save_db(db2)
            embed.add_field(name="🧑‍🍳 ¡Ingrediente encontrado!", value=f"¡Conseguiste {ing} **{INGREDIENTS.get(ing, '')}** para cocinar!", inline=False)

    if channel_id in active_battles:
        del active_battles[channel_id]

    try:
        await interaction.response.edit_message(embed=embed, view=None)
    except Exception:
        await interaction.message.edit(embed=embed, view=None)

    # Drops de misión activa (quest) — post-batalla
    db3 = load_db()
    winner3 = get_user(db3, winner_id)
    if winner3:
        changed = False
        for qid in winner3.get("active_quests", []):
            prev = winner3.get("quest_progress", {}).get(qid, 0)
            await check_quest_drops(winner3, qid, interaction.channel)
            if winner3.get("quest_progress", {}).get(qid, 0) != prev:
                changed = True
        if changed:
            save_db(db3)

# ============================================================
#  COMANDOS
# ============================================================

GUILD_ID = 1236294131534401647  # ← PON AQUÍ EL ID DE TU SERVIDOR (clic derecho al servidor > Copiar ID)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} está en línea!")
    await bot.tree.sync()
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ {len(synced)} comandos sincronizados en el servidor!")
    else:
        print("⚠️ Pon tu GUILD_ID para sync instantáneo")

# --- REGISTRO ---
@bot.tree.command(name="registrar", description="Regístrate en el Androide del PvP y obtén 1000 monedas!")
async def registrar(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if user:
        await interaction.response.send_message(
            f"⚠️ Ya estás registrado como **{user['name']}** con **{user['coins']}** monedas!",
            ephemeral=True
        )
        return

    modal = discord.ui.Modal(title="¡Bienvenido al Androide del PvP!")

    name_input = discord.ui.TextInput(
        label="¿Cómo quieres que te conozca el bot?",
        placeholder="Ej: El Destructor, MegaGamer, etc.",
        max_length=32
    )
    modal.add_item(name_input)

    async def on_submit(modal_interaction: discord.Interaction):
        display_name = name_input.value.strip()
        create_user(db, modal_interaction.user.id, display_name)
        embed = discord.Embed(
            title="🎉 ¡Registro exitoso!",
            description=f"¡Bienvenido, **{display_name}**!\nEres conocido en la arena como el gran **{display_name}**.",
            color=0x2ecc71
        )
        embed.add_field(name="💰 Monedas iniciales", value="1,000 monedas", inline=True)
        embed.add_field(name="🎮 Siguiente paso", value="Usa `/tienda` para comprar tu primera figura!", inline=True)
        embed.set_footer(text="¡Que comience la batalla!")
        await modal_interaction.response.send_message(embed=embed)

    modal.on_submit = on_submit
    await interaction.response.send_modal(modal)

# --- PERFIL ---
@bot.tree.command(name="perfil", description="Mira tu perfil y tus estadísticas")
async def perfil(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ No estás registrado. Usa `/registrar` primero.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"👤 Perfil de {user['name']}",
        color=0x3498db
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="💰 Monedas", value=f"{user['coins']:,}", inline=True)
    embed.add_field(name="🏆 Nivel", value=user.get("level", 1), inline=True)
    embed.add_field(name="⚡ XP", value=f"{user.get('xp',0)}/{xp_to_level_up(user.get('level',1))}", inline=True)
    embed.add_field(name="✅ Victorias", value=user.get("wins", 0), inline=True)
    embed.add_field(name="❌ Derrotas", value=user.get("losses", 0), inline=True)
    embed.add_field(name="🎭 Figuras", value=len(user.get("figures", [])), inline=True)

    active = user.get("active_figure")
    if active:
        fig = FIGURES.get(active)
        if fig:
            embed.add_field(name="🌟 Figura activa", value=f"{fig['emoji']} {fig['name']}", inline=False)

    await interaction.response.send_message(embed=embed)

# --- TIENDA ---
@bot.tree.command(name="tienda", description="Compra figuras para tu colección")
async def tienda(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return

    # Excluir figuras con price=0 (exclusivas de jefes) y roblox_boss
    available = {k: v for k, v in FIGURES.items() if v.get("price", 0) > 0 and k != "roblox_boss"}

    if not available:
        await interaction.response.send_message("🎉 ¡Ya tienes todas las figuras!", ephemeral=True)
        return

    # Mostrar página 0
    await show_shop_page(interaction, available, user, 0, db)

async def show_shop_page(interaction, available, user, page, db):
    items = list(available.items())
    per_page = 4
    total_pages = (len(items) + per_page - 1) // per_page
    start = page * per_page
    end = start + per_page
    page_items = items[start:end]

    embed = discord.Embed(
        title="🏪 Tienda de Figuras",
        description=f"💰 Tus monedas: **{user['coins']:,}** | Página {page+1}/{total_pages}",
        color=0xf39c12
    )

    for key, fig in page_items:
        star = RARITY_STARS[fig["rarity"]]
        embed.add_field(
            name=f"{fig['emoji']} {fig['name']} {star}",
            value=(
                f"💎 {fig['rarity'].upper()} | 💰 {fig['price']} monedas\n"
                f"❤️ HP:{fig['hp']} ⚔️ ATK:{fig['attack']} 🛡️ DEF:{fig['defense']} ⚡ VEL:{fig['speed']}\n" +
                " | ".join(f"✨{sk['name']}" for sk in FIGURE_SKILLS.get(key, []))
            ),
            inline=False
        )

    view = ShopView(available, user, page, total_pages, page_items, db)

    if hasattr(interaction, 'response') and not interaction.response.is_done():
        await interaction.response.send_message(embed=embed, view=view)
    else:
        await interaction.edit_original_response(embed=embed, view=view)

class ShopView(discord.ui.View):
    def __init__(self, available, user, page, total_pages, page_items, db):
        super().__init__(timeout=60)
        self.available = available
        self.user = user
        self.page = page
        self.total_pages = total_pages
        self.page_items = page_items
        self.db = db

        # Botones de compra
        for key, fig in page_items:
            btn = discord.ui.Button(
                label=f"Comprar {fig['name']} ({fig['price']}🪙)",
                style=discord.ButtonStyle.success,
                custom_id=f"buy_{key}",
                disabled=user["coins"] < fig["price"]
            )
            btn.callback = self.make_buy_callback(key, fig)
            self.add_item(btn)

        # Navegación
        if page > 0:
            prev_btn = discord.ui.Button(label="◀ Anterior", style=discord.ButtonStyle.secondary, custom_id="prev")
            prev_btn.callback = self.prev_page
            self.add_item(prev_btn)

        if page < total_pages - 1:
            next_btn = discord.ui.Button(label="Siguiente ▶", style=discord.ButtonStyle.secondary, custom_id="next")
            next_btn.callback = self.next_page
            self.add_item(next_btn)

    def make_buy_callback(self, key, fig):
        async def callback(interaction: discord.Interaction):
            db = load_db()
            user = get_user(db, interaction.user.id)
            if not user:
                await interaction.response.send_message("❌ No registrado.", ephemeral=True)
                return
            if user["coins"] < fig["price"]:
                await interaction.response.send_message("❌ No tienes suficientes monedas.", ephemeral=True)
                return
            user["coins"] -= fig["price"]
            user["figures"].append({"key": key, "level": 1, "xp": 0})
            # Si el equipo tiene huecos, llenarlos automáticamente
            team = user.get("team", [None, None, None])
            for i in range(3):
                if i >= len(team): team.append(None)
                if team[i] is None:
                    team[i] = len(user["figures"]) - 1  # índice en figures
                    break
            user["team"] = team
            save_db(db)

            embed = discord.Embed(
                title="✅ ¡Figura comprada!",
                description=f"¡Obtuviste a **{fig['emoji']} {fig['name']}**!",
                color=RARITY_COLOR[fig["rarity"]]
            )
            embed.add_field(name="💰 Monedas restantes", value=f"{user['coins']:,}", inline=True)
            embed.add_field(name="💡 Tip", value="Usa `/misfiguras` para ver tu colección y `/equipar` para armar tu equipo de 3.", inline=False)
            if fig.get("image"):
                embed.set_image(url=fig["image"])

            await interaction.response.edit_message(embed=embed, view=None)
        return callback

    async def prev_page(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = load_db()
        user = get_user(db, interaction.user.id) or self.user
        available = {k: v for k, v in FIGURES.items() if v.get("price", 0) > 0 and k != "roblox_boss"}
        await show_shop_page(interaction, available, user, self.page - 1, db)

    async def next_page(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = load_db()
        user = get_user(db, interaction.user.id) or self.user
        available = {k: v for k, v in FIGURES.items() if v.get("price", 0) > 0 and k != "roblox_boss"}
        await show_shop_page(interaction, available, user, self.page + 1, db)

# --- MIS FIGURAS ---
@bot.tree.command(name="misfiguras", description="Ver tu colección de figuras")
async def misfiguras(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return

    figs = user.get("figures", [])
    if not figs:
        await interaction.response.send_message("📭 No tienes figuras. Usa `/tienda` para comprar.", ephemeral=True)
        return

    await show_figure_menu(interaction, user, figs, page=0)

def get_unique_figs(figs):
    """Devuelve lista de figuras únicas (sin duplicados) con conteo de copias.
    Cada entrada: (key, fig_data_mejor_nivel, count)
    Ordenadas según aparecen por primera vez en la colección."""
    seen = {}   # key -> {"data": fig_data, "count": n, "order": i}
    for i, fd in enumerate(figs):
        k = fd["key"]
        if k not in seen:
            seen[k] = {"data": fd, "count": 1, "order": i}
        else:
            seen[k]["count"] += 1
            # Guardar la copia de mayor nivel
            if fd.get("level", 1) > seen[k]["data"].get("level", 1):
                seen[k]["data"] = fd
    # Ordenar por orden de primera aparición
    ordered = sorted(seen.values(), key=lambda x: x["order"])
    return [(v["data"]["key"], v["data"], v["count"]) for v in ordered]

def build_figure_embed(user, unique_figs, page):
    key, fig_data, count = unique_figs[page]
    fig = FIGURES.get(key, {})
    lvl = fig_data.get("level", 1)
    xp  = fig_data.get("xp", 0)
    team = user.get("team", [None, None, None])
    all_figs = user.get("figures", [])
    pos_names = ["🥇 Frontal", "🥈 Centro", "🥉 Trasero"]
    rarity = fig.get("rarity", "común")
    star  = RARITY_STARS.get(rarity, "⚪")
    color = RARITY_COLOR.get(rarity, 0x95a5a6)

    # ¿Está en el equipo?
    in_team = ""
    for t_pos, t_idx in enumerate(team):
        if t_idx is not None and t_idx < len(all_figs) and all_figs[t_idx]["key"] == key:
            in_team += f" **[{pos_names[t_pos]}]**"

    # Título con contador de copias
    copies_txt = f" ×{count}" if count > 1 else ""
    embed = discord.Embed(
        title=f"{fig.get('emoji','')} {fig.get('name', key)}{copies_txt} {star}{in_team}",
        description=f"Rareza: **{rarity.upper()}** | Precio: **{fig.get('price',0):,}🪙**",
        color=color
    )

    # Copias
    if count > 1:
        embed.add_field(name="📦 Copias", value=f"Tienes **{count}** de esta figura", inline=False)

    embed.add_field(
        name="📊 Stats",
        value=(
            f"❤️ **Vida:** {apply_level_bonus(fig.get('hp',0), lvl)}\n"
            f"⚔️ **Ataque:** {apply_level_bonus(fig.get('attack',0), lvl)}\n"
            f"🛡️ **Defensa:** {apply_level_bonus(fig.get('defense',0), lvl)}\n"
            f"⚡ **Velocidad:** {fig.get('speed',0)}"
        ),
        inline=True
    )
    embed.add_field(
        name="🏅 Progreso",
        value=(f"Nivel: **{lvl}**\nXP: **{xp}/{xp_to_level_up(lvl)}**"),
        inline=True
    )

    # Equipo
    team_str = ""
    for i, idx in enumerate(team):
        if idx is not None and idx < len(all_figs):
            fd = all_figs[idx]
            fg = FIGURES.get(fd["key"])
            name  = fg.get("name", fd["key"]) if fg else fd["key"]
            emoji = fg.get("emoji", "") if fg else ""
            team_str += f"{pos_names[i]}: {emoji} {name}\n"
        else:
            team_str += f"{pos_names[i]}: _(vacío)_\n"
    embed.add_field(name="⚔️ Tu equipo", value=team_str, inline=False)

    # Habilidades
    skills = FIGURE_SKILLS.get(key, [])
    type_emoji = {
        "damage":"⚔️","heal":"💚","drain":"⚡","drain_fill":"🔴","parry":"🛡️",
        "buff":"⭐","gamble":"🎲","gamble_fire":"🔥","team_atk_buff":"⭐","dot":"💣",
        "bad_update":"🔳","ban_hammer":"🔨","fly_away":"✈️","michi_counter":"🦊",
        "glitch_dmg":"🌀","corruption":"🌑","retribution":"🦷","fast_kill":"🔪",
        "consumed_fury":"💥","revive_team":"💀","heal_team_self":"🍗",
        "switch_sword":"🗡️","slash":"⚔️","lobster":"🦞",
    }
    bar_labels = {30:"🟡[30⚡]", 60:"🟠[60⚡]", 100:"🔴[100⚡]"}
    skill_str = ""
    for sk in skills:
        te = type_emoji.get(sk["type"], "⚡")
        bl = bar_labels.get(sk["cost"], f"[{sk['cost']}⚡]")
        skill_str += f"{bl} {te} **{sk['name']}**\n_{sk['desc']}_\n\n"
    if skill_str:
        embed.add_field(name="✨ Habilidades", value=skill_str.strip(), inline=False)

    if fig.get("image"):
        embed.set_image(url=fig["image"])

    embed.set_footer(text=f"Figura {page+1} de {len(unique_figs)}  •  Colección única")
    return embed

def make_fig_view_sync(orig_user_id, user, unique_figs, page):
    view = discord.ui.View(timeout=120)
    total = len(unique_figs)

    prev_btn = discord.ui.Button(label="◀ Anterior", style=discord.ButtonStyle.secondary,
                                  disabled=page==0, custom_id="fig_prev", row=0)
    counter_btn = discord.ui.Button(label=f"{page+1} / {total}", style=discord.ButtonStyle.primary,
                                     disabled=True, custom_id="fig_counter", row=0)
    next_btn = discord.ui.Button(label="Siguiente ▶", style=discord.ButtonStyle.secondary,
                                  disabled=page==total-1, custom_id="fig_next", row=0)

    def make_nav(new_page):
        async def callback(inter: discord.Interaction):
            if inter.user.id != orig_user_id:
                await inter.response.send_message("❌ Este menú no es tuyo.", ephemeral=True)
                return
            db2 = load_db()
            u2 = get_user(db2, inter.user.id)
            uf2 = get_unique_figs(u2.get("figures", []))
            embed2 = build_figure_embed(u2, uf2, new_page)
            view2  = make_fig_view_sync(orig_user_id, u2, uf2, new_page)
            await inter.response.edit_message(embed=embed2, view=view2)
        return callback

    prev_btn.callback = make_nav(page - 1)
    next_btn.callback = make_nav(page + 1)
    view.add_item(prev_btn)
    view.add_item(counter_btn)
    view.add_item(next_btn)
    return view

async def show_figure_menu(interaction, user, figs, page: int):
    unique_figs = get_unique_figs(figs)
    if not unique_figs:
        await interaction.response.send_message("📭 No tienes figuras.", ephemeral=True)
        return
    page = min(page, len(unique_figs) - 1)
    embed = build_figure_embed(user, unique_figs, page)
    view  = make_fig_view_sync(interaction.user.id, user, unique_figs, page)
    if hasattr(interaction, 'response') and not interaction.response.is_done():
        await interaction.response.send_message(embed=embed, view=view)
    else:
        await interaction.edit_original_response(embed=embed, view=view)

# --- EQUIPAR ---
@bot.tree.command(name="equipar", description="Arma tu equipo de 3 figuras (frontal, centro, trasero)")
async def equipar(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user or not user.get("figures"):
        await interaction.response.send_message("❌ No tienes figuras. Compra en `/tienda`.", ephemeral=True)
        return

    await show_equip_menu(interaction, user, step=0)

async def show_equip_menu(interaction, user, step: int):
    pos_names = ["🥇 Frontal", "🥈 Centro", "🥉 Trasero"]
    pos_desc  = ["primera en entrar al combate", "entra si la frontal cae", "la última en combatir"]
    figs = user.get("figures", [])

    options = []
    for i, fig_data in enumerate(figs):
        fig = FIGURES.get(fig_data["key"])
        if fig:
            lvl = fig_data.get("level", 1)
            raw_emoji = fig["emoji"]
            # Discord SelectOption acepta emojis unicode o PartialEmoji para emojis personalizados
            # Si el emoji tiene formato <:name:id>, parsearlo como PartialEmoji
            if raw_emoji.startswith("<:") or raw_emoji.startswith("<a:"):
                try:
                    emoji_obj = discord.PartialEmoji.from_str(raw_emoji)
                except Exception:
                    emoji_obj = None
            else:
                emoji_obj = raw_emoji
            option_kwargs = dict(
                label=f"#{i+1} {fig['name']} (Nv.{lvl})",
                value=str(i),
                description=f"{fig['rarity'].upper()} | ATK:{apply_level_bonus(fig['attack'],lvl)} HP:{apply_level_bonus(fig['hp'],lvl)}"
            )
            if emoji_obj:
                option_kwargs["emoji"] = emoji_obj
            options.append(discord.SelectOption(**option_kwargs))

    select = discord.ui.Select(
        placeholder=f"Elige tu figura {pos_names[step]}...",
        options=options[:25],  # Discord limita a 25 opciones por Select
        custom_id=f"equip_step_{step}"
    )

    async def select_callback(inter: discord.Interaction):
        chosen_idx = int(select.values[0])
        db2 = load_db()
        usr2 = get_user(db2, inter.user.id)
        team = usr2.get("team", [None, None, None])
        while len(team) < 3: team.append(None)
        team[step] = chosen_idx
        usr2["team"] = team
        save_db(db2)

        fig_data = usr2["figures"][chosen_idx]
        fig = FIGURES[fig_data["key"]]

        if step < 2:
            # Continuar al siguiente paso
            await inter.response.edit_message(
                content=f"✅ {pos_names[step]}: **{fig['emoji']} {fig['name']}** — Ahora elige la {pos_names[step+1]}",
                view=None
            )
            await show_equip_menu(inter, usr2, step + 1)
        else:
            # Equipo completo
            team_final = usr2["team"]
            resumen = []
            for i, idx in enumerate(team_final):
                if idx is not None and idx < len(usr2["figures"]):
                    fd = usr2["figures"][idx]
                    fg = FIGURES.get(fd["key"])
                    if fg:
                        resumen.append(f"{pos_names[i]}: {fg['emoji']} **{fg['name']}**")
            embed = discord.Embed(
                title="✅ ¡Equipo armado!",
                description="\n".join(resumen),
                color=0x2ecc71
            )
            embed.set_footer(text="¡Tu equipo está listo para batallar!")
            await inter.response.edit_message(content=None, embed=embed, view=None)

    select.callback = select_callback
    view = discord.ui.View(timeout=60)
    view.add_item(select)

    msg = f"**Paso {step+1}/3** — Elige tu figura **{pos_names[step]}** ({pos_desc[step]})"
    if hasattr(interaction, 'response') and not interaction.response.is_done():
        await interaction.response.send_message(msg, view=view, ephemeral=True)
    else:
        await interaction.followup.send(msg, view=view, ephemeral=True)


# ============================================================
#  BOTS RIVALES — dificultad progresiva + jefe final
# ============================================================
BOT_ROSTER = [
    {
        "id": "facil",
        "name": "🪆 Maniquí de Combate",
        "desc": "Solo está ahí para recibir golpes. No te pongas nervioso.",
        "difficulty": 1,
        "team": ["agustoloco", "agustoloco", "agustoloco"],
        "level": 1,
        "hp_mult": 1.0, "atk_mult": 1.0, "energy_bonus": 0,
        "reward_coins": 80,
        "reward_xp": 30,
    },
    {
        "id": "medio",
        "name": "💼 Trabajador Ocupado",
        "desc": "Está peleando en su hora de almuerzo. Tiene algo de experiencia.",
        "difficulty": 2,
        "team": ["gamer64", "agustoloco", "agustoloco"],
        "level": 3,
        "hp_mult": 1.1, "atk_mult": 1.1, "energy_bonus": 0,
        "reward_coins": 150,
        "reward_xp": 60,
    },
    {
        "id": "dificil",
        "name": "🎮 Jugador Tryhard",
        "desc": "Lleva 14 horas jugando sin dormir. Un rival serio.",
        "difficulty": 3,
        "team": ["sonic", "gamer64", "agustoloco"],
        "level": 6,
        "hp_mult": 1.2, "atk_mult": 1.2, "energy_bonus": 5,
        "reward_coins": 250,
        "reward_xp": 100,
    },
    {
        "id": "experto",
        "name": "👾 Glitch",
        "desc": "Un OC malvado que rompe las reglas del juego. Muy pocos lo han derrotado.",
        "difficulty": 4,
        "team": ["sonic", "alex", "gamer64"],
        "level": 10,
        "hp_mult": 1.4, "atk_mult": 1.3, "energy_bonus": 8,
        "reward_coins": 400,
        "reward_xp": 150,
    },
    {
        "id": "nino_random",
        "name": "👦 Niño Random",
        "desc": "No sabes su nombre. No sabe el tuyo. Pero está MUY enojado.",
        "difficulty": 5,
        "team": ["boss_nino1", "boss_nino2", "boss_nino3"],
        "level": 13,
        "hp_mult": 1.5, "atk_mult": 1.4, "energy_bonus": 10,
        "reward_coins": 550,
        "reward_xp": 200,
        "is_boss": True,
    },
    {
        "id": "paper_mario",
        "name": "📄 Paper Mario",
        "desc": "Es delgado como papel pero golpea como un libro de texto.",
        "difficulty": 6,
        "team": ["boss_paper1", "boss_paper2", "boss_paper3"],
        "level": 15,
        "hp_mult": 1.6, "atk_mult": 1.5, "energy_bonus": 12,
        "reward_coins": 700,
        "reward_xp": 280,
        "is_boss": True,
    },
    {
        "id": "steve",
        "name": "⛏️ Steve",
        "desc": "Lleva sobreviviendo desde el 2011. Ha visto cosas que tú no puedes imaginar.",
        "difficulty": 7,
        "team": ["boss_steve1", "boss_steve2", "boss_steve3"],
        "level": 17,
        "hp_mult": 1.8, "atk_mult": 1.6, "energy_bonus": 15,
        "reward_coins": 850,
        "reward_xp": 350,
        "is_boss": True,
    },
    {
        "id": "impostor_negro",
        "name": "🔪 Impostor Negro",
        "desc": "El mismo que conoces, pero entrenado para matar. Sus movimientos son letales.",
        "difficulty": 8,
        "team": ["boss_impostor1", "boss_impostor2", "blackout"],
        "level": 19,
        "hp_mult": 2.0, "atk_mult": 1.8, "energy_bonus": 18,
        "reward_coins": 950,
        "reward_xp": 420,
        "is_boss": True,
    },
    {
        "id": "jefe",
        "name": "💀 El Antifas Antifasado",
        "desc": "El jefe supremo. Nadie sabe de dónde vino. Sus figuras no se consiguen en la tienda.",
        "difficulty": 9,
        "team": ["antifas", "roblox_boss", "gamer64"],
        "level": 20,
        "hp_mult": 2.2, "atk_mult": 2.0, "energy_bonus": 20,
        "reward_coins": 1500,
        "reward_xp": 600,
        "is_boss": True,
    },
]

# ── Figuras exclusivas de los nuevos jefes ────────────────────────────────────

# Niño Random
FIGURES["boss_nino1"] = {"name":"Niño Enfadado","emoji":"😡","rarity":"legendario","price":0,"hp":200,"attack":38,"defense":20,"speed":40,"image":""}
FIGURES["boss_nino2"] = {"name":"Niño con Palo","emoji":"🏏","rarity":"legendario","price":0,"hp":180,"attack":45,"defense":15,"speed":35,"image":""}
FIGURES["boss_nino3"] = {"name":"Niño Llorón","emoji":"😭","rarity":"legendario","price":0,"hp":160,"attack":30,"defense":25,"speed":30,"image":""}
FIGURE_SKILLS["boss_nino1"] = [
    {"name":"Rabieta",       "cost":30, "type":"damage",       "power":25, "stun":True,  "desc":"El niño hace una rabieta y golpea al rival aturdido."},
    {"name":"QUIERO ESO YA","cost":60, "type":"team_atk_buff", "power":0,  "atk_buff":20,"desc":"Exige lo que quiere — todo el equipo gana +20 ATK."},
    {"name":"¡ME LO DICES A MÍ!","cost":100,"type":"damage",  "power":70, "aoe":True,"aoe_secondary_power":40,"desc":"Explota de furia y golpea a todo el equipo rival."},
]
FIGURE_SKILLS["boss_nino2"] = [
    {"name":"Palazo",        "cost":30, "type":"damage",  "power":30, "desc":"Un palazo directo sin contemplaciones."},
    {"name":"Palazo x2",     "cost":60, "type":"damage",  "power":55, "aoe":True,"aoe_secondary_power":25,"desc":"Gira el palo y golpea a todos los rivales."},
    {"name":"SUPER PALAZO",  "cost":100,"type":"damage",  "power":85, "stun":True,"stun_turns":2,"desc":"Un golpe devastador que aturde 2 turnos."},
]
FIGURE_SKILLS["boss_nino3"] = [
    {"name":"Llanto",        "cost":30, "type":"heal",         "power":40, "team_heal":True,"team_heal_power":20,"desc":"Sus lágrimas curan al equipo."},
    {"name":"Llamar a Mamá", "cost":60, "type":"team_atk_buff","power":0,  "atk_buff":15,  "desc":"Llama a mamá — el equipo se motiva con +15 ATK."},
    {"name":"Berrinche Total","cost":100,"type":"dot",         "power":15,"dot_turns":4,   "desc":"Berrinche imparable: 15 daño/turno x4 al rival."},
]

# Paper Mario
FIGURES["boss_paper1"] = {"name":"Paper Mario","emoji":"📄","rarity":"legendario","price":0,"hp":220,"attack":42,"defense":35,"speed":38,"image":""}
FIGURES["boss_paper2"] = {"name":"Paper Bowser","emoji":"🐢","rarity":"legendario","price":0,"hp":280,"attack":50,"defense":45,"speed":20,"image":""}
FIGURES["boss_paper3"] = {"name":"Paper Peach","emoji":"👸","rarity":"legendario","price":0,"hp":190,"attack":35,"defense":30,"speed":42,"image":""}
FIGURE_SKILLS["boss_paper1"] = [
    {"name":"Martillo de Papel","cost":30,"type":"damage",  "power":28, "desc":"Saca su martillo de papel y golpea."},
    {"name":"Estrella de Papel","cost":60,"type":"heal",    "power":50, "team_heal":True,"team_heal_power":25,"desc":"Una estrella de papel cura a todo el equipo."},
    {"name":"Modo Ultrahammer", "cost":100,"type":"damage", "power":90, "stun":True,"desc":"El martillo definitivo que aplasta todo."},
]
FIGURE_SKILLS["boss_paper2"] = [
    {"name":"Lanzallamas",   "cost":30,"type":"damage","power":32,"aoe":True,"aoe_secondary_power":18,"desc":"Escupe fuego a todos los rivales."},
    {"name":"Koopa Shell",   "cost":60,"type":"damage","power":50,"force_switch":True,"force_switch_turns":2,"desc":"Lanza su caparazón que bloquea a una figura 2 turnos."},
    {"name":"BOWSER PAPER FURY","cost":100,"type":"damage","power":100,"desc":"La ira definitiva de Bowser en formato papel."},
]
FIGURE_SKILLS["boss_paper3"] = [
    {"name":"Bofetada Real", "cost":30,"type":"damage","power":22,"stun":True,"desc":"Una bofetada elegante que aturde al rival."},
    {"name":"Curación Real", "cost":60,"type":"heal",  "power":60,"team_heal":True,"team_heal_power":30,"desc":"Peach cura generosamente a todo el equipo."},
    {"name":"Parasol Real",  "cost":100,"type":"retribution","power":0,"desc":"El parasol devuelve la mitad del daño recibido."},
]

# Steve
FIGURES["boss_steve1"] = {"name":"Steve","emoji":"⛏️","rarity":"legendario","price":0,"hp":300,"attack":48,"defense":50,"speed":25,"image":""}
FIGURES["boss_steve2"] = {"name":"Creeper","emoji":"💚","rarity":"legendario","price":0,"hp":200,"attack":55,"defense":20,"speed":30,"image":""}
FIGURES["boss_steve3"] = {"name":"Enderman","emoji":"🌑","rarity":"legendario","price":0,"hp":250,"attack":45,"defense":35,"speed":45,"image":""}
FIGURE_SKILLS["boss_steve1"] = [
    {"name":"Picar con Pico", "cost":30,"type":"damage",       "power":30, "desc":"Steve pica con su pico de diamante."},
    {"name":"Crafting Rápido","cost":60,"type":"team_atk_buff","power":0,"atk_buff":20,"desc":"Steve craftea armas para todo el equipo: +20 ATK."},
    {"name":"TNT",            "cost":100,"type":"damage",      "power":80,"aoe":True,"aoe_secondary_power":50,"desc":"Steve coloca TNT y vuela a todo el equipo rival."},
]
FIGURE_SKILLS["boss_steve2"] = [
    {"name":"Sssss...",       "cost":30,"type":"dot",     "power":12,"dot_turns":3,"desc":"El Creeper empieza a sisear... 12 daño/turno x3."},
    {"name":"¡BOOM!",         "cost":60,"type":"damage",  "power":70,"aoe":True,"aoe_secondary_power":40,"desc":"EXPLOTA haciendo daño masivo a todo el equipo."},
    {"name":"Mega Explosión", "cost":100,"type":"consumed_fury","power":0,"splash_dmg":30,"desc":"La explosión más grande que has visto. Mata al activo + 30 splash."},
]
FIGURE_SKILLS["boss_steve3"] = [
    {"name":"Teletransporte", "cost":30,"type":"damage",  "power":25,"stun":True,"desc":"Aparece detrás del rival y golpea."},
    {"name":"Bloque de Ender","cost":60,"type":"parry",   "power":0,"parry_dmg_pct":35,"desc":"Bloquea el ataque y contraataca con el 35% del HP rival."},
    {"name":"Ojos de Ender",  "cost":100,"type":"damage", "power":90,"force_switch":True,"force_switch_turns":3,"desc":"Sus ojos lanzan un rayo que bloquea a la figura 3 turnos."},
]

# Impostor Negro (jefe)
FIGURES["boss_impostor1"] = {"name":"Impostor Rojo","emoji":"🔴","rarity":"legendario","price":0,"hp":240,"attack":50,"defense":30,"speed":35,"image":""}
FIGURES["boss_impostor2"] = {"name":"Impostor Blanco","emoji":"⚪","rarity":"legendario","price":0,"hp":220,"attack":45,"defense":35,"speed":40,"image":""}
FIGURE_SKILLS["boss_impostor1"] = [
    {"name":"Ventilación",   "cost":30,"type":"damage",  "power":35,"desc":"Se escapa por el ventilador y aparece detrás del rival."},
    {"name":"Sabotaje",      "cost":60,"type":"dot",     "power":12,"dot_turns":4,"desc":"Sabotea el sistema: 12 daño/turno x4."},
    {"name":"Emergency Meeting","cost":100,"type":"damage","power":80,"aoe":True,"aoe_secondary_power":45,"desc":"Llama a una reunión de emergencia y ataca a todos."},
]
FIGURE_SKILLS["boss_impostor2"] = [
    {"name":"Cuchillo Veloz","cost":30,"type":"damage",  "power":32,"stun":True,"desc":"Lanza su cuchillo y aturde al rival."},
    {"name":"Fake Task",     "cost":60,"type":"buff",    "power":0,"atk_buff":25,"desc":"Finge hacer una tarea para preparar un golpe masivo."},
    {"name":"Sus",           "cost":100,"type":"damage", "power":85,"force_switch":True,"force_switch_turns":2,"desc":"El clásico. Elimina a la figura activa y la bloquea 2 turnos."},
]

# Figuras exclusivas del jefe (versiones potenciadas)
# --- Figuras exclusivas del jefe (price=0 = no aparecen en tienda) ---
FIGURES["antifas"] = {
    "name": "Antifas Antifasado",
    "emoji": "🦝",
    "rarity": "legendario",
    "price": 0,
    "hp": 235,
    "attack": 40,
    "defense": 38,
    "speed": 39,
    "image": "",
}
FIGURE_SKILLS["antifas"] = [
    {
        "name": "Heroic Pose",
        "cost": 30,
        "type": "team_atk_buff",   # buff de ATK acumulable al equipo
        "power": 0,
        "atk_buff": 15,            # +15 ATK acumulable, se consume al atacar
        "team_buff": True,
        "desc": "Pose heroica: +15 ATK a todas las figuras aliadas. Acumulable. Se consume al atacar.",
    },
    {
        "name": "Throwable Bomb",
        "cost": 60,
        "type": "dot",             # daño por turnos
        "power": 10,
        "dot_turns": 3,            # dura 3 turnos
        "dot_stackable": True,     # acumulable
        "desc": "Lanza una bomba venenosa. 10 de daño cada turno por 3 turnos. ¡Acumulable!",
    },
    {
        "name": "Dark Hole",
        "cost": 100,
        "type": "damage",
        "power": 15,
        "force_switch": True,
        "force_switch_turns": 3,
        "desc": "Invoca un agujero negro que manda a una figura enemiga al vacío por 3 turnos.",
    },
]

# --- Roblox (disponible en tienda Y usado por el jefe con stats superiores) ---
FIGURES["roblox"] = {
    "name": "Roblox",
    "emoji": "🔳",
    "rarity": "mítico",
    "price": 2003,
    "hp": 230,           # stats de tienda
    "attack": 35,
    "defense": 45,
    "speed": 35,
    "image": "https://tr.rbxcdn.com/30DAY-Avatar-310966282D3529E36976BF6B07B1DC90-Png/720/720/Avatar/Webp/noFilter",
}
FIGURES["roblox_boss"] = {
    "name": "Roblox",
    "emoji": "🔳",
    "rarity": "mítico",
    "price": 0,          # no aparece en tienda
    "hp": 270,           # stats del jefe
    "attack": 50,
    "defense": 45,
    "speed": 35,
    "image": "https://tr.rbxcdn.com/30DAY-Avatar-310966282D3529E36976BF6B07B1DC90-Png/720/720/Avatar/Webp/noFilter",
}
_roblox_skills = [
    {
        "name": "Bad Update",
        "cost": 30,
        "type": "bad_update",      # daño aleatorio a enemigos + cura aliados
        "power": 0,
        "desc": "Mala actualización: daña 4/6/8 a cada enemigo y cura la mitad a cada aliado.",
    },
    {
        "name": "Shut Down",
        "cost": 60,
        "type": "damage",
        "power": 20,
        "stun": True,
        "stun_turns": 3,           # stun extendido 3 turnos
        "desc": "Apaga los servidores. Aturde a la figura enemiga activa por 3 turnos.",
    },
    {
        "name": "Ban Hammer",
        "cost": 100,
        "type": "ban_hammer",      # 50/50: mata al enemigo O a un aliado
        "power": 0,
        "desc": "50% de chances de eliminar a la figura enemiga activa. El otro 50%... mata a una aliada.",
    },
]
FIGURE_SKILLS["roblox"] = _roblox_skills
FIGURE_SKILLS["roblox_boss"] = _roblox_skills

# --- BATALLA CONTRA BOT ---
@bot.tree.command(name="pvpbot", description="Elige un rival bot y batalla con tu equipo")
async def pvpbot(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return
    if interaction.channel_id in active_battles:
        await interaction.response.send_message("❌ Ya hay una batalla activa en este canal.", ephemeral=True)
        return

    owned = user.get("figures", [])
    if not owned:
        await interaction.response.send_message("❌ No tienes figuras. Compra en `/tienda`.", ephemeral=True)
        return

    # Mostrar selector de bot rival
    embed = discord.Embed(
        title="⚔️ Elige tu rival",
        description="Selecciona contra quién quieres batallar:",
        color=0x3498db
    )
    for b in BOT_ROSTER:
        team_preview = " | ".join(FIGURES[k]["emoji"] + " " + FIGURES[k]["name"] for k in b["team"] if k in FIGURES)
        diff_stars = "⭐" * b["difficulty"]
        boss_tag = " 👑 **JEFE FINAL**" if b.get("is_boss") else ""
        embed.add_field(
            name=f"{b['name']}{boss_tag} {diff_stars}",
            value=f"{b['desc']}\n🎭 Equipo: {team_preview}\n💰 Recompensa: {b['reward_coins']}🪙 +{b['reward_xp']}XP",
            inline=False
        )


    view = discord.ui.View(timeout=60)
    for b in BOT_ROSTER:
        style = discord.ButtonStyle.danger if b.get("is_boss") else discord.ButtonStyle.primary
        btn = discord.ui.Button(
            label=b["name"],
            style=style,
            custom_id=f"fight_{b['id']}"
        )
        btn.callback = make_bot_fight_callback(b, user, interaction.user.id)
        view.add_item(btn)

    await interaction.response.send_message(embed=embed, view=view)

def make_bot_fight_callback(bot_data, user, user_discord_id):
    async def callback(inter: discord.Interaction):
        if inter.user.id != user_discord_id:
            await inter.response.send_message("❌ Este menú no es tuyo.", ephemeral=True)
            return
        if inter.channel_id in active_battles:
            await inter.response.send_message("❌ Ya hay una batalla activa.", ephemeral=True)
            return

        db = load_db()
        usr = get_user(db, inter.user.id)
        owned = usr.get("figures", [])

        team_indices = usr.get("team", [None, None, None])
        p1_keys, p1_figs_data = [], []
        for idx in team_indices:
            if idx is not None and idx < len(owned):
                p1_keys.append(owned[idx]["key"])
                p1_figs_data.append(owned[idx])
        while len(p1_keys) < 3 and owned:
            p1_keys.append(owned[0]["key"])
            p1_figs_data.append(owned[0])

        bot_level  = bot_data["level"]
        hp_mult    = bot_data.get("hp_mult", 1.0)
        atk_mult   = bot_data.get("atk_mult", 1.0)
        nrg_bonus  = bot_data.get("energy_bonus", 0)
        p2_keys = bot_data["team"]
        p2_figs_data = [{"key": k, "level": bot_level, "xp": 0, "hp_mult": hp_mult, "atk_mult": atk_mult, "energy_bonus": nrg_bonus} for k in p2_keys]

        battle = BattleState(
            p1_id=inter.user.id,
            p2_id=0,
            p1_team_keys=p1_keys,
            p2_team_keys=p2_keys,
            p1_figs_data=p1_figs_data,
            p2_figs_data=p2_figs_data,
            is_bot=True
        )
        battle.p1_name = usr["name"]
        battle.p2_name = bot_data["name"]
        battle.bot_reward_coins = bot_data["reward_coins"]
        battle.bot_reward_xp = bot_data["reward_xp"]

        active_battles[inter.channel_id] = battle

        boss_title = "💀 ¡BATALLA CONTRA EL JEFE FINAL!" if bot_data.get("is_boss") else f"⚔️ ¡BATALLA vs {bot_data['name']}!"
        embed = battle.get_embed(title=boss_title)
        view = get_battle_view(battle)
        await inter.response.edit_message(embed=embed, view=view)
        # Guardar referencia al mensaje para poder editarlo al cambiar figura
        battle.message = await inter.original_response()
    return callback

# --- RETAR A JUGADOR ---
@bot.tree.command(name="retar", description="Reta a otro jugador a un duelo PvP de equipos")
@app_commands.describe(rival="El jugador al que quieres retar")
async def retar(interaction: discord.Interaction, rival: discord.Member):
    db = load_db()
    user = get_user(db, interaction.user.id)
    rival_data = get_user(db, rival.id)

    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return
    if not rival_data:
        await interaction.response.send_message("❌ Tu rival no está registrado.", ephemeral=True)
        return
    if rival.id == interaction.user.id:
        await interaction.response.send_message("❌ No puedes retarte a ti mismo.", ephemeral=True)
        return
    if not user.get("figures"):
        await interaction.response.send_message("❌ No tienes figuras. Compra en `/tienda`.", ephemeral=True)
        return
    if not rival_data.get("figures"):
        await interaction.response.send_message(f"❌ {rival.mention} no tiene figuras.", ephemeral=True)
        return
    if interaction.channel_id in active_battles:
        await interaction.response.send_message("❌ Ya hay batalla activa aquí.", ephemeral=True)
        return

    u1_figs = user["figures"]
    u2_figs = rival_data["figures"]

    def build_team(figs, team_indices):
        keys, datas = [], []
        for idx in (team_indices or []):
            if idx is not None and idx < len(figs):
                keys.append(figs[idx]["key"]); datas.append(figs[idx])
        while len(keys) < 3 and figs:
            keys.append(figs[0]["key"]); datas.append(figs[0])
        return keys[:3], datas[:3]

    u1_keys, u1_data = build_team(u1_figs, user.get("team", []))
    u2_keys, u2_data = build_team(u2_figs, rival_data.get("team", []))

    # Preview del equipo
    def team_preview(keys):
        names = []
        for k in keys:
            fig = FIGURES.get(k)
            if fig: names.append(f"{fig['emoji']} {fig['name']}")
        return " | ".join(names)

    embed = discord.Embed(
        title="⚔️ ¡DESAFÍO PvP!",
        description=f"{interaction.user.mention} reta a {rival.mention} a un duelo de equipos!",
        color=0xe74c3c
    )
    embed.add_field(name=f"🥊 {user['name']}", value=team_preview(u1_keys), inline=False)
    embed.add_field(name="⚡ VS ⚡", value="\u200b", inline=False)
    embed.add_field(name=f"🥊 {rival_data['name']}", value=team_preview(u2_keys), inline=False)

    accept_btn = discord.ui.Button(label="✅ Aceptar", style=discord.ButtonStyle.success, custom_id="accept_pvp")
    reject_btn = discord.ui.Button(label="❌ Rechazar", style=discord.ButtonStyle.danger, custom_id="reject_pvp")

    async def accept_callback(btn_inter: discord.Interaction):
        if btn_inter.user.id != rival.id:
            await btn_inter.response.send_message("❌ Solo el retado puede aceptar.", ephemeral=True)
            return
        if interaction.channel_id in active_battles:
            await btn_inter.response.send_message("❌ Ya hay una batalla activa.", ephemeral=True)
            return
        db2 = load_db()
        u1 = get_user(db2, interaction.user.id)
        u2 = get_user(db2, rival.id)
        def bteam(figs, tidx):
            ks, ds = [], []
            for i in (tidx or []):
                if i is not None and i < len(figs):
                    ks.append(figs[i]["key"]); ds.append(figs[i])
            while len(ks) < 3 and figs:
                ks.append(figs[0]["key"]); ds.append(figs[0])
            return ks[:3], ds[:3]

        k1, d1 = bteam(u1["figures"], u1.get("team", []))
        k2, d2 = bteam(u2["figures"], u2.get("team", []))

        battle = BattleState(
            p1_id=interaction.user.id,
            p2_id=rival.id,
            p1_team_keys=k1,
            p2_team_keys=k2,
            p1_figs_data=d1,
            p2_figs_data=d2,
            is_bot=False
        )
        battle.p1_name = get_user(db2, interaction.user.id)["name"]
        battle.p2_name = get_user(db2, rival.id)["name"]
        active_battles[interaction.channel_id] = battle
        view = get_battle_view(battle)
        await btn_inter.response.edit_message(embed=battle.get_embed(title="⚔️ ¡LA BATALLA COMIENZA!"), view=view)
        battle.message = await btn_inter.original_response()

    async def reject_callback(btn_inter: discord.Interaction):
        if btn_inter.user.id != rival.id:
            await btn_inter.response.send_message("❌ Solo el retado puede rechazar.", ephemeral=True)
            return
        reject_embed = discord.Embed(title="❌ Desafío rechazado", description=f"{rival.mention} rechazó el duelo.", color=0x95a5a6)
        await btn_inter.response.edit_message(embed=reject_embed, view=None)

    accept_btn.callback = accept_callback
    reject_btn.callback = reject_callback
    view = discord.ui.View(timeout=60)
    view.add_item(accept_btn)
    view.add_item(reject_btn)
    await interaction.response.send_message(content=rival.mention, embed=embed, view=view)

# --- RANKING ---
@bot.tree.command(name="ranking", description="Top 10 jugadores del servidor")
async def ranking(interaction: discord.Interaction):
    db = load_db()
    users = db.get("users", {})
    if not users:
        await interaction.response.send_message("📭 Nadie registrado aún.", ephemeral=True)
        return

    sorted_users = sorted(users.values(), key=lambda u: u.get("wins", 0), reverse=True)[:10]

    embed = discord.Embed(title="🏆 Ranking del Androide del PvP", color=0xf1c40f)
    medals = ["🥇", "🥈", "🥉"] + ["🔸"] * 7

    for i, u in enumerate(sorted_users):
        winrate = 0
        total = u.get("wins", 0) + u.get("losses", 0)
        if total > 0:
            winrate = round((u.get("wins", 0) / total) * 100, 1)
        embed.add_field(
            name=f"{medals[i]} {u['name']} (Nv.{u.get('level',1)})",
            value=f"✅ {u.get('wins',0)}V / ❌ {u.get('losses',0)}D | WR: {winrate}% | 💰 {u.get('coins',0):,}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# --- RECOMPENSA DIARIA ---
DAILY_MAX_STREAK = 7

DAILY_STREAK_REWARDS = {
    1: {"coins": 300,  "emoji": "📦", "label": "Día 1"},
    2: {"coins": 350,  "emoji": "📦", "label": "Día 2"},
    3: {"coins": 450,  "emoji": "🎁", "label": "Día 3"},
    4: {"coins": 500,  "emoji": "🎁", "label": "Día 4"},
    5: {"coins": 600,  "emoji": "💎", "label": "Día 5"},
    6: {"coins": 700,  "emoji": "💎", "label": "Día 6"},
    7: {"coins": 1000, "emoji": "🌟", "label": "¡Racha Máxima!"},
}

# Probabilidad de figura según racha (día: % de chance)
DAILY_FIGURE_CHANCE = {
    1: 10,   # 10% día 1
    2: 12,
    3: 18,
    4: 22,
    5: 30,
    6: 40,
    7: 60,   # 60% en racha máxima
}

# Probabilidad de rareza según racha
def get_figure_rarity_pool(streak):
    """Devuelve un pool de claves de figuras ponderado por rareza según la racha."""
    pool = []
    for key, fig in FIGURES.items():
        rarity = fig["rarity"]
        # A más racha, más peso a figuras raras/épicas/legendarias
        if rarity == "común":
            weight = max(1, 6 - streak)        # baja con racha
        elif rarity == "raro":
            weight = 3
        elif rarity == "épico":
            weight = streak                     # sube con racha
        elif rarity == "legendario":
            weight = max(0, streak - 4)         # solo aparece en racha 5+
        pool.extend([key] * weight)
    return pool

@bot.tree.command(name="diario", description="Reclama tu recompensa diaria (cada 24 horas)")
async def diario(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return

    now = datetime.now(timezone.utc)
    last_daily = user.get("last_daily")
    streak = user.get("daily_streak", 0)

    if last_daily:
        last_dt = datetime.fromisoformat(last_daily)
        diff_hours = (now - last_dt).total_seconds() / 3600

        if diff_hours < 24:
            remaining = 24 - diff_hours
            horas = int(remaining)
            minutos = int((remaining - horas) * 60)

            embed = discord.Embed(
                title="⏰ Ya reclamaste tu recompensa hoy",
                description=f"Vuelve en **{horas}h {minutos}m** para el siguiente diario.",
                color=0xe74c3c
            )
            embed.add_field(name="🔥 Racha actual", value=f"{streak} día(s)", inline=True)
            barra = "".join(
                DAILY_STREAK_REWARDS[d]["emoji"] if d <= streak else "⬛"
                for d in range(1, DAILY_MAX_STREAK + 1)
            )
            embed.add_field(name="📅 Racha semanal", value=barra, inline=False)
            # Mostrar % de figura del día siguiente
            next_streak = min(streak + 1, DAILY_MAX_STREAK)
            chance = DAILY_FIGURE_CHANCE[next_streak]
            embed.add_field(
                name="🎲 Mañana tendrás",
                value=f"**{chance}%** de probabilidad de ganar una figura gratis!",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        elif diff_hours >= 48:
            streak = 0

    # Reclamar recompensa
    streak = min(streak + 1, DAILY_MAX_STREAK)
    reward = DAILY_STREAK_REWARDS[streak]
    coins_earned = reward["coins"]

    user["coins"] = user.get("coins", 0) + coins_earned
    user["last_daily"] = now.isoformat()
    user["daily_streak"] = streak

    # ¿Gana figura?
    figure_won = None
    chance = DAILY_FIGURE_CHANCE[streak]
    owned_keys = [f["key"] for f in user.get("figures", [])]
    available_keys = [k for k in FIGURES.keys() if k not in owned_keys]

    if available_keys and random.randint(1, 100) <= chance:
        pool = [k for k in get_figure_rarity_pool(streak) if k in available_keys]
        if pool:
            figure_won = random.choice(pool)
            user["figures"].append({"key": figure_won, "level": 1, "xp": 0})
            if not user.get("active_figure"):
                user["active_figure"] = figure_won

    save_db(db)

    # Embed principal
    is_max = streak == DAILY_MAX_STREAK
    color = 0xf1c40f if is_max else (0x9b59b6 if streak >= 5 else (0x3498db if streak >= 3 else 0x2ecc71))

    desc = "🎊 ¡RACHA MÁXIMA! ¡INCREÍBLE! 🎊" if is_max else f"¡Buen trabajo, **{user['name']}**!"
    embed = discord.Embed(
        title=f"{reward['emoji']} ¡Recompensa Diaria Reclamada!",
        description=desc,
        color=color
    )

    embed.add_field(name="💰 Monedas ganadas", value=f"+**{coins_earned:,}** monedas", inline=True)
    embed.add_field(name="💳 Total actual", value=f"**{user['coins']:,}** monedas", inline=True)
    embed.add_field(name="🔥 Racha", value=f"**{streak}** día(s) seguidos", inline=True)

    barra = "".join(
        DAILY_STREAK_REWARDS[d]["emoji"] if d <= streak else "⬛"
        for d in range(1, DAILY_MAX_STREAK + 1)
    )
    embed.add_field(name="📅 Progreso semanal", value=barra, inline=False)

    # Bloque de figura ganada
    if figure_won:
        fig = FIGURES[figure_won]
        star = RARITY_STARS[fig["rarity"]]
        embed.add_field(
            name="🎉 ¡FIGURA SORPRESA!",
            value=(
                f"{fig['emoji']} **{fig['name']}** {star}\n"
                f"Rareza: **{fig['rarity'].upper()}**\n"
                f"❤️ HP:{fig['hp']} ⚔️ ATK:{fig['attack']} 🛡️ DEF:{fig['defense']} ⚡ VEL:{fig['speed']}\n" +
                " | ".join(f"✨{sk['name']}" for sk in FIGURE_SKILLS.get(key, []))
            ),
            inline=False
        )
        if fig.get("image"):
            embed.set_image(url=fig["image"])
        embed.color = RARITY_COLOR[fig["rarity"]]
    else:
        # Mostrar % de figura para motivar
        embed.add_field(
            name="🎲 Probabilidad de figura hoy",
            value=f"Tenías **{chance}%** de ganar una figura. ¡Sigue intentando mañana!",
            inline=False
        )

    # Próxima recompensa
    if streak < DAILY_MAX_STREAK:
        next_reward = DAILY_STREAK_REWARDS[streak + 1]
        next_chance = DAILY_FIGURE_CHANCE[streak + 1]
        embed.add_field(
            name="➡️ Mañana",
            value=(
                f"{next_reward['emoji']} **{next_reward['coins']:,}** monedas\n"
                f"🎲 **{next_chance}%** de probabilidad de figura!"
            ),
            inline=False
        )
    else:
        embed.add_field(
            name="🔄 Racha reiniciada",
            value="Mañana empieza una nueva racha semanal. ¡Eres una leyenda!",
            inline=False
        )
        user["daily_streak"] = 0
        save_db(db)

    embed.set_footer(text="Vuelve en 24 horas para mantener tu racha!")
    await interaction.response.send_message(embed=embed)

# --- AYUDA ---
@bot.tree.command(name="ayuda", description="Ver todos los comandos disponibles")
async def ayuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Androide del PvP — Comandos",
        description="¡Bienvenido al sistema de batallas de figuras!",
        color=0x3498db
    )
    embed.add_field(name="📋 Inicio", value="`/registrar` — Créate una cuenta y recibe 1,000 monedas", inline=False)
    embed.add_field(name="👤 Perfil", value="`/perfil` — Ve tus stats, nivel y monedas", inline=False)
    embed.add_field(name="🏪 Tienda", value="`/tienda` — Compra nuevas figuras con botones", inline=False)
    embed.add_field(name="🎭 Colección", value="`/misfiguras` — Ve todas tus figuras y sus niveles", inline=False)
    embed.add_field(name="⚡ Equipar", value="`/equipar` — Elige tu figura activa para batallar", inline=False)
    embed.add_field(name="🤖 PvP vs Bot", value="`/pvpbot` — Batalla contra un bot IA", inline=False)
    embed.add_field(name="⚔️ PvP", value="`/retar @usuario` — Reta a otro jugador a duelo", inline=False)
    embed.add_field(name="🏆 Ranking", value="`/ranking` — Top 10 del servidor", inline=False)
    embed.add_field(name="📅 Diario", value="`/diario` — Reclama monedas diarias y mantén tu racha!", inline=False)
    embed.add_field(name="💰 Admin", value="`/oro @usuario cantidad` — Regala monedas a un usuario [Solo admins]", inline=False)
    embed.add_field(name="🧑‍🍳 Cocina", value="`/cook` — Cocina con una langosta + hasta 3 ingredientes para conseguir buffs!\n`/ingredientes` — Ve tu despensa de ingredientes", inline=False)
    embed.set_footer(text="¡Colecciona, mejora y conquista la arena!")
    await interaction.response.send_message(embed=embed)


# --- LOBSTER ---
@bot.tree.command(name="lobster", description="🦞 Obtén una langosta misteriosa")
async def lobster_cmd(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return

    user["figures"].append({"key": "lobster", "level": 1, "xp": 0})
    # Añadir al equipo si hay hueco
    team = user.get("team", [None, None, None])
    while len(team) < 3: team.append(None)
    for i in range(3):
        if team[i] is None:
            team[i] = len(user["figures"]) - 1
            break
    user["team"] = team
    save_db(db)

    embed = discord.Embed(
        title="🦞 Una langosta ha aparecido",
        description="No sabes de dónde vino. No sabes qué quiere.\nPero ahora es tuya.",
        color=0xe74c3c
    )
    embed.add_field(name="❤️ Vida", value="1", inline=True)
    embed.add_field(name="⚔️ Ataque", value="1", inline=True)
    embed.add_field(name="🛡️ Defensa", value="1", inline=True)
    embed.add_field(
        name="✨ Habilidad: LOBSTER",
        value="No hace nada.\nO eso crees. Tiene un **0.01%** de matar a todas las figuras enemigas.",
        inline=False
    )
    embed.set_footer(text="Úsala con /equipar. Buena suerte.")
    await interaction.response.send_message(embed=embed)

# --- ORO (solo admins) ---
@bot.tree.command(name="oro", description="[ADMIN] Regala monedas a un usuario")
@app_commands.describe(usuario="Usuario al que regalar monedas", cantidad="Cantidad de monedas a regalar")
async def oro(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
        return
    if cantidad <= 0:
        await interaction.response.send_message("❌ La cantidad debe ser mayor a 0.", ephemeral=True)
        return
    db = load_db()
    target = get_user(db, usuario.id)
    if not target:
        await interaction.response.send_message(f"❌ {usuario.mention} no está registrado.", ephemeral=True)
        return
    target["coins"] = target.get("coins", 0) + cantidad
    save_db(db)
    embed = discord.Embed(title="💰 ¡Monedas regaladas!", color=0xf1c40f)
    embed.add_field(name="👤 Receptor", value=f"{target['name']} ({usuario.mention})", inline=True)
    embed.add_field(name="💰 Cantidad", value=f"+**{cantidad:,}** monedas", inline=True)
    embed.add_field(name="💳 Nuevo saldo", value=f"**{target['coins']:,}** monedas", inline=True)
    embed.set_footer(text=f"Otorgado por {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)
# ============================================================
#  PERMISOS DE ADMINISTRADOR
# ============================================================
MATHEO_ID = 357067563842297857  # ID de matheogamer64 (siempre tiene acceso)

def is_admin(interaction: discord.Interaction) -> bool:
    """Devuelve True si el usuario es admin del servidor o es matheogamer64."""
    if interaction.user.id == MATHEO_ID:
        return True
    # Verificar permisos de administrador en el servidor
    if isinstance(interaction.user, discord.Member):
        return interaction.user.guild_permissions.administrator
    return False

# --- RESET (cualquier usuario, solo afecta su canal) ---
@bot.tree.command(name="reset", description="Reinicia la batalla activa en este canal")
async def reset_battle(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Solo los admins pueden reiniciar batallas.", ephemeral=True)
        return
    removed = False
    if interaction.channel_id in active_battles:
        del active_battles[interaction.channel_id]
        removed = True
    # Limpiar también peleas PvP pendientes en este canal
    to_remove = [k for k, v in pending_pvp.items() if v.get("channel_id") == interaction.channel_id]
    for k in to_remove:
        del pending_pvp[k]
        removed = True
    if removed:
        embed = discord.Embed(
            title="🔄 Batalla reiniciada",
            description="La batalla activa en este canal ha sido cancelada. ¡Podéis iniciar una nueva!",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ No hay ninguna batalla activa en este canal.", ephemeral=True)

# --- BOMB (solo admins) ---
@bot.tree.command(name="bomb", description="[ADMIN] Quita monedas a un usuario")
@app_commands.describe(usuario="Usuario objetivo", cantidad="Monedas a quitar")
async def bomb(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
        return
    db = load_db()
    target = get_user(db, usuario.id)
    if not target:
        await interaction.response.send_message("❌ Usuario no registrado.", ephemeral=True)
        return
    if cantidad <= 0:
        await interaction.response.send_message("❌ La cantidad debe ser mayor a 0.", ephemeral=True)
        return
    before = target.get("coins", 0)
    target["coins"] = max(0, before - cantidad)
    save_db(db)
    embed = discord.Embed(title="💣 ¡BOOM!", color=0xe74c3c)
    embed.add_field(name="👤 Usuario", value=target["name"], inline=True)
    embed.add_field(name="💸 Monedas eliminadas", value=f"-**{cantidad:,}**", inline=True)
    embed.add_field(name="💳 Saldo restante", value=f"**{target['coins']:,}**", inline=True)
    await interaction.response.send_message(embed=embed)

# --- NUKE (solo admins) ---
@bot.tree.command(name="nuke", description="[ADMIN] Resetea a un usuario a nivel 1")
@app_commands.describe(usuario="Usuario a nukear")
async def nuke(interaction: discord.Interaction, usuario: discord.Member):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
        return
    db = load_db()
    target = get_user(db, usuario.id)
    if not target:
        await interaction.response.send_message("❌ Usuario no registrado.", ephemeral=True)
        return
    nombre = target["name"]
    target["coins"]   = 0
    target["figures"] = []
    target["team"]    = [None, None, None]
    target["level"]   = 1
    target["xp"]      = 0
    target["wins"]    = 0
    target["losses"]  = 0
    save_db(db)
    embed = discord.Embed(
        title="☢️ NUKE ACTIVADO",
        description=f"**{nombre}** ha sido reseteado a nivel 1.\nSin monedas. Sin figuras. Sin nada.",
        color=0xff0000
    )
    embed.set_footer(text="F en el chat")
    await interaction.response.send_message(embed=embed)

# --- ROB ---
ROB_COOLDOWN = {}  # {user_id: timestamp}

@bot.tree.command(name="rob", description="Intenta robarle monedas a otro usuario")
@app_commands.describe(usuario="Usuario al que intentar robar")
async def rob(interaction: discord.Interaction, usuario: discord.Member):
    if usuario.id == interaction.user.id:
        await interaction.response.send_message("❌ No puedes robarte a ti mismo.", ephemeral=True)
        return

    now = datetime.now(timezone.utc).timestamp()
    cd_key = interaction.user.id
    if cd_key in ROB_COOLDOWN:
        diff = now - ROB_COOLDOWN[cd_key]
        if diff < 600:  # 10 minutos
            restante = int(600 - diff)
            m = restante // 60
            s = restante % 60
            await interaction.response.send_message(
                f"⏰ Cooldown activo. Puedes robar de nuevo en **{m}m {s}s**.", ephemeral=True
            )
            return

    db = load_db()
    robber = get_user(db, interaction.user.id)
    victim = get_user(db, usuario.id)

    if not robber:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return
    if not victim:
        await interaction.response.send_message("❌ Ese usuario no está registrado.", ephemeral=True)
        return
    if victim.get("coins", 0) <= 0:
        await interaction.response.send_message("❌ Ese usuario no tiene monedas que robar.", ephemeral=True)
        return

    ROB_COOLDOWN[cd_key] = now

    roll = random.randint(1, 100)
    if roll <= 10:       # 10% — robo grande
        pct = random.uniform(0.30, 0.50)
        result = "grande"
    elif roll <= 35:     # 25% — robo mediano
        pct = random.uniform(0.10, 0.29)
        result = "mediano"
    elif roll <= 60:     # 25% — robo pequeño
        pct = random.uniform(0.01, 0.09)
        result = "pequeño"
    else:                # 40% — fallo
        result = "fallo"
        pct = 0

    embed = discord.Embed(color=0x9b59b6)
    if result == "fallo":
        embed.title = "🚨 ¡Te atraparon!"
        embed.description = f"Intentaste robarle a **{victim['name']}** pero te pillaron con las manos en la masa. ¡Qué vergüenza!"
        fine = min(victim.get("coins",0), random.randint(20, 80))
        robber["coins"] = max(0, robber.get("coins",0) - fine)
        embed.add_field(name="💸 Multa", value=f"-**{fine:,}** monedas por torpe", inline=True)
    else:
        stolen = max(1, int(victim.get("coins", 0) * pct))
        victim["coins"]  = max(0, victim.get("coins",0) - stolen)
        robber["coins"]  = robber.get("coins",0) + stolen
        icons = {"grande":"💰💰💰", "mediano":"💰💰", "pequeño":"💰"}
        embed.title = f"🦹 ¡Robo {icons[result]} exitoso!"
        embed.description = f"Le robaste a **{victim['name']}** sin que se diera cuenta."
        embed.add_field(name="💰 Robado", value=f"+**{stolen:,}** monedas", inline=True)
        embed.add_field(name="📊 Tipo", value=result.capitalize(), inline=True)
        embed.add_field(name="💳 Tu saldo", value=f"**{robber['coins']:,}**", inline=True)

    save_db(db)
    embed.set_footer(text="Cooldown: 2 horas")
    await interaction.response.send_message(embed=embed)

# --- WORK ---
WORK_COOLDOWN = {}  # {user_id: timestamp}
WORK_COOLDOWN_SECS = 3600  # 1 hora entre trabajos

@bot.tree.command(name="work", description="Trabaja para ganar monedas con un minijuego")
async def work(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return

    now = datetime.now(timezone.utc).timestamp()
    if interaction.user.id in WORK_COOLDOWN:
        diff = now - WORK_COOLDOWN[interaction.user.id]
        if diff < WORK_COOLDOWN_SECS:
            restante = int(WORK_COOLDOWN_SECS - diff)
            m = restante // 60
            s = restante % 60
            await interaction.response.send_message(
                f"⏰ Ya trabajaste hoy. Descansa **{m}m {s}s** más.", ephemeral=True
            )
            return

    # Elegir trabajo
    embed = discord.Embed(
        title="💼 ¿En qué quieres trabajar hoy?",
        description="Elige tu trabajo y demuestra lo que vales:",
        color=0x2ecc71
    )
    embed.add_field(name="🍔 Preparar Hamburguesas", value="Secuencia de botones. Recompensa: 80-300🪙", inline=False)
    embed.add_field(name="🎣 Pescar",                value="Opción múltiple. Recompensa: 50-400🪙",    inline=False)
    embed.add_field(name="🎬 Crear Videos",          value="Escribe rápido. Recompensa: 100-500🪙",    inline=False)

    view = discord.ui.View(timeout=30)
    for job_id, label in [("burger","🍔 Hamburguesas"), ("fish","🎣 Pescar"), ("video","🎬 Videos")]:
        btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=f"job_{job_id}")
        btn.callback = make_job_callback(job_id, interaction.user.id)
        view.add_item(btn)

    await interaction.response.send_message(embed=embed, view=view)

def make_job_callback(job_id: str, user_discord_id: int):
    async def callback(inter: discord.Interaction):
        if inter.user.id != user_discord_id:
            await inter.response.send_message("❌ Este trabajo no es tuyo.", ephemeral=True)
            return
        WORK_COOLDOWN[inter.user.id] = datetime.now(timezone.utc).timestamp()
        if job_id == "burger":
            await start_burger_minigame(inter)
        elif job_id == "fish":
            await start_fish_minigame(inter)
        elif job_id == "video":
            await start_video_minigame(inter)
    return callback

# ── MINIJUEGO 1: HAMBURGUESAS (secuencia de botones) ──────────────────────────
BURGER_SEQUENCES = [
    ["🥩","🧀","🥬","🍅","🥚"],
    ["🥬","🥩","🧀","🥚","🍅"],
    ["🧀","🥚","🥩","🍅","🥬"],
    ["🍅","🥬","🥚","🧀","🥩"],
]

async def start_burger_minigame(inter: discord.Interaction):
    sequence = random.choice(BURGER_SEQUENCES)
    seq_display = " → ".join(sequence)
    embed = discord.Embed(
        title="🍔 ¡Prepara la hamburguesa!",
        description=f"Añade los ingredientes en este orden:\n**{seq_display}**\n\nTienes 20 segundos!",
        color=0xe67e22
    )
    state = {"sequence": sequence, "progress": [], "user_id": inter.user.id}

    view = make_burger_view(state, inter)
    await inter.response.edit_message(embed=embed, view=view)

def make_burger_view(state, orig_inter):
    view = discord.ui.View(timeout=20)
    ingredients = ["🥩","🧀","🥬","🍅","🥚"]
    random.shuffle(ingredients)

    for ing in ingredients:
        btn = discord.ui.Button(label=ing, style=discord.ButtonStyle.secondary, custom_id=f"ing_{ing}")
        async def ing_cb(inter: discord.Interaction, ingredient=ing, s=state, oi=orig_inter):
            if inter.user.id != s["user_id"]:
                await inter.response.send_message("❌ No es tu minijuego.", ephemeral=True)
                return
            s["progress"].append(ingredient)
            expected = s["sequence"][len(s["progress"])-1]
            if ingredient != expected:
                # Error — calcular recompensa parcial
                correct = len(s["progress"]) - 1
                coins = max(30, correct * 40)
                db = load_db(); u = get_user(db, inter.user.id)
                u["coins"] = u.get("coins",0) + coins; save_db(db)
                embed = discord.Embed(title="❌ ¡Ingrediente equivocado!",
                    description=f"Pusiste **{ingredient}** pero era **{expected}**.\n+**{coins}**🪙 por {correct} ingredientes correctos.",
                    color=0xe74c3c)
                await inter.response.edit_message(embed=embed, view=None)
                return
            if len(s["progress"]) == len(s["sequence"]):
                # ¡Perfecto!
                coins = random.randint(200, 300)
                db = load_db(); u = get_user(db, inter.user.id)
                u["coins"] = u.get("coins",0) + coins; save_db(db)
                embed = discord.Embed(title="🍔 ¡Hamburguesa perfecta!",
                    description=f"¡Orden completada! +**{coins}**🪙", color=0x2ecc71)
                await inter.response.edit_message(embed=embed, view=None)
                return
            # Siguiente ingrediente
            done = " ✅ ".join(s["progress"])
            remaining = len(s["sequence"]) - len(s["progress"])
            embed = discord.Embed(title="🍔 ¡Bien!",
                description=f"Añadido: {done}\nFaltan **{remaining}** ingredientes...",
                color=0xe67e22)
            await inter.response.edit_message(embed=embed, view=make_burger_view(s, oi))
        btn.callback = ing_cb
        view.add_item(btn)
    return view

# ── MINIJUEGO 2: PESCAR (opción múltiple) ─────────────────────────────────────
FISH_QUESTIONS = [
    {"q": "El agua está turbia y hay algas. ¿Qué cebo usas?", "opts": ["🪱 Gusano","🐟 Pececillo","🌽 Maíz","🦐 Camarón"], "ans": "🦐 Camarón", "coins": (200,400)},
    {"q": "Es de madrugada en un río. ¿Dónde lanzas?", "opts": ["🌊 Centro","🪨 Rocas","🌿 Orilla con plantas","🏖️ Playa abierta"], "ans": "🌿 Orilla con plantas", "coins": (150,350)},
    {"q": "El pez picó pero está resistiendo fuerte. ¿Qué haces?", "opts": ["💪 Tiro fuerte","⏳ Espero y suelto hilo","🎣 Recojo rápido","❌ Suelto la caña"], "ans": "⏳ Espero y suelto hilo", "coins": (180,380)},
    {"q": "¿Qué hora es mejor para pescar peces grandes?", "opts": ["🌅 Amanecer","☀️ Mediodía","🌆 Atardecer","🌙 Noche"], "ans": "🌅 Amanecer", "coins": (100,300)},
    {"q": "Ves burbujas en el agua. ¿Qué significa?", "opts": ["💨 Gas del fondo","🐟 Peces alimentándose","🐊 Peligro","🪨 Corriente"], "ans": "🐟 Peces alimentándose", "coins": (220,420)},
]

async def start_fish_minigame(inter: discord.Interaction):
    q = random.choice(FISH_QUESTIONS)
    embed = discord.Embed(
        title="🎣 ¡Momento de pescar!",
        description=f"**{q['q']}**\n\nElige la respuesta correcta:",
        color=0x3498db
    )
    view = discord.ui.View(timeout=20)
    opts = q["opts"].copy(); random.shuffle(opts)
    for opt in opts:
        style = discord.ButtonStyle.primary
        btn = discord.ui.Button(label=opt, style=style, custom_id=f"fish_{opt}")
        async def fish_cb(fi: discord.Interaction, choice=opt, question=q, uid=inter.user.id):
            if fi.user.id != uid:
                await fi.response.send_message("❌ No es tu minijuego.", ephemeral=True)
                return
            if choice == question["ans"]:
                coins = random.randint(*question["coins"])
                db = load_db(); u = get_user(db, fi.user.id)
                u["coins"] = u.get("coins",0) + coins; save_db(db)
                embed2 = discord.Embed(title="🎣 ¡Pez capturado!",
                    description=f"¡Respuesta correcta! +**{coins}**🪙", color=0x2ecc71)
            else:
                coins = random.randint(30, 80)
                db = load_db(); u = get_user(db, fi.user.id)
                u["coins"] = u.get("coins",0) + coins; save_db(db)
                embed2 = discord.Embed(title="🎣 ¡Se escapó el pez!",
                    description=f"Respuesta incorrecta. La correcta era **{question['ans']}**.\n+**{coins}**🪙 de consolación.",
                    color=0xe74c3c)
            await fi.response.edit_message(embed=embed2, view=None)
        btn.callback = fish_cb
        view.add_item(btn)
    await inter.response.edit_message(embed=embed, view=view)

# ── MINIJUEGO 3: CREAR VIDEOS (escribe rápido) ────────────────────────────────
VIDEO_CHALLENGES = [
    {"prompt": "Tu video se llama: **'Top 10 momentos épicos'**\nEscribe exactamente: `epico`",       "answer": "epico",       "coins": (200,350)},
    {"prompt": "El algoritmo pide un hashtag. Escribe: `viral`",                                        "answer": "viral",       "coins": (150,300)},
    {"prompt": "Tu intro necesita energía. Escribe: `subscribe`",                                       "answer": "subscribe",   "coins": (180,380)},
    {"prompt": "El editor te pide la música. Escribe: `bangermusic`",                                   "answer": "bangermusic", "coins": (250,450)},
    {"prompt": "El thumbnail necesita texto. Escribe: `clickbait`",                                     "answer": "clickbait",   "coins": (200,400)},
]

async def start_video_minigame(inter: discord.Interaction):
    challenge = random.choice(VIDEO_CHALLENGES)
    embed = discord.Embed(
        title="🎬 ¡Estudio de grabación!",
        description=f"{challenge['prompt']}\n\n⏰ Tienes **30 segundos** para responder en el chat.",
        color=0x9b59b6
    )
    await inter.response.edit_message(embed=embed, view=None)
    msg = await inter.original_response()

    def check(m):
        return m.author.id == inter.user.id and m.channel.id == inter.channel_id

    try:
        response = await bot.wait_for("message", check=check, timeout=30)
        if response.content.strip().lower() == challenge["answer"]:
            coins = random.randint(*challenge["coins"])
            db = load_db(); u = get_user(db, inter.user.id)
            u["coins"] = u.get("coins",0) + coins; save_db(db)
            embed2 = discord.Embed(title="🎬 ¡Video viral!",
                description=f"¡Correcto! Tu video arrasa en internet.\n+**{coins}**🪙", color=0x2ecc71)
        else:
            coins = random.randint(40, 100)
            db = load_db(); u = get_user(db, inter.user.id)
            u["coins"] = u.get("coins",0) + coins; save_db(db)
            embed2 = discord.Embed(title="🎬 ¡Demonetizado!",
                description=f"Escribiste **{response.content}** pero era **{challenge['answer']}**.\n+**{coins}**🪙 de consuelo.",
                color=0xe74c3c)
        await msg.edit(embed=embed2)
        try: await response.delete()
        except: pass
    except asyncio.TimeoutError:
        coins = 0
        embed2 = discord.Embed(title="🎬 ¡Se venció el tiempo!",
            description="Tardaste demasiado. El video fue eliminado por copyright. +0🪙",
            color=0x95a5a6)
        await msg.edit(embed=embed2)



# ============================================================
#  SISTEMA DE COCINA
# ============================================================
INGREDIENTS = {
    "🦞": "Langosta",
    "🌶️": "Chile",
    "🧄": "Ajo",
    "🧅": "Cebolla",
    "🫙": "Salsa Secreta",
    "🍖": "Carne",
    "🌿": "Hierbas",
    "🥚": "Huevo",
    "🧀": "Queso",
    "🍫": "Chocolate",
}

RECIPES = [
    {
        "name": "🦞🌶️🧄 Langosta Picante",
        "ingredients": ["🦞", "🌶️", "🧄"],
        "effect": "coins_boost",
        "value": 1.5,
        "desc": "¡+50% de monedas ganadas en batalla por 3 victorias!",
        "turns": 3,
    },
    {
        "name": "🦞🍖🧅 Estofado de Langosta",
        "ingredients": ["🦞", "🍖", "🧅"],
        "effect": "hp_boost",
        "value": 30,
        "desc": "¡+30 HP a todas las figuras de tu equipo en la próxima batalla!",
        "turns": 1,
    },
    {
        "name": "🦞🫙🌿 Langosta Gourmet",
        "ingredients": ["🦞", "🫙", "🌿"],
        "effect": "atk_boost",
        "value": 10,
        "desc": "¡+10 ATK a todas las figuras de tu equipo en la próxima batalla!",
        "turns": 1,
    },
    {
        "name": "🦞🥚🧀 Langosta con Queso",
        "ingredients": ["🦞", "🥚", "🧀"],
        "effect": "xp_boost",
        "value": 2.0,
        "desc": "¡XP x2 en la próxima batalla!",
        "turns": 1,
    },
    {
        "name": "🦞🍫🌿 Langosta Dulce",
        "ingredients": ["🦞", "🍫", "🌿"],
        "effect": "level_fig",
        "value": 1,
        "desc": "¡Sube 1 nivel a la figura frontal de tu equipo!",
        "turns": 1,
    },
    {
        "name": "🦞🧄🧅 Langosta Tradicional",
        "ingredients": ["🦞", "🧄", "🧅"],
        "effect": "coins_boost",
        "value": 1.3,
        "desc": "¡+30% de monedas por 2 victorias!",
        "turns": 2,
    },
    {
        "name": "🦞🍖🫙 Langosta a la Brasa",
        "ingredients": ["🦞", "🍖", "🫙"],
        "effect": "atk_boost",
        "value": 15,
        "desc": "¡+15 ATK a todas tus figuras en la próxima batalla!",
        "turns": 1,
    },
    {
        "name": "🦞🌶️🧀 Langosta Explosiva",
        "ingredients": ["🦞", "🌶️", "🧀"],
        "effect": "hp_boost",
        "value": 50,
        "desc": "¡+50 HP a todas las figuras de tu equipo en la próxima batalla!",
        "turns": 1,
    },
]

TOTAL_RECIPES_FOR_EVENT = 40  # Recetas globales necesarias para Langosta Madre

# Contador global de recetas cocinadas
global_recipe_count = 0
lobster_madre_active = False

# Ingredientes que el jugador puede conseguir en batallas (se añaden a user["ingredients"])
BATTLE_INGREDIENT_DROP_CHANCE = 40  # 40% de probabilidad de conseguir ingrediente al ganar batalla

def give_battle_ingredient(user):
    """Da un ingrediente aleatorio al usuario (excepto langosta, que va por /lobster)."""
    non_lobster = [k for k in INGREDIENTS if k != "🦞"]
    ingredient = random.choice(non_lobster)
    if "ingredients" not in user:
        user["ingredients"] = {}
    user["ingredients"][ingredient] = user["ingredients"].get(ingredient, 0) + 1
    return ingredient

@bot.tree.command(name="ingredientes", description="Ve tus ingredientes de cocina actuales")
async def ingredientes_cmd(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return
    ings = user.get("ingredients", {})
    # Langosta del inventario de figuras
    lobster_count = sum(1 for f in user.get("figures", []) if f["key"] == "lobster")
    embed = discord.Embed(title="🧑‍🍳 Tu despensa", color=0xe67e22)
    ing_str = ""
    if lobster_count:
        ing_str += f"🦞 Langosta x{lobster_count}\n"
    for emoji, amount in ings.items():
        name = INGREDIENTS.get(emoji, emoji)
        ing_str += f"{emoji} {name} x{amount}\n"
    embed.description = ing_str or "_Sin ingredientes. ¡Gana batallas o consigue una langosta!_"
    embed.set_footer(text=f"Recetas globales cocinadas: {global_recipe_count}/{TOTAL_RECIPES_FOR_EVENT}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="cook", description="Cocina una receta combinando una langosta con hasta 3 ingredientes")
async def cook_cmd(interaction: discord.Interaction):
    global global_recipe_count, lobster_madre_active
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return
    # Verificar que tiene al menos una langosta
    lobster_idx = next((i for i, f in enumerate(user.get("figures", [])) if f["key"] == "lobster"), None)
    if lobster_idx is None:
        await interaction.response.send_message("❌ Necesitas al menos una 🦞 Langosta. Consíguela con `/lobster`.", ephemeral=True)
        return
    ings = user.get("ingredients", {})
    available = {k: v for k, v in ings.items() if v > 0}
    if not available:
        await interaction.response.send_message("❌ No tienes ingredientes. ¡Gana batallas para conseguir algunos!", ephemeral=True)
        return

    # Mostrar selector de ingredientes
    ing_options = [discord.SelectOption(label=f"{emoji} {INGREDIENTS.get(emoji, emoji)} x{amt}", value=emoji, emoji=emoji)
                   for emoji, amt in available.items()]

    state = {"selected": [], "user_id": interaction.user.id}

    async def show_cook_menu(inter, state, is_first=False):
        selected_str = " + ".join(state["selected"]) if state["selected"] else "_Ninguno aún_"
        embed = discord.Embed(
            title="🧑‍🍳 ¡Hora de cocinar!",
            description=f"🦞 Langosta + **{selected_str}**\n\nElige hasta 3 ingredientes y luego **Cocinar**:",
            color=0xe67e22
        )
        view = discord.ui.View(timeout=60)
        # Select de ingredientes
        sel = discord.ui.Select(
            placeholder="Añadir ingrediente...",
            options=ing_options,
            max_values=1
        )
        async def add_ingredient(si: discord.Interaction):
            if si.user.id != state["user_id"]:
                await si.response.send_message("❌ No es tu menú.", ephemeral=True)
                return
            chosen = sel.values[0]
            if len(state["selected"]) >= 3:
                await si.response.send_message("❌ Máximo 3 ingredientes.", ephemeral=True)
                return
            state["selected"].append(chosen)
            await si.response.edit_message(
                embed=discord.Embed(title="🧑‍🍳 ¡Hora de cocinar!", description=f"🦞 Langosta + **{' + '.join(state['selected'])}**\n\nElige más o presiona Cocinar:", color=0xe67e22),
                view=build_cook_view(state, si)
            )
        sel.callback = add_ingredient
        view.add_item(sel)

        cook_btn = discord.ui.Button(label="🍳 ¡Cocinar!", style=discord.ButtonStyle.success, disabled=len(state["selected"]) == 0)
        async def do_cook(ci: discord.Interaction):
            if ci.user.id != state["user_id"]:
                await ci.response.send_message("❌ No es tu menú.", ephemeral=True)
                return
            global global_recipe_count, lobster_madre_active
            db2 = load_db()
            user2 = get_user(db2, ci.user.id)
            # Verificar langosta
            lb_idx = next((i for i, f in enumerate(user2.get("figures", [])) if f["key"] == "lobster"), None)
            if lb_idx is None:
                await ci.response.edit_message(content="❌ Ya no tienes langosta.", embed=None, view=None)
                return
            # Verificar ingredientes
            ings2 = user2.get("ingredients", {})
            for ing in state["selected"]:
                if ings2.get(ing, 0) <= 0:
                    await ci.response.edit_message(content=f"❌ Ya no tienes {ing}.", embed=None, view=None)
                    return
            # Consumir
            user2["figures"].pop(lb_idx)
            for ing in state["selected"]:
                ings2[ing] -= 1
            user2["ingredients"] = ings2
            # Buscar receta
            matched = None
            for recipe in RECIPES:
                recipe_ings = set(recipe["ingredients"])
                used = set(["🦞"] + state["selected"])
                if recipe_ings == used:
                    matched = recipe
                    break
            global_recipe_count += 1
            if "recipe_count" not in user2:
                user2["recipe_count"] = 0
            user2["recipe_count"] = user2.get("recipe_count", 0) + 1
            # Aplicar efecto
            result_desc = ""
            if matched:
                if "buffs" not in user2:
                    user2["buffs"] = []
                user2["buffs"].append({"effect": matched["effect"], "value": matched["value"], "turns": matched["turns"]})
                if matched["effect"] == "level_fig":
                    team = user2.get("team", [])
                    if team and team[0] is not None and team[0] < len(user2.get("figures", [])):
                        user2["figures"][team[0]]["level"] = user2["figures"][team[0]].get("level", 1) + 1
                result_desc = matched["desc"]
                recipe_name = matched["name"]
            else:
                # Receta desconocida: monedas aleatorias
                coins = random.randint(50, 200)
                user2["coins"] = user2.get("coins", 0) + coins
                recipe_name = "🍲 Receta Experimental"
                result_desc = f"No es receta conocida, pero huele bien. +{coins}🪙"
            save_db(db2)
            embed2 = discord.Embed(
                title=f"✅ {recipe_name}",
                description=result_desc,
                color=0x2ecc71
            )
            embed2.set_footer(text=f"Recetas globales: {global_recipe_count}/{TOTAL_RECIPES_FOR_EVENT}")
            await ci.response.edit_message(embed=embed2, view=None)
            # ¿Langosta Madre?
            if global_recipe_count >= TOTAL_RECIPES_FOR_EVENT and not lobster_madre_active:
                lobster_madre_active = True
                await trigger_lobster_madre(ci.channel)
        cook_btn.callback = do_cook
        view.add_item(cook_btn)
        return view

    def build_cook_view(state, inter):
        import asyncio as _asyncio
        view = discord.ui.View(timeout=60)
        sel2 = discord.ui.Select(placeholder="Añadir otro ingrediente...", options=ing_options, max_values=1)
        async def add_again(si: discord.Interaction):
            if si.user.id != state["user_id"]:
                await si.response.send_message("❌ No es tu menú.", ephemeral=True)
                return
            chosen = sel2.values[0]
            if len(state["selected"]) >= 3:
                await si.response.send_message("❌ Máximo 3 ingredientes.", ephemeral=True)
                return
            state["selected"].append(chosen)
            await si.response.edit_message(
                embed=discord.Embed(title="🧑‍🍳 ¡Hora de cocinar!", description=f"🦞 Langosta + **{' + '.join(state['selected'])}**", color=0xe67e22),
                view=build_cook_view(state, si)
            )
        sel2.callback = add_again
        view.add_item(sel2)
        cook2 = discord.ui.Button(label="🍳 ¡Cocinar!", style=discord.ButtonStyle.success)
        cook2.callback = do_cook
        view.add_item(cook2)
        return view

    view_final = await show_cook_menu(interaction, state, is_first=True)
    await interaction.response.send_message(
        embed=discord.Embed(title="🧑‍🍳 ¡Hora de cocinar!", description=f"🦞 Langosta + _Ninguno aún_\n\nElige ingredientes y luego Cocinar:", color=0xe67e22),
        view=view_final,
        ephemeral=True
    )

# ─── LANGOSTA MADRE (evento global) ───────────────────────────────────────────
LOBSTER_MADRE_HP = 300000
lobster_madre_state = {}

async def trigger_lobster_madre(channel):
    """Inicia el evento global de la Langosta Madre."""
    global lobster_madre_state
    lobster_madre_state = {
        "hp": LOBSTER_MADRE_HP,
        "max_hp": LOBSTER_MADRE_HP,
        "participants": {},  # user_id -> damage dealt
        "active": True,
    }
    embed = discord.Embed(
        title="🦞🦞🦞 ¡APARECE LA LANGOSTA MADRE! 🦞🦞🦞",
        description=(
            "¡40 recetas han sido cocinadas! ¡La **LANGOSTA MADRE** ha despertado!\n\n"
            "❤️ **HP:** 300,000\n⚔️ **ATK:** 70 | 🛡️ **DEF:** 30\n\n"
            "**¡Tienes 60 segundos para unirte!** Todos los jugadores que se unan atacarán juntos."
        ),
        color=0xe74c3c
    )
    view = discord.ui.View(timeout=60)
    join_btn = discord.ui.Button(label="⚔️ ¡UNIRME AL ATAQUE!", style=discord.ButtonStyle.danger, custom_id="join_lobster")
    async def join_cb(inter: discord.Interaction):
        uid = inter.user.id
        if not lobster_madre_state.get("active"):
            await inter.response.send_message("❌ El evento ya terminó.", ephemeral=True)
            return
        if uid in lobster_madre_state["participants"]:
            await inter.response.send_message("✅ Ya estás en el ataque!", ephemeral=True)
            return
        lobster_madre_state["participants"][uid] = 0
        await inter.response.send_message(f"⚔️ ¡<@{uid}> se unió al ataque! Ya somos **{len(lobster_madre_state['participants'])}** guerreros!", ephemeral=False)
    join_btn.callback = join_cb
    view.add_item(join_btn)
    msg = await channel.send(embed=embed, view=view)
    await asyncio.sleep(60)
    # ¡A pelear!
    await run_lobster_madre_battle(channel, msg)

async def run_lobster_madre_battle(channel, msg):
    """Ejecuta la batalla contra la Langosta Madre con todos los participantes."""
    global lobster_madre_active
    participants = list(lobster_madre_state.get("participants", {}).keys())
    if not participants:
        await channel.send("🦞 Nadie se unió al ataque... La Langosta Madre se retira victoriosa.")
        lobster_madre_active = False
        return

    lm_hp = lobster_madre_state["hp"]
    lm_max = lobster_madre_state["max_hp"]
    lm_atk = 70
    all_skills_pool = [sk for skills in FIGURE_SKILLS.values() for sk in skills
                       if sk["type"] not in ("consumed_fury", "revive_team", "ban_hammer", "drain_fill", "lobster")]
    round_num = 0

    while lm_hp > 0 and participants:
        round_num += 1
        log = [f"**Ronda {round_num}**"]

        # Jugadores atacan
        db = load_db()
        total_dmg = 0
        for uid in participants[:]:
            user = get_user(db, uid)
            if not user:
                participants.remove(uid)
                continue
            # Ataque básico del jugador
            atk = random.randint(15, 40)
            lm_hp = max(0, lm_hp - atk)
            total_dmg += atk
            lobster_madre_state["participants"][uid] = lobster_madre_state["participants"].get(uid, 0) + atk
        log.append(f"⚔️ Los {len(participants)} guerreros hacen **{total_dmg}** daño total! (🦞 HP: {lm_hp:,}/{lm_max:,})")

        if lm_hp <= 0:
            break

        # Langosta Madre ataca con habilidad aleatoria
        skill_used = random.choice(all_skills_pool)
        dmg_to_all = random.randint(20, lm_atk)
        log.append(f"🦞 **¡LANGOSTA MADRE** usa **{skill_used['name']}**! ¡{dmg_to_all} daño a todos!")

        bar_len = 20
        filled = int((lm_hp / lm_max) * bar_len)
        hp_bar = "🟥" * filled + "⬛" * (bar_len - filled)

        embed = discord.Embed(
            title="🦞 LANGOSTA MADRE",
            description=f"{hp_bar}\n❤️ **{lm_hp:,}/{lm_max:,} HP**\n\n" + "\n".join(log),
            color=0xe74c3c if lm_hp > lm_max * 0.5 else 0x95a5a6
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(3)

        if lm_hp <= 0:
            break

    # Resultado
    lobster_madre_active = False
    if lm_hp <= 0:
        db = load_db()
        rewards_text = []
        for uid, dmg in lobster_madre_state["participants"].items():
            user = get_user(db, uid)
            if user:
                coins_reward = 500 + (dmg // 10)
                user["coins"] = user.get("coins", 0) + coins_reward
                rewards_text.append(f"<@{uid}>: +{coins_reward}🪙 ({dmg} daño total)")
        save_db(db)
        embed = discord.Embed(
            title="🏆 ¡LANGOSTA MADRE DERROTADA!",
            description="¡Increíble! ¡Los guerreros lograron derrotar a la Langosta Madre!\n\n" + "\n".join(rewards_text[:10]),
            color=0x2ecc71
        )
    else:
        embed = discord.Embed(
            title="💀 La Langosta Madre sobrevivió...",
            description=f"¡La LANGOSTA MADRE sobrevivió con **{lm_hp:,} HP** restantes! ¡Mejor suerte la próxima vez!",
            color=0xe74c3c
        )
    await channel.send(embed=embed)

# ============================================================
#  SISTEMA DE LEVEL UP CON ELECCIÓN DE STAT (figuras)
# ============================================================
FIGURE_LEVEL_MAX = 50

def check_figure_levelup(fig_data, interaction_hook=None):
    """
    Verifica si una figura subió de nivel y devuelve (leveled_up, new_level).
    fig_data es el dict de la figura del usuario (con key, level, xp, stat_ups).
    """
    leveled = False
    while fig_data.get("level", 1) < FIGURE_LEVEL_MAX:
        needed = xp_to_level_up(fig_data.get("level", 1))
        if fig_data.get("xp", 0) >= needed:
            fig_data["xp"] -= needed
            fig_data["level"] = fig_data.get("level", 1) + 1
            if "pending_stat_up" not in fig_data:
                fig_data["pending_stat_up"] = 0
            fig_data["pending_stat_up"] = fig_data.get("pending_stat_up", 0) + 1
            leveled = True
        else:
            break
    return leveled

async def prompt_stat_up(interaction: discord.Interaction, fig_data: dict, fig_key: str, db):
    """Muestra un menú para elegir qué stat subir (+2) al subir de nivel."""
    pending = fig_data.get("pending_stat_up", 0)
    if pending <= 0:
        return
    fig_base = FIGURES.get(fig_key, {})
    fig_name = fig_base.get("name", fig_key)
    fig_emoji = fig_base.get("emoji", "🎭")
    lvl = fig_data.get("level", 1)

    embed = discord.Embed(
        title=f"⬆️ ¡{fig_emoji} {fig_name} subió al nivel {lvl}!",
        description="Elige **qué stat subir +2**:",
        color=0xf1c40f
    )
    view = discord.ui.View(timeout=60)
    stats = [("hp", "❤️ HP"), ("attack", "⚔️ ATK"), ("defense", "🛡️ DEF"), ("speed", "⚡ VEL")]
    user_id = interaction.user.id

    async def make_callback(stat_key, stat_label):
        async def callback(inter: discord.Interaction):
            if inter.user.id != user_id:
                await inter.response.send_message("❌ No es tu menú.", ephemeral=True)
                return
            db2 = load_db()
            u2 = get_user(db2, user_id)
            if not u2:
                await inter.response.send_message("❌ Error al cargar tu perfil.", ephemeral=True)
                return
            # Encontrar la figura correcta
            target = next((f for f in u2.get("figures", []) if f.get("key") == fig_key and f.get("pending_stat_up", 0) > 0), None)
            if not target:
                await inter.response.edit_message(content="✅ Ya fue procesado.", embed=None, view=None)
                return
            if "stat_ups" not in target:
                target["stat_ups"] = {}
            target["stat_ups"][stat_key] = target["stat_ups"].get(stat_key, 0) + 2
            target["pending_stat_up"] = target.get("pending_stat_up", 0) - 1
            save_db(db2)
            result_embed = discord.Embed(
                title=f"✅ {fig_emoji} {fig_name} — stat mejorado",
                description=f"**{stat_label} +2** permanente! (Nv.{target.get('level',1)})",
                color=0x2ecc71
            )
            await inter.response.edit_message(embed=result_embed, view=None)
            # Si quedan más pending, volver a preguntar
            if target.get("pending_stat_up", 0) > 0:
                await asyncio.sleep(1)
                await prompt_stat_up(inter, target, fig_key, db2)
        return callback

    for stat_key, stat_label in stats:
        btn = discord.ui.Button(label=stat_label, style=discord.ButtonStyle.primary)
        btn.callback = await make_callback(stat_key, stat_label)
        view.add_item(btn)

    try:
        if hasattr(interaction, 'followup'):
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.channel.send(embed=embed, view=view)
    except Exception:
        pass

# ============================================================
#  LEADERBOARDS EXPANDIDOS
# ============================================================
@bot.tree.command(name="leaderboard", description="Ver los rankings del servidor")
async def leaderboard_cmd(interaction: discord.Interaction):
    view = discord.ui.View(timeout=60)

    async def make_lb_callback(lb_type):
        async def callback(inter: discord.Interaction):
            db = load_db()
            users = list(db.get("users", {}).items())
            if not users:
                await inter.response.send_message("📭 Nadie registrado aún.", ephemeral=True)
                return
            medals = ["🥇", "🥈", "🥉"] + ["🔸"] * 17

            if lb_type == "wins":
                sorted_u = sorted(users, key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
                embed = discord.Embed(title="🏆 Top Victorias", color=0xf1c40f)
                for i, (uid, u) in enumerate(sorted_u):
                    total = u.get("wins", 0) + u.get("losses", 0)
                    wr = round(u["wins"] / total * 100, 1) if total > 0 else 0
                    embed.add_field(
                        name=f"{medals[i]} {u['name']}",
                        value=f"✅ {u.get('wins',0)}V ❌ {u.get('losses',0)}D | WR: **{wr}%**",
                        inline=False
                    )

            elif lb_type == "coins":
                sorted_u = sorted(users, key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
                embed = discord.Embed(title="💰 Top Riqueza", color=0xf1c40f)
                for i, (uid, u) in enumerate(sorted_u):
                    embed.add_field(
                        name=f"{medals[i]} {u['name']}",
                        value=f"💰 **{u.get('coins',0):,}** monedas",
                        inline=False
                    )

            elif lb_type == "figures":
                sorted_u = sorted(users, key=lambda x: len(x[1].get("figures", [])), reverse=True)[:10]
                embed = discord.Embed(title="🎭 Top Coleccionistas", color=0x9b59b6)
                for i, (uid, u) in enumerate(sorted_u):
                    unique = len({f["key"] for f in u.get("figures", [])})
                    embed.add_field(
                        name=f"{medals[i]} {u['name']}",
                        value=f"🎭 **{len(u.get('figures',[]))}** figuras ({unique} únicas)",
                        inline=False
                    )

            elif lb_type == "figlevels":
                def total_fig_levels(u):
                    return sum(f.get("level", 1) for f in u.get("figures", []))
                sorted_u = sorted(users, key=lambda x: total_fig_levels(x[1]), reverse=True)[:10]
                embed = discord.Embed(title="⬆️ Top Niveles de Figuras", color=0x2ecc71)
                for i, (uid, u) in enumerate(sorted_u):
                    total_lvl = total_fig_levels(u)
                    avg = round(total_lvl / max(1, len(u.get("figures", []))), 1)
                    embed.add_field(
                        name=f"{medals[i]} {u['name']}",
                        value=f"⬆️ Suma niveles: **{total_lvl}** | Promedio: **{avg}**",
                        inline=False
                    )

            await inter.response.edit_message(embed=embed, view=view)
        return callback

    btn_wins    = discord.ui.Button(label="🏆 Victorias",   style=discord.ButtonStyle.primary)
    btn_coins   = discord.ui.Button(label="💰 Riqueza",     style=discord.ButtonStyle.primary)
    btn_figs    = discord.ui.Button(label="🎭 Figuras",     style=discord.ButtonStyle.primary)
    btn_levels  = discord.ui.Button(label="⬆️ Niv. Figs",  style=discord.ButtonStyle.primary)

    btn_wins.callback   = await make_lb_callback("wins")
    btn_coins.callback  = await make_lb_callback("coins")
    btn_figs.callback   = await make_lb_callback("figures")
    btn_levels.callback = await make_lb_callback("figlevels")

    for btn in [btn_wins, btn_coins, btn_figs, btn_levels]:
        view.add_item(btn)

    db = load_db()
    users = list(db.get("users", {}).items())
    sorted_u = sorted(users, key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["🔸"] * 7
    embed = discord.Embed(title="🏆 Top Victorias", color=0xf1c40f)
    for i, (uid, u) in enumerate(sorted_u):
        total = u.get("wins", 0) + u.get("losses", 0)
        wr = round(u["wins"] / total * 100, 1) if total > 0 else 0
        embed.add_field(
            name=f"{medals[i]} {u['name']}",
            value=f"✅ {u.get('wins',0)}V ❌ {u.get('losses',0)}D | WR: **{wr}%**",
            inline=False
        )
    await interaction.response.send_message(embed=embed, view=view)

# ============================================================
#  PERFIL DE OTROS USUARIOS
# ============================================================
@bot.tree.command(name="verPerfil", description="Ver el perfil de otro usuario")
@app_commands.describe(usuario="El usuario cuyo perfil quieres ver")
async def ver_perfil(interaction: discord.Interaction, usuario: discord.Member):
    db = load_db()
    u = get_user(db, usuario.id)
    if not u:
        await interaction.response.send_message(f"❌ {usuario.display_name} no está registrado.", ephemeral=True)
        return
    total = u.get("wins", 0) + u.get("losses", 0)
    wr = round(u["wins"] / total * 100, 1) if total > 0 else 0
    lvl = u.get("level", 1)
    xp = u.get("xp", 0)
    needed = xp_to_level_up(lvl)
    embed = discord.Embed(title=f"👤 Perfil de {u['name']}", color=0x3498db)
    embed.add_field(name="🏆 Nivel", value=lvl, inline=True)
    embed.add_field(name="✨ XP", value=f"{xp}/{needed}", inline=True)
    embed.add_field(name="💰 Monedas", value=f"{u.get('coins',0):,}", inline=True)
    embed.add_field(name="✅ Victorias", value=u.get("wins", 0), inline=True)
    embed.add_field(name="❌ Derrotas", value=u.get("losses", 0), inline=True)
    embed.add_field(name="📊 Win Rate", value=f"{wr}%", inline=True)
    embed.add_field(name="🎭 Figuras", value=len(u.get("figures", [])), inline=True)
    team_keys = [u.get("figures", [])[i]["key"] if i < len(u.get("figures", [])) else None
                 for i in (u.get("team", [None, None, None]) or [None, None, None])]
    team_str = " | ".join(FIGURES[k]["emoji"] + " " + FIGURES[k]["name"] if k and k in FIGURES else "—" for k in team_keys)
    embed.add_field(name="⚔️ Equipo activo", value=team_str or "—", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="verFiguras", description="Ver las figuras de otro usuario")
@app_commands.describe(usuario="El usuario cuyas figuras quieres ver")
async def ver_figuras(interaction: discord.Interaction, usuario: discord.Member):
    db = load_db()
    u = get_user(db, usuario.id)
    if not u or not u.get("figures"):
        await interaction.response.send_message(f"❌ {usuario.display_name} no tiene figuras o no está registrado.", ephemeral=True)
        return
    embed = discord.Embed(title=f"🎭 Figuras de {u['name']}", color=0x9b59b6)
    seen = {}
    for fd in u["figures"]:
        k = fd.get("key")
        if k not in seen or fd.get("level", 1) > seen[k].get("level", 1):
            seen[k] = fd
    for k, fd in seen.items():
        fig = FIGURES.get(k)
        if not fig:
            continue
        lvl = fd.get("level", 1)
        xp = fd.get("xp", 0)
        stat_ups = fd.get("stat_ups", {})
        sup_str = " ".join(f"+{v}{s}" for s, v in stat_ups.items()) if stat_ups else ""
        embed.add_field(
            name=f"{fig['emoji']} {fig['name']} Nv.{lvl}",
            value=f"❤️{apply_level_bonus(fig['hp'],lvl)+stat_ups.get('hp',0)} ⚔️{apply_level_bonus(fig['attack'],lvl)+stat_ups.get('attack',0)} 🛡️{apply_level_bonus(fig['defense'],lvl)+stat_ups.get('defense',0)} ⚡{apply_level_bonus(fig['speed'],lvl)+stat_ups.get('speed',0)}\nXP: {xp}/{xp_to_level_up(lvl)} {sup_str}",
            inline=True
        )
    await interaction.response.send_message(embed=embed)

# ============================================================
#  SISTEMA DE MISIONES (/quest)
# ============================================================
QUESTS = {
    "documentos_jane": {
        "name": "📄 Documentos de Jane",
        "desc": "Jane Doe escondió sus documentos de identidad. Consigue 6 documentos ganando batallas para desbloquear la posibilidad de comprarla.",
        "goal": 6,
        "progress_key": "docs_collected",
        "reward_key": "jane_unlocked",
        "reward_desc": "🔓 ¡Jane Doe desbloqueada en la tienda!",
        "drop_chance": 60,  # % de chance de documento al ganar batalla
    },
}

def is_quest_unlocked(user: dict, quest_id: str) -> bool:
    return user.get("quests_completed", {}).get(quest_id, False)

def get_quest_progress(user: dict, quest_id: str) -> int:
    return user.get("quest_progress", {}).get(quest_id, 0)

async def check_quest_drops(user: dict, quest_id: str, channel):
    """Llamar tras ganar una batalla para ver si cae progreso de misión."""
    quest = QUESTS.get(quest_id)
    if not quest:
        return
    if is_quest_unlocked(user, quest_id):
        return
    active = user.get("active_quests", [])
    if quest_id not in active:
        return
    if random.randint(1, 100) <= quest["drop_chance"]:
        if "quest_progress" not in user:
            user["quest_progress"] = {}
        user["quest_progress"][quest_id] = user["quest_progress"].get(quest_id, 0) + 1
        prog = user["quest_progress"][quest_id]
        goal = quest["goal"]
        await channel.send(f"📄 **¡Documento encontrado!** ({prog}/{goal}) — Misión: {quest['name']}")
        if prog >= goal:
            if "quests_completed" not in user:
                user["quests_completed"] = {}
            user["quests_completed"][quest_id] = True
            await channel.send(f"🎉 **¡Misión completada!** {quest['name']}\n{quest['reward_desc']}")

@bot.tree.command(name="quest", description="Ver y activar misiones disponibles")
async def quest_cmd(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return

    embed = discord.Embed(title="📋 Misiones disponibles", color=0xe67e22)
    view = discord.ui.View(timeout=60)

    for qid, quest in QUESTS.items():
        completed = is_quest_unlocked(user, qid)
        active = qid in user.get("active_quests", [])
        prog = get_quest_progress(user, qid)
        goal = quest["goal"]

        if completed:
            status = f"✅ Completada"
        elif active:
            status = f"🔄 En progreso: {prog}/{goal}"
        else:
            status = "❌ Inactiva"

        embed.add_field(
            name=f"{quest['name']} — {status}",
            value=f"{quest['desc']}\n**Recompensa:** {quest['reward_desc']}",
            inline=False
        )

        if not completed and not active:
            btn = discord.ui.Button(label=f"Activar: {quest['name']}", style=discord.ButtonStyle.success)
            async def make_activate(quest_id):
                async def activate(inter: discord.Interaction):
                    if inter.user.id != interaction.user.id:
                        await inter.response.send_message("❌ No es tu menú.", ephemeral=True)
                        return
                    db2 = load_db()
                    u2 = get_user(db2, inter.user.id)
                    if "active_quests" not in u2:
                        u2["active_quests"] = []
                    if quest_id not in u2["active_quests"]:
                        u2["active_quests"].append(quest_id)
                    save_db(db2)
                    await inter.response.send_message(f"✅ ¡Misión **{QUESTS[quest_id]['name']}** activada! Gana batallas para progresar.", ephemeral=True)
                return activate
            btn.callback = await make_activate(qid)
            view.add_item(btn)

    await interaction.response.send_message(embed=embed, view=view)

# ============================================================
#  SISTEMA DE EXPLORACIÓN (/exploracion)
# ============================================================
EXPLORATION_DURATION = 30 * 60  # 30 minutos en segundos
EXPLORATION_REWARDS = [
    {"type": "coins",      "weight": 35, "min": 100, "max": 400},
    {"type": "ingredient", "weight": 30},
    {"type": "xp_fig",    "weight": 20, "value": 80},
    {"type": "recipe_sheet","weight": 10},
    {"type": "figure",     "weight": 5},
]

RECIPE_SHEETS = [
    {"name": "📜 Hoja: Langosta Picante",   "recipe_idx": 0},
    {"name": "📜 Hoja: Estofado de Langosta","recipe_idx": 1},
    {"name": "📜 Hoja: Langosta Gourmet",   "recipe_idx": 2},
    {"name": "📜 Hoja: Langosta con Queso", "recipe_idx": 3},
    {"name": "📜 Hoja: Langosta Dulce",     "recipe_idx": 4},
]

def pick_exploration_reward(user: dict) -> dict:
    """Elige una recompensa de exploración según los pesos."""
    total = sum(r["weight"] for r in EXPLORATION_REWARDS)
    roll = random.randint(1, total)
    acc = 0
    for reward in EXPLORATION_REWARDS:
        acc += reward["weight"]
        if roll <= acc:
            if reward["type"] == "coins":
                amount = random.randint(reward["min"], reward["max"])
                user["coins"] = user.get("coins", 0) + amount
                return {"type": "coins", "desc": f"💰 +{amount} monedas"}
            elif reward["type"] == "ingredient":
                non_lobster = [k for k in INGREDIENTS if k != "🦞"]
                ing = random.choice(non_lobster)
                if "ingredients" not in user:
                    user["ingredients"] = {}
                user["ingredients"][ing] = user["ingredients"].get(ing, 0) + 1
                return {"type": "ingredient", "desc": f"{ing} {INGREDIENTS.get(ing, 'Ingrediente')} x1"}
            elif reward["type"] == "xp_fig":
                return {"type": "xp_fig", "desc": f"✨ +{reward['value']} XP a tus figuras exploradoras"}
            elif reward["type"] == "recipe_sheet":
                sheet = random.choice(RECIPE_SHEETS)
                if "recipe_sheets" not in user:
                    user["recipe_sheets"] = []
                user["recipe_sheets"].append(sheet["recipe_idx"])
                return {"type": "recipe_sheet", "desc": f"📜 ¡Hoja de receta: {sheet['name']}!"}
            elif reward["type"] == "figure":
                buyable = [k for k, v in FIGURES.items() if v.get("price", 0) > 0 and k not in ("roblox_boss", "janedoe") or is_quest_unlocked(user, "documentos_jane")]
                if buyable:
                    fig_key = random.choice(buyable)
                    user["figures"].append({"key": fig_key, "level": 1, "xp": 0})
                    fig = FIGURES[fig_key]
                    return {"type": "figure", "desc": f"🎭 ¡Encontraste a **{fig['emoji']} {fig['name']}**!"}
                else:
                    user["coins"] = user.get("coins", 0) + 200
                    return {"type": "coins", "desc": "💰 +200 monedas (sin figuras disponibles)"}
    return {"type": "nothing", "desc": "Nada especial..."}

@bot.tree.command(name="exploracion", description="Manda 3 figuras a explorar (30 min) para conseguir recompensas")
async def exploracion_cmd(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return

    # Ver si ya hay exploración activa
    exp = user.get("exploration")
    now = time.time()
    if exp and now < exp.get("end_time", 0):
        remaining = int(exp["end_time"] - now)
        m, s = divmod(remaining, 60)
        fig_names = [FIGURES.get(k, {}).get("name", k) for k in exp.get("fig_keys", [])]
        embed = discord.Embed(
            title="🗺️ Exploración en curso",
            description=f"Tus figuras **{', '.join(fig_names)}** regresan en **{m}m {s}s**.",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Recoger resultados si ya terminó
    if exp and now >= exp.get("end_time", 0):
        rewards = []
        db2 = load_db()
        u2 = get_user(db2, interaction.user.id)
        for fig_key in exp.get("fig_keys", []):
            reward = pick_exploration_reward(u2)
            rewards.append(reward)
            # XP a las figuras exploradoras
            for fd in u2.get("figures", []):
                if fd.get("key") == fig_key:
                    fd["xp"] = fd.get("xp", 0) + 60
                    if check_figure_levelup(fd):
                        pass  # Se notificará al usuario al entrar al perfil
                    break
        u2["exploration"] = None
        save_db(db2)
        embed = discord.Embed(title="🎒 ¡Tu equipo regresó de la exploración!", color=0xf1c40f)
        for i, r in enumerate(rewards):
            fig_key = exp["fig_keys"][i] if i < len(exp["fig_keys"]) else "?"
            fig_name = FIGURES.get(fig_key, {}).get("name", fig_key)
            embed.add_field(name=f"🗺️ {fig_name} encontró:", value=r["desc"], inline=False)
        await interaction.response.send_message(embed=embed)
        return

    # Elegir figuras para explorar
    figs = user.get("figures", [])
    exploring_keys = [f["key"] for f in (user.get("exploration", {}) or {}).get("fig_keys", [])]
    team_indices = user.get("team", [])

    # Filtrar figuras disponibles (no en exploración activa)
    available_figs = []
    seen_keys = set()
    for i, fd in enumerate(figs):
        k = fd.get("key")
        if k and k not in seen_keys and k not in exploring_keys:
            seen_keys.add(k)
            available_figs.append((i, fd))

    if len(available_figs) < 1:
        await interaction.response.send_message("❌ No tienes figuras disponibles para explorar.", ephemeral=True)
        return

    options = []
    for idx, fd in available_figs[:25]:
        fig = FIGURES.get(fd["key"])
        if fig:
            raw_emoji = fig["emoji"]
            emoji_obj = discord.PartialEmoji.from_str(raw_emoji) if raw_emoji.startswith("<") else raw_emoji
            opt = discord.SelectOption(
                label=f"{fig['name']} Nv.{fd.get('level',1)}",
                value=fd["key"],
                description=f"{fig['rarity'].upper()} | HP:{fig['hp']} ATK:{fig['attack']}"
            )
            try:
                opt.emoji = emoji_obj
            except Exception:
                pass
            options.append(opt)

    state = {"selected": [], "user_id": interaction.user.id}

    async def show_exp_menu(inter, is_first=False):
        embed = discord.Embed(
            title="🗺️ Preparar Exploración",
            description=f"Elige hasta 3 figuras para explorar **(30 minutos)**.\nNo podrán batallar durante la exploración.\n\nSeleccionadas: **{', '.join(FIGURES.get(k,{}).get('name',k) for k in state['selected']) or 'Ninguna'}**",
            color=0x2ecc71
        )
        view = discord.ui.View(timeout=60)
        sel = discord.ui.Select(placeholder="Elige una figura...", options=options, max_values=1)

        async def add_fig(si: discord.Interaction):
            if si.user.id != state["user_id"]:
                await si.response.send_message("❌ No es tu menú.", ephemeral=True)
                return
            k = sel.values[0]
            if k in state["selected"]:
                await si.response.send_message("⚠️ Ya seleccionaste esa figura.", ephemeral=True)
                return
            if len(state["selected"]) >= 3:
                await si.response.send_message("❌ Máximo 3 figuras.", ephemeral=True)
                return
            state["selected"].append(k)
            new_embed = discord.Embed(
                title="🗺️ Preparar Exploración",
                description=f"Seleccionadas: **{', '.join(FIGURES.get(k2,{}).get('name',k2) for k2 in state['selected'])}**\n\nAñade más o pulsa **¡Explorar!**",
                color=0x2ecc71
            )
            await si.response.edit_message(embed=new_embed, view=build_exp_view(state))
        sel.callback = add_fig
        view.add_item(sel)

        start_btn = discord.ui.Button(
            label="🗺️ ¡Explorar!",
            style=discord.ButtonStyle.success,
            disabled=len(state["selected"]) == 0
        )
        async def start_exp(si: discord.Interaction):
            if si.user.id != state["user_id"]:
                await si.response.send_message("❌ No es tu menú.", ephemeral=True)
                return
            db2 = load_db()
            u2 = get_user(db2, si.user.id)
            end_time = time.time() + EXPLORATION_DURATION
            u2["exploration"] = {
                "fig_keys": state["selected"],
                "end_time": end_time,
                "started": time.time()
            }
            save_db(db2)
            names = [FIGURES.get(k, {}).get("name", k) for k in state["selected"]]
            conf_embed = discord.Embed(
                title="✅ ¡Exploración iniciada!",
                description=f"**{', '.join(names)}** salieron a explorar.\nRegresarán en **30 minutos**.\nUsa `/exploracion` de nuevo para recoger sus recompensas.",
                color=0x2ecc71
            )
            await si.response.edit_message(embed=conf_embed, view=None)
        start_btn.callback = start_exp
        view.add_item(start_btn)
        return embed, view

    def build_exp_view(st):
        """Reconstruye el view con los datos actuales."""
        v = discord.ui.View(timeout=60)
        sel2 = discord.ui.Select(placeholder="Añadir figura...", options=options, max_values=1)
        async def add2(si: discord.Interaction):
            if si.user.id != st["user_id"]: return
            k = sel2.values[0]
            if k not in st["selected"] and len(st["selected"]) < 3:
                st["selected"].append(k)
            new_embed = discord.Embed(
                title="🗺️ Preparar Exploración",
                description=f"Seleccionadas: **{', '.join(FIGURES.get(k2,{}).get('name',k2) for k2 in st['selected'])}**",
                color=0x2ecc71
            )
            await si.response.edit_message(embed=new_embed, view=build_exp_view(st))
        sel2.callback = add2
        v.add_item(sel2)
        sb = discord.ui.Button(label="🗺️ ¡Explorar!", style=discord.ButtonStyle.success)
        async def do_start(si: discord.Interaction):
            if si.user.id != st["user_id"]: return
            db2 = load_db()
            u2 = get_user(db2, si.user.id)
            u2["exploration"] = {"fig_keys": st["selected"], "end_time": time.time() + EXPLORATION_DURATION, "started": time.time()}
            save_db(db2)
            names = [FIGURES.get(k, {}).get("name", k) for k in st["selected"]]
            await si.response.edit_message(embed=discord.Embed(title="✅ ¡Exploración iniciada!", description=f"**{', '.join(names)}** salieron. Regresan en 30 min.", color=0x2ecc71), view=None)
        sb.callback = do_start
        v.add_item(sb)
        return v

    embed, view = await show_exp_menu(interaction, is_first=True)
    await interaction.response.send_message(embed=embed, view=view)

# ============================================================
#  SISTEMA MULTIPLAYER (/multiplayer) — hasta 4 jugadores
# ============================================================
active_multiplayer = {}  # channel_id -> MultiplayerSession

class MultiplayerSession:
    def __init__(self, host_id, host_name, channel_id):
        self.channel_id = channel_id
        self.host_id = host_id
        self.players = {host_id: {"name": host_name, "ready": False, "team": None, "figs_data": None}}
        self.max_players = 4
        self.started = False
        self.turn_order = []
        self.current_turn_idx = 0
        self.round_num = 1
        self.eliminated = set()
        self.log = []
        self.invert_event_active = False  # evento de inversión

@bot.tree.command(name="multiplayer", description="Crea una batalla multijugador (2-4 jugadores)")
async def multiplayer_cmd(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id in active_multiplayer:
        await interaction.response.send_message("❌ Ya hay una partida multijugador en este canal.", ephemeral=True)
        return
    if channel_id in active_battles:
        await interaction.response.send_message("❌ Ya hay una batalla activa. Usa `/reset` primero.", ephemeral=True)
        return
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return
    if not user.get("team") or not user.get("figures"):
        await interaction.response.send_message("❌ Equipa tus figuras con `/equipar` primero.", ephemeral=True)
        return

    session = MultiplayerSession(interaction.user.id, interaction.user.display_name, channel_id)
    active_multiplayer[channel_id] = session

    # Guardar equipo del host
    team_indices = user.get("team", [])
    host_team_keys = []
    host_figs_data = []
    for ti in team_indices:
        if ti is not None and ti < len(user["figures"]):
            fd = user["figures"][ti]
            host_team_keys.append(fd["key"])
            host_figs_data.append(fd)
    session.players[interaction.user.id]["team"] = host_team_keys
    session.players[interaction.user.id]["figs_data"] = host_figs_data
    session.players[interaction.user.id]["ready"] = True

    embed = discord.Embed(
        title="⚔️ Sala Multijugador creada",
        description=f"👑 **{interaction.user.display_name}** creó la sala.\n\n¡Únete con el botón de abajo! (máx. 4 jugadores)\nEl host puede iniciar cuando haya al menos 2.",
        color=0x9b59b6
    )
    embed.add_field(name="Jugadores", value=f"1. {interaction.user.display_name} ✅", inline=False)

    view = discord.ui.View(timeout=180)

    join_btn = discord.ui.Button(label="🎮 Unirme", style=discord.ButtonStyle.primary)
    start_btn = discord.ui.Button(label="⚔️ Iniciar batalla", style=discord.ButtonStyle.success)
    cancel_btn = discord.ui.Button(label="❌ Cancelar", style=discord.ButtonStyle.danger)

    async def join_callback(inter: discord.Interaction):
        sess = active_multiplayer.get(channel_id)
        if not sess or sess.started:
            await inter.response.send_message("❌ La sala ya no está disponible.", ephemeral=True)
            return
        if inter.user.id in sess.players:
            await inter.response.send_message("⚠️ Ya estás en la sala.", ephemeral=True)
            return
        if len(sess.players) >= sess.max_players:
            await inter.response.send_message("❌ La sala está llena.", ephemeral=True)
            return
        db2 = load_db()
        u2 = get_user(db2, inter.user.id)
        if not u2:
            await inter.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
            return
        if not u2.get("team") or not u2.get("figures"):
            await inter.response.send_message("❌ Equipa tus figuras con `/equipar` primero.", ephemeral=True)
            return
        team_idxs = u2.get("team", [])
        p_keys, p_figs = [], []
        for ti in team_idxs:
            if ti is not None and ti < len(u2["figures"]):
                fd = u2["figures"][ti]
                p_keys.append(fd["key"])
                p_figs.append(fd)
        sess.players[inter.user.id] = {"name": inter.user.display_name, "ready": True, "team": p_keys, "figs_data": p_figs}
        player_list = "\n".join(f"{i+1}. {p['name']} ✅" for i, p in enumerate(sess.players.values()))
        new_embed = discord.Embed(title="⚔️ Sala Multijugador", description=f"¡Únete! (máx. 4)", color=0x9b59b6)
        new_embed.add_field(name=f"Jugadores ({len(sess.players)}/4)", value=player_list, inline=False)
        await inter.response.edit_message(embed=new_embed, view=view)

    async def start_callback(inter: discord.Interaction):
        sess = active_multiplayer.get(channel_id)
        if not sess:
            await inter.response.send_message("❌ Sala no encontrada.", ephemeral=True)
            return
        if inter.user.id != sess.host_id:
            await inter.response.send_message("❌ Solo el host puede iniciar.", ephemeral=True)
            return
        if len(sess.players) < 2:
            await inter.response.send_message("❌ Se necesitan al menos 2 jugadores.", ephemeral=True)
            return
        sess.started = True
        # Construir equipos
        sess.turn_order = list(sess.players.keys())
        random.shuffle(sess.turn_order)
        # Crear figuras listas para batalla
        sess.fighters = {}
        for uid, pdata in sess.players.items():
            fighters = []
            for i, fkey in enumerate(pdata["team"]):
                fd = pdata["figs_data"][i] if i < len(pdata["figs_data"]) else {"level": 1}
                f = make_fighter(fkey, fd)
                f["owner_id"] = uid
                f["owner_name"] = pdata["name"]
                fighters.append(f)
            sess.fighters[uid] = fighters

        await inter.response.edit_message(
            embed=discord.Embed(title="⚔️ ¡Batalla iniciada!", description=f"Orden de turnos: {' → '.join(sess.players[uid]['name'] for uid in sess.turn_order)}", color=0xe74c3c),
            view=None
        )
        await run_multiplayer_battle(inter.channel, sess)

    async def cancel_callback(inter: discord.Interaction):
        sess = active_multiplayer.get(channel_id)
        if sess and inter.user.id == sess.host_id:
            del active_multiplayer[channel_id]
            await inter.response.edit_message(embed=discord.Embed(title="❌ Sala cancelada", color=0xe74c3c), view=None)
        else:
            await inter.response.send_message("❌ Solo el host puede cancelar.", ephemeral=True)

    join_btn.callback = join_callback
    start_btn.callback = start_callback
    cancel_btn.callback = cancel_callback
    view.add_item(join_btn)
    view.add_item(start_btn)
    view.add_item(cancel_btn)

    await interaction.response.send_message(embed=embed, view=view)

async def run_multiplayer_battle(channel, sess: MultiplayerSession):
    """Motor de batalla multijugador. Turnos en círculos, elige a quién atacar."""
    import asyncio

    def alive_players():
        return [uid for uid in sess.turn_order if uid not in sess.eliminated and any(f["hp"] > 0 for f in sess.fighters.get(uid, []))]

    def get_active_fighter(uid):
        for f in sess.fighters.get(uid, []):
            if f["hp"] > 0:
                return f
        return None

    async def send_status(msg=None):
        lines = []
        for uid in sess.turn_order:
            if uid in sess.eliminated:
                lines.append(f"💀 ~~{sess.players[uid]['name']}~~")
                continue
            figs = sess.fighters.get(uid, [])
            fig_parts = []
            for f in figs:
                hp_str = "💀" if f["hp"] <= 0 else f"{f['hp']}HP"
                fig_parts.append(f"{f['emoji']} {hp_str}")
            fig_str = " | ".join(fig_parts)
            lines.append(f"**{sess.players[uid]['name']}**: {fig_str}")
        embed = discord.Embed(
            title=f"⚔️ Multijugador — Ronda {sess.round_num}",
            description="\n".join(lines),
            color=0x9b59b6
        )
        if sess.invert_event_active:
            embed.add_field(name="🔀 EVENTO GLOBAL", value="¡Los ejes están invertidos! Los ataques curan al enemigo y las curaciones dañan!", inline=False)
        if sess.log:
            embed.add_field(name="📋 Último turno", value="\n".join(sess.log[-5:]), inline=False)
        if msg:
            await msg.edit(embed=embed)
            return msg
        else:
            return await channel.send(embed=embed)

    status_msg = await send_status()

    while len(alive_players()) > 1:
        # Evento global aleatorio (10% por ronda)
        if random.randint(1, 100) <= 10:
            sess.invert_event_active = not sess.invert_event_active
            event_msg = "🔀 **¡EVENTO GLOBAL!** ¡Los ejes se han invertido!" if sess.invert_event_active else "🔀 **¡EVENTO GLOBAL!** ¡Los ejes vuelven a la normalidad!"
            await channel.send(event_msg)

        for uid in list(sess.turn_order):
            alives = alive_players()
            if len(alives) <= 1:
                break
            if uid in sess.eliminated:
                continue
            if not any(f["hp"] > 0 for f in sess.fighters.get(uid, [])):
                sess.eliminated.add(uid)
                continue

            attacker_fig = get_active_fighter(uid)
            if not attacker_fig:
                continue

            # Construir opciones de ataque
            enemies = [eid for eid in alives if eid != uid]
            if not enemies:
                break

            # Pedir al jugador que elija target
            target_options = []
            for eid in enemies:
                ef = get_active_fighter(eid)
                if ef:
                    target_options.append(discord.SelectOption(
                        label=f"Atacar a {sess.players[eid]['name']}",
                        value=str(eid),
                        description=f"{ef['emoji']} {ef['name']} — {ef['hp']}HP"
                    ))

            # Construir skill options
            skills = FIGURE_SKILLS.get(attacker_fig.get("key", ""), [])
            skill_options = []
            for i, sk in enumerate(skills):
                cost = sk.get("cost", 0)
                skill_options.append(discord.SelectOption(
                    label=f"{sk['name']} ({cost}⚡)",
                    value=str(i),
                    description=sk.get("desc", "")[:50]
                ))

            turn_embed = discord.Embed(
                title=f"🎮 Turno de {sess.players[uid]['name']}",
                description=f"**{attacker_fig['emoji']} {attacker_fig['name']}** — {attacker_fig['hp']}HP | {attacker_fig.get('energy',0)}⚡\n\nElige objetivo y habilidad:",
                color=0x3498db
            )
            turn_view = discord.ui.View(timeout=30)
            turn_state = {"target_id": None, "skill_idx": None, "done": False}

            if target_options:
                target_sel = discord.ui.Select(placeholder="🎯 Elegir objetivo...", options=target_options)
                async def target_cb(inter: discord.Interaction):
                    if inter.user.id != uid:
                        await inter.response.send_message("❌ No es tu turno.", ephemeral=True)
                        return
                    turn_state["target_id"] = int(inter.user.id if inter.data["values"][0] == str(uid) else inter.data["values"][0])
                    # Usar el valor seleccionado directamente
                    turn_state["target_id"] = int(inter.data["values"][0])
                    await inter.response.defer()
                target_sel.callback = target_cb
                turn_view.add_item(target_sel)

            if skill_options:
                skill_sel = discord.ui.Select(placeholder="✨ Elegir habilidad...", options=skill_options[:25])
                async def skill_cb(inter: discord.Interaction):
                    if inter.user.id != uid:
                        await inter.response.send_message("❌ No es tu turno.", ephemeral=True)
                        return
                    turn_state["skill_idx"] = int(inter.data["values"][0])
                    await inter.response.defer()
                skill_sel.callback = skill_cb
                turn_view.add_item(skill_sel)

            confirm_btn = discord.ui.Button(label="✅ Confirmar", style=discord.ButtonStyle.success)
            async def confirm_cb(inter: discord.Interaction):
                if inter.user.id != uid:
                    await inter.response.send_message("❌ No es tu turno.", ephemeral=True)
                    return
                if turn_state["target_id"] is None:
                    await inter.response.send_message("❌ Elige un objetivo primero.", ephemeral=True)
                    return
                turn_state["done"] = True
                await inter.response.defer()
            confirm_btn.callback = confirm_cb
            turn_view.add_item(confirm_btn)

            # Auto-confirm timer: si no actúa en 30s, ataque automático
            skip_btn = discord.ui.Button(label="⏩ Saltar (auto)", style=discord.ButtonStyle.secondary)
            async def skip_cb(inter: discord.Interaction):
                turn_state["done"] = True
                turn_state["target_id"] = int(enemies[0]) if enemies else None
                turn_state["skill_idx"] = 0
                await inter.response.defer()
            skip_btn.callback = skip_cb
            turn_view.add_item(skip_btn)

            turn_msg = await channel.send(f"<@{uid}>", embed=turn_embed, view=turn_view)

            # Esperar hasta 30 segundos
            for _ in range(30):
                if turn_state["done"]:
                    break
                await asyncio.sleep(1)

            # Auto-acción si no respondió
            if not turn_state["done"] or turn_state["target_id"] is None:
                turn_state["target_id"] = int(enemies[0]) if enemies else None
                turn_state["skill_idx"] = 0

            # Ejecutar ataque
            target_uid = turn_state["target_id"]
            defender_fig = get_active_fighter(target_uid)
            sess.log = []

            if defender_fig and attacker_fig:
                skill_idx = turn_state["skill_idx"] if turn_state["skill_idx"] is not None else 0
                skills_list = FIGURE_SKILLS.get(attacker_fig.get("key", ""), [])
                skill = skills_list[skill_idx] if skill_idx is not None and skill_idx < len(skills_list) else None

                if skill:
                    power = skill.get("power", 50)
                    dmg = max(1, int(attacker_fig["atk"] * (power / 100)) + random.randint(-3, 8) - (defender_fig["defense"] // 4))
                    if sess.invert_event_active:
                        # Invertido: el daño cura al defensor
                        defender_fig["hp"] = min(defender_fig["max_hp"], defender_fig["hp"] + dmg)
                        sess.log.append(f"🔀 **{sess.players[uid]['name']}** usa **{skill['name']}** en {sess.players[target_uid]['name']} → ¡**CURA {dmg}HP**! (invertido)")
                    else:
                        defender_fig["hp"] = max(0, defender_fig["hp"] - dmg)
                        sess.log.append(f"⚔️ **{sess.players[uid]['name']}** usa **{skill['name']}** en {sess.players[target_uid]['name']} → **{dmg} daño**")
                    if defender_fig["hp"] <= 0:
                        sess.log.append(f"💀 {defender_fig['emoji']} {defender_fig['name']} cayó!")
                else:
                    dmg = random.randint(10, 30)
                    defender_fig["hp"] = max(0, defender_fig["hp"] - dmg)
                    sess.log.append(f"⚔️ **{sess.players[uid]['name']}** ataca a {sess.players[target_uid]['name']} → **{dmg} daño**")

            # Verificar si el target fue eliminado
            if not any(f["hp"] > 0 for f in sess.fighters.get(target_uid, [])):
                sess.eliminated.add(target_uid)
                sess.log.append(f"💀 **{sess.players[target_uid]['name']}** fue eliminado!")

            try:
                await turn_msg.delete()
            except Exception:
                pass

            status_msg = await send_status(status_msg)

        sess.round_num += 1

        # Regenerar energía
        for uid, figs in sess.fighters.items():
            for f in figs:
                if f["hp"] > 0:
                    f["energy"] = min(100, f.get("energy", 0) + 20)

    # Fin de batalla
    winner_ids = alive_players()
    if channel_id in active_multiplayer:
        del active_multiplayer[channel_id]

    if winner_ids:
        wid = winner_ids[0]
        wname = sess.players[wid]["name"]
        db = load_db()
        wu = get_user(db, wid)
        if wu:
            wu["wins"] = wu.get("wins", 0) + 1
            wu["coins"] = wu.get("coins", 0) + COINS_WIN * (len(sess.players) - 1)
            wu["xp"] = wu.get("xp", 0) + XP_PER_WIN
            while wu["xp"] >= xp_to_level_up(wu["level"]):
                wu["xp"] -= xp_to_level_up(wu["level"])
                wu["level"] += 1
        for uid in sess.eliminated:
            lu = get_user(db, uid)
            if lu:
                lu["losses"] = lu.get("losses", 0) + 1
                lu["coins"] = lu.get("coins", 0) + COINS_LOSS
        save_db(db)
        final_embed = discord.Embed(
            title=f"🏆 ¡{wname} ganó el Multijugador!",
            description=f"¡**{wname}** es el último en pie!\n+{COINS_WIN * (len(sess.players)-1)}🪙 | +{XP_PER_WIN}XP",
            color=0xf1c40f
        )
    else:
        final_embed = discord.Embed(title="🤝 Empate multijugador", description="¡Nadie sobrevivió!", color=0x95a5a6)
    await channel.send(embed=final_embed)

# ============================================================
#  TIENDA: Jane Doe requiere quest completada
# ============================================================
# Parchear show_shop_page para bloquear janedoe sin quest
_original_tienda = tienda.callback if hasattr(tienda, 'callback') else None

# ============================================================
#  HOOK: Notificar level up de figuras post-batalla
# ============================================================
# Se integra en el finish_battle existente — aquí añadimos el check post-guardar
async def notify_pending_stat_ups(interaction_or_channel, user_data: dict, db):
    """Notifica al usuario si alguna figura tiene pending_stat_up."""
    for fd in user_data.get("figures", []):
        if fd.get("pending_stat_up", 0) > 0:
            fig = FIGURES.get(fd.get("key", ""), {})
            fig_name = fig.get("name", fd.get("key", "?"))
            fig_emoji = fig.get("emoji", "🎭")
            lvl = fd.get("level", 1)
            embed = discord.Embed(
                title=f"⬆️ ¡{fig_emoji} {fig_name} subió al nivel {lvl}!",
                description="Elige qué stat subir **+2** con `/subirstat`.",
                color=0xf1c40f
            )
            try:
                if hasattr(interaction_or_channel, "followup"):
                    await interaction_or_channel.followup.send(embed=embed)
                else:
                    await interaction_or_channel.send(embed=embed)
            except Exception:
                pass
            break  # Notificar solo una a la vez

@bot.tree.command(name="subirstat", description="Elige qué stat subir en tus figuras con nivel pendiente")
async def subir_stat_cmd(interaction: discord.Interaction):
    db = load_db()
    user = get_user(db, interaction.user.id)
    if not user:
        await interaction.response.send_message("❌ Usa `/registrar` primero.", ephemeral=True)
        return

    # Buscar figuras con pending
    pending_figs = [(i, fd) for i, fd in enumerate(user.get("figures", [])) if fd.get("pending_stat_up", 0) > 0]
    if not pending_figs:
        await interaction.response.send_message("✅ No hay figuras esperando subir stat.", ephemeral=True)
        return

    idx, fd = pending_figs[0]
    fig = FIGURES.get(fd["key"], {})
    fig_name = fig.get("name", fd["key"])
    fig_emoji = fig.get("emoji", "🎭")
    lvl = fd.get("level", 1)

    embed = discord.Embed(
        title=f"⬆️ {fig_emoji} {fig_name} — Nv.{lvl}",
        description=f"Tienes **{fd['pending_stat_up']}** punto(s) de stat pendiente.\n¿Qué stat quieres subir **+2**?",
        color=0xf1c40f
    )
    view = discord.ui.View(timeout=60)
    stats = [("hp", "❤️ HP +2"), ("attack", "⚔️ ATK +2"), ("defense", "🛡️ DEF +2"), ("speed", "⚡ VEL +2")]

    for stat_key, label in stats:
        btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
        async def make_cb(sk, sl, fig_idx):
            async def cb(inter: discord.Interaction):
                if inter.user.id != interaction.user.id:
                    await inter.response.send_message("❌ No es tu menú.", ephemeral=True)
                    return
                db2 = load_db()
                u2 = get_user(db2, inter.user.id)
                target_fd = u2["figures"][fig_idx]
                if "stat_ups" not in target_fd:
                    target_fd["stat_ups"] = {}
                target_fd["stat_ups"][sk] = target_fd["stat_ups"].get(sk, 0) + 2
                target_fd["pending_stat_up"] = max(0, target_fd.get("pending_stat_up", 0) - 1)
                save_db(db2)
                result = discord.Embed(
                    title=f"✅ ¡{FIGURES.get(target_fd['key'],{}).get('emoji','🎭')} {FIGURES.get(target_fd['key'],{}).get('name',target_fd['key'])} mejorado!",
                    description=f"**{sl}** permanente aplicado. (Nv.{target_fd.get('level',1)})",
                    color=0x2ecc71
                )
                await inter.response.edit_message(embed=result, view=None)
                # Verificar si quedan más pending
                if target_fd.get("pending_stat_up", 0) > 0:
                    await asyncio.sleep(1)
                    await subir_stat_cmd.callback(inter)
            return cb
        btn.callback = await make_cb(stat_key, label, idx)
        view.add_item(btn)

    await interaction.response.send_message(embed=embed, view=view)

# ============================================================
#  ACTUALIZAR /tienda PARA BLOQUEAR JANEDOE SIN QUEST
# ============================================================
# Se inserta en show_shop_page como filtro adicional
_base_show_shop_page = show_shop_page

async def show_shop_page_with_quest_filter(interaction, available, user, page, db):
    """Wrapper que filtra janedoe si el usuario no completó la quest."""
    filtered = {
        k: v for k, v in available.items()
        if k != "janedoe" or is_quest_unlocked(user, "documentos_jane")
    }
    await _base_show_shop_page(interaction, filtered, user, page, db)

show_shop_page = show_shop_page_with_quest_filter

# ============================================================
#  HOOK EN FINISH_BATTLE PARA QUEST Y LEVEL UP DE FIGURAS
# ============================================================
# Parchar check_figure_levelup en el finish_battle
_base_check_figure_levelup = check_figure_levelup



# ============================================================
#  ARRANQUE
# ============================================================
bot.run(TOKEN)

