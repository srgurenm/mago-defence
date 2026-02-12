import pygame
import os
import sys

# --- FUNCIÓN DE RUTAS UNIVERSAL ---
def resolver_ruta(ruta_relativa):
    if sys.platform == 'emscripten':
        return ruta_relativa.replace("\\", "/")
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa).replace("\\", "/")

# --- CONFIGURACIÓN DE PANTALLA ---
ANCHO = 800
ALTO = 600
FPS = 60
VERSION = "1.0.1"
VOLUMEN_MUSICA_DEFAULT = 0.15
VOLUMEN_SFX_DEFAULT = 0.20

# --- ESTADOS DEL JUEGO ---
ESTADO_MENU = 0
ESTADO_JUGANDO = 1
ESTADO_PAUSA = 2
ESTADO_GAMEOVER = 3
ESTADO_TRANSICION = 4 
ESTADO_SELECCION_MEJORA = 5 
ESTADO_SELECCION_PERSONAJE = 6 
ESTADO_TIENDA = 7 
ESTADO_SELECCION_RECOMPENSA_BOSS = 8
ESTADO_DEBUG_MENU = 9
ESTADO_VICTORIA_FINAL = 10
ESTADO_CONFIG_AUDIO = 11

# --- MODOS DE DIFICULTAD ---
MODO_NORMAL = 0
MODO_DIFICIL = 1

# --- COLORES ---
NEGRO = (10, 10, 20)
BLANCO = (255, 255, 255)
AZUL_MAGO = (100, 100, 255)
CIAN_MAGIA = (0, 255, 255)
NARANJA_FUEGO = (255, 100, 0)
ROJO_VIDA = (255, 50, 50)
VERDE_BARRERA = (50, 255, 50)
MORADO_OSCURO = (138, 43, 226)
MORADO_CARGADO = (75, 0, 130)
ORO_PODER = (255, 215, 0)
COLOR_CORAZON = (255, 0, 127)
GRIS_TARJETA = (50, 50, 60)
BORDE_TARJETA = (100, 100, 120)
AZUL_RAYO = (200, 230, 255) 
ORO_PROYECTIL = (255, 255, 100) 
VERDE_VENENO = (100, 255, 100) 
ROJO_SANGRE = (200, 0, 0)      
BLANCO_HIELO = (200, 255, 255) 
MAGENTA_ARCO = (255, 100, 255)
VERDE_CAZADOR = (50, 180, 50)
GRIS_ELITE = (180, 180, 190)
ROJO_ORBITAL = (255, 80, 80)
AZUL_HOMING = (80, 150, 255)
AZUL_CONGELADO = (100, 255, 255)
COLOR_BARRERA_LLENA = (50, 255, 50)
COLOR_BARRERA_MEDIA = (200, 200, 50)
COLOR_BARRERA_BAJA = (255, 50, 50)
COLOR_HUD_BG = (10, 10, 30, 200)

# --- COLORES UI ---
ROJO_BORRAR = (200, 40, 40)
ROJO_BORRAR_HOVER = (255, 0, 0)
VERDE_JUGAR = (40, 180, 40)
GRIS_DESACTIVADO = (80, 80, 80)
GRIS_BOTON = (60, 60, 70)
AMARILLO_SELECCION = (255, 215, 0)
VERDE_XP = (150, 255, 100)
AMARILLO_DORADO = (255, 215, 0)
VERDE_FLUOR = (150, 255, 50)

# --- COLORES AMBIENTALES ---
COLOR_LUCIERNAGA = (200, 255, 150)     
COLOR_MOTA_MAGICA = (100, 200, 255)    
COLOR_NIEBLA_BRUMA = (200, 220, 230)   

# --- BALANCEO ROGUELIKE ---
XP_POR_ENEMIGO = 1
XP_BASE_REQUERIDA = 15
XP_FACTOR_ESCALADO = 1.50 

ESCALADO_CADENCIA_POR_NIVEL = 0.99 
VELOCIDAD_DASH = 18
DURACION_DASH = 150 

CADENCIA_BASE = 500

# --- CONFIGURACIÓN DE BALANCEO POR PERSONAJE ---

CONFIG_PERSONAJES = {
    "MAGO": {
        # STATS BASE
        "vida_inicial": 3,
        "vida_maxima": 3,
        "danio_base": 10,
        "danio_multi": 1.0,
        "danio_escalado_por_nivel": 0.8,
        
        # ATAQUE
        "cadencia_base_ms": 450,
        "cadencia_escalado": 0.98,
        "velocidad_proyectil": 9.0,
        "proyectiles_extra": 0,
        "dispersion_angulo": 10,
        
        # MOVIMIENTO
        "velocidad_movimiento": 5.0,
        "dash_velocidad": 18,
        "dash_duracion_ms": 150,
        "dash_cooldown_ms": 1200,
        
        # CRÍTICO
        "chance_critico": 0.05,
        "danio_critico": 1.5,
        
        # ESPECIAL
        "habilidad_especial": None,
        "modificadores_iniciales": [],
        
        # DESCRIPCIÓN
        "nombre": "MAGO",
        "desc": "Equilibrado.",
        "detalle": "Ideal para empezar.",
        "color": AZUL_MAGO,
        "sprite": "assets/mago.png",
        "sprite_disparo": "assets/mago_disparo.png",
        "sprite_frente": "assets/mago_frente.png"
    },
    
    "piromante": {
        # STATS BASE
        "vida_inicial": 3,
        "vida_maxima": 4,
        "danio_base": 15,
        "danio_multi": 1.5,
        "danio_escalado_por_nivel": 0.6,
        
        # ATAQUE
        "cadencia_base_ms": 1200,
        "cadencia_escalado": 0.90,
        "velocidad_proyectil": 5.0,
        "proyectiles_extra": 0,
        "dispersion_angulo": 35,
        
        # MOVIMIENTO
        "velocidad_movimiento": 4.5,
        "dash_velocidad": 15,
        "dash_duracion_ms": 150,
        "dash_cooldown_ms": 1500,
        
        # CRÍTICO
        "chance_critico": 0.05,
        "danio_critico": 1.5,
        
        # ESPECIAL - Quemadura explosiva
        "habilidad_especial": "explosion_quemadura",
        "explosion_danio": 0.7,
        "explosion_radio": 70,
        "modificadores_iniciales": ["explosivo"],
        
        # DESCRIPCIÓN
        "nombre": "PIROMANTE",
        "desc": "Daño explosivo.",
        "detalle": "Lento pero letal.",
        "color": NARANJA_FUEGO,
        "sprite": "assets/mago_piromante.png",
        "sprite_disparo": "assets/mago_piromante_disparo.png",
        "sprite_frente": "assets/piromante_frente.png"
    },
    
    "cazador": {
        # STATS BASE
        "vida_inicial": 3,
        "vida_maxima": 3,
        "danio_base": 5,
        "danio_multi": 0.5,
        "danio_escalado_por_nivel": 0.5,
        
        # ATAQUE
        "cadencia_base_ms": 750,
        "cadencia_escalado": 0.94,
        "velocidad_proyectil": 12.0,
        "proyectiles_extra": 1,
        "dispersion_angulo": 8,
        
        # MOVIMIENTO
        "velocidad_movimiento": 7.5,
        "dash_velocidad": 20,
        "dash_duracion_ms": 150,
        "dash_cooldown_ms": 1000,
        
        # CRÍTICO 
        "chance_critico": 0.15,
        "danio_critico": 2.0,
        
        # ESPECIAL
        "habilidad_especial": None,
        "modificadores_iniciales": [],
        
        # DESCRIPCIÓN
        "nombre": "CAZADOR",
        "desc": "Doble disparo.",
        "detalle": "Rápido y preciso.",
        "color": VERDE_CAZADOR,
        "sprite": "assets/mago_cazador.png",
        "sprite_disparo": "assets/mago_cazador_disparo.png",
        "sprite_frente": "assets/cazador_frente.png"
    },
    
    "el_loco": {
        # STATS BASE
        "vida_inicial": 2,
        "vida_maxima": 2,
        "danio_base": 1.0,
        "danio_multi": 0.1,
        "danio_escalado_por_nivel": 0.05,
        
        # ATAQUE - Cadencia extrema
        "cadencia_base_ms": 150,
        "cadencia_escalado": 0.99,
        "velocidad_proyectil": 5.0,
        "proyectiles_extra": 0,
        "dispersion_angulo": 20,
        
        # MOVIMIENTO
        "velocidad_movimiento": 7.0,
        "dash_velocidad": 22,
        "dash_duracion_ms": 150,
        "dash_cooldown_ms": 800,
        
        # CRÍTICO
        "chance_critico": 0.03,
        "danio_critico": 1.25,
        
        # ESPECIAL
        "habilidad_especial": None,
        "modificadores_iniciales": [],
        
        # DESCRIPCIÓN
        "nombre": "EL LOCO",
        "desc": "Cadencia extrema.",
        "detalle": "Muchos disparos débiles.",
        "color": (200, 255, 0),
        "sprite": "assets/mago_loco.png",
        "sprite_disparo": "assets/mago_loco_disparo.png",
        "sprite_frente": "assets/mago_loco_frente.png"
    },
    
    "snake": {
        # STATS BASE
        "vida_inicial": 2,
        "vida_maxima": 2,
        "danio_base": 0.05,
        "danio_multi": 1.0,
        "danio_escalado_por_nivel": 0.05,
        
        # ATAQUE - Sistema de carga (disparo único)
        "cadencia_base_ms": 80,
        "cadencia_escalado": 0.98,
        "velocidad_proyectil": 2.0,
        "proyectiles_extra": 0,
        "dispersion_angulo": 0,
        
        # SISTEMA DE CARGA
        "tiempo_carga_max_ms": 1000,
        "danio_carga_max": 0.15,
        "danio_carga_minimo": 0.02,
        "velocidad_carga_multi": 1.0,
        "velocidad_carga": 2.8,  
        
        # MOVIMIENTO
        "velocidad_movimiento": 4.0,
        "dash_velocidad": 18,
        "dash_duracion_ms": 150,
        "dash_cooldown_ms": 1200,
        
        # CRÍTICO
        "chance_critico": 0.01,
        "danio_critico": 1.25,
        
        # ESPECIAL
        "habilidad_especial": None,
        "modificadores_iniciales": [],
        
        # DESCRIPCIÓN
        "nombre": "SNAKE",
        "desc": "Rayo cargado.",
        "detalle": "Disparo lento que atraviesa todo.",
        "color": (255, 0, 150),
        "sprite": "assets/mago_snake.png",
        "sprite_disparo": "assets/mago_snake_disparo.png",
        "sprite_frente": "assets/mago_snake_frente.png"
    }
}

#
DATOS_PERSONAJES = {
    key: {
        "nombre": value["nombre"],
        "desc": value["desc"],
        "detalle": value["detalle"],
        "color": value["color"],
        "sprite": value["sprite"],
        "sprite_disparo": value["sprite_disparo"],
        "sprite_frente": value.get("sprite_frente", value["sprite"]),
        "stats_base": {
            "danio_multi": value["danio_multi"],
            "velocidad_ataque_multi": CADENCIA_BASE / value["cadencia_base_ms"],
            "proyectiles_extra": value["proyectiles_extra"],
            "velocidad_movimiento": value["velocidad_movimiento"],
            "modificadores": value["modificadores_iniciales"]
        }
    }
    for key, value in CONFIG_PERSONAJES.items()
}

# --- PALETAS DE BIOMAS ---
BIOMAS = {
    0: {"cesped": (20, 35, 20), "var1": (25, 45, 25), "var2": (15, 30, 15), "arbol_fondo": (5, 20, 5), "arbol_frente": (10, 40, 10)}, 
    1: {"cesped": (194, 178, 128), "var1": (210, 180, 140), "var2": (180, 160, 110), "arbol_fondo": (139, 69, 19), "arbol_frente": (160, 82, 45)}, 
    2: {"cesped": (200, 200, 220), "var1": (220, 220, 240), "var2": (180, 180, 200), "arbol_fondo": (50, 50, 80), "arbol_frente": (70, 70, 100)} 
}
MARRON_TIERRA_BASE = (50, 35, 20); MARRON_TIERRA_PIEDRA = (65, 45, 30); MARRON_TIERRA_OSCURO = (40, 25, 15)
GRIS_PIEDRA_BASE = (60, 60, 65); GRIS_PIEDRA_CLARO = (80, 80, 85)
MARRON_MADERA = (100, 50, 20); MARRON_MADERA_OSCURO = (70, 35, 10)

# --- TAMAÑOS ---
MAGO_ANCHO = 24
MAGO_ALTO = 24

# --- BALANCEO ---
VELOCIDAD_MAGO = 6
DANIO_BASE_MAGO = 10
VIDAS_INICIALES_MAGO = 3
MAX_VIDAS_BASE = 3 

# --- META-PROGRESIÓN ---
FACTOR_COSTO_TIENDA = 1.6 
PRECIOS_TIENDA = {
    "vida_base": {"base": 150, "max": 3, "nombre": "VIDA"},
    "danio_base": {"base": 100, "max": 10, "nombre": "Daño"},
    "critico": {"base": 200, "max": 10, "nombre": "%Critico"},
}

# --- PROGRESIÓN IN-GAME ---
MEJORA_VELOCIDAD_ATAQUE_POR_NIVEL = 0.99 
MEJORA_DANIO_PERMANENTE = 0.5           
MEJORA_VIDA_MAXIMA = 1                  

# --- ENEMIGOS ---
TIPO_ENEMIGO_NORMAL = 0
TIPO_ENEMIGO_RAPIDO = 1 
TIPO_ENEMIGO_TANQUE = 2 
TIPO_ENEMIGO_TESORO = 3 
TIPO_ENEMIGO_ELITE = 4 

COLOR_BORDE_TANQUE = (100, 100, 100)
COLOR_BORDE_ELITE = (255, 215, 0)
COLOR_BORDE_TESORO = (255, 255, 0)
COLOR_GLOW_ENEMIGO = (200, 0, 255)
COLOR_PROYECTIL_ENEMIGO = (150, 0, 255)
COLOR_ESCUDO_PENDIENTE = (0, 200, 255)
COLOR_ESCUDO_ACTIVO = (255, 120, 0, 95)
FACTOR_RALENTIZADO = 0.5
DURACION_RALENTIZADO = 3000
DURACION_CHARCO = 5000
TICK_CHARCO_VENENO = 1000

# Escalado de vida 
PUNTOS_POR_FILA = {0: 10, 1: 30, 2: 60, 3: 150}
HP_POR_FILA = {0: 15, 1: 30, 2: 45, 3: 55} 
MULT_VIDA_POR_NIVEL = 0.15 # 10% de vida extra por nivel 

COLORES_POR_FILA = {0: (50, 200, 50), 1: (200, 200, 50), 2: (200, 100, 50), 3: (200, 50, 50)}

CHANCE_DISPARO_BASE = 0.0004 
CHANCE_DISPARO_INCREMENTO = 0.00002 
CHANCE_DISPARO_POR_TIPO = {
    TIPO_ENEMIGO_NORMAL: 1.0,
    TIPO_ENEMIGO_RAPIDO: 2.9,
    TIPO_ENEMIGO_TANQUE: 0.5,
    TIPO_ENEMIGO_ELITE: 2.9,
    TIPO_ENEMIGO_TESORO: 9.5
}
VEL_MONSTRUO_BASE_X = 0.2 
DISTANCIA_DESCENSO_BASE = 4
FILAS_MONSTRUOS = 4
COLUMNAS_MONSTRUOS = 10
INCREMENTO_VEL_X_POR_NIVEL = 0.2
INCREMENTO_DESCENSO_CADA_5 = 2
MULT_VEL_DIFICIL = 1.9
MULT_DISPARO_DIFICIL = 2.9

# --- BOSSES ---
FRECUENCIA_BOSS = 5 
HP_BOSS_BASE = 700 
VEL_BOSS_X_MAX = 4.0
VEL_BOSS_Y_MAX = 2.0
LIMITE_INFERIOR_BOSS = 300 
BOSS_VEL_MULT_DIFICIL = 1.9

BOSS_CD_ARCO = 2000
BOSS_CD_RAFAGA = 5500
BOSS_CD_ATAQUE_CARGADO = 8000 
BOSS_TIEMPO_TELEGRAFO = 1500

BOSS_TIPO_NORMAL = 0
BOSS_TIPO_HIELO = 1
BOSS_TIPO_TOXICO = 2
BOSS_TIPO_FUEGO = 3
BOSS_TIPO_SNAKE = 4

HP_BOSS_SNAKE = 4200
BOSS_FUEGO_COLOR = (255, 69, 0)
PATH_BOSS_ATAQUE = "assets/boss_ataque.png"
PATH_BOSS_MUERTE = "assets/boss_muerte.png"

# --- EFECTOS DE ESTADO ---
DURACION_CONGELACION_NORMAL = 2200
DURACION_CONGELACION_BOSS = 660

# --- POWER-UPS ---
PROB_CORAZON = 0.0008 
CANTIDAD_GRUPOS_BARRERAS = 3
BARRERA_VIDA_MAX = 10      
BARRERA_ANCHO = 40         
BARRERA_ALTO = 9
PROB_POWERUP_CIELO = 0.0001 
PROB_POWERUP_BASE = 0.12 
PROB_POWERUP_ENDGAME = 0.30
PROB_POWERUP_RAYO = 0.02

TIEMPO_SIN_POWERUP_MS_BONUS = 15000
BONUS_PROB_POR_SEGUNDO = 0.004
BONUS_PROB_MAXIMO = 0.20
BONUS_PROB_BOSS = 2.0
INTERVALO_MINIMO_POWERUPS = 800

COLORES_PU = {
    "cadencia": (0, 255, 255), "arco": (255, 0, 255), "disparo_doble": (0, 255, 0),
    "disparo_triple": (255, 200, 0), "explosivo": (255, 165, 0), "escudo": (255, 50, 50), "doble_danio": ORO_PODER,
    "rayo": AZUL_RAYO,
    "orbital": ROJO_ORBITAL, "homing": AZUL_HOMING
}
POWERUPS_STATS = {
    "cadencia": {"duracion": 8000}, "arco": {"cargas": 5}, "disparo_doble": {"cargas": 8},
    "disparo_triple": {"cargas": 4}, "explosivo": {"cargas": 3}, "escudo": {"duracion": 9500},
    "doble_danio": {"duracion": 9500},
    "rayo": {"cargas": 2},
    "orbital": {"duracion": 11000},
    "homing": {"cargas": 15}
}

UNLOCK_REQ_ORBITAL = 1
UNLOCK_REQ_HOMING = 3

PATH_MUSIC = "assets/musica_fondo.mp3"
PATH_SND_DISPARO = "assets/disparo.wav"
PATH_SND_MUERTE = "assets/muerte.wav"
PATH_SND_POWERUP = "assets/powerup.wav"
PATH_SND_NIVEL = "assets/nivel_up.wav"
PATH_BOSS_SPRITE = "assets/boss.png"
ALPHA_BOTONES = 110

# --- MODO DEBUG ---
DEBUG_MODE = False  # DESACTIVADO por defecto - activar desde el menú F12
DEBUG_NIVEL_INICIO = 1  # Nivel donde empezar (1-10)
DEBUG_GOD_MODE = False  # Invencibilidad
DEBUG_MAX_STATS = False  # Stats maximizadas
DEBUG_ALL_UNLOCKED = False  # Todos los personajes desbloqueados
DEBUG_ALL_POWERUPS = False  # Todos los power-ups permanentes
DEBUG_INFINITE_CHARGES = False  # Cargas infinitas de power-ups
