import pygame
import math
import random
import os
import settings
from settings import *

class Particula(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        size = random.randint(2, 6)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx, self.vy = random.uniform(-6, 6), random.uniform(-6, 6)
        self.alpha, self.decay = 255, random.randint(8, 15)

    def update(self, *args, **kwargs):
        self.rect.x += self.vx; self.rect.y += self.vy; self.vy += 0.2
        self.alpha -= self.decay
        if self.alpha <= 0: self.kill()
        else: self.image.set_alpha(self.alpha)

class OrbeXP(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.valor = XP_POR_ENEMIGO
        size = 8
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, VERDE_XP, (size//2, size//2), size//2)
        pygame.draw.circle(self.image, BLANCO, (size//2, size//2), size//4)
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = random.uniform(1.5, 3.0)
        self.vx = random.uniform(-1, 1)

    def update(self, *args, **kwargs):
        mago = kwargs.get('mago', None)
        if not mago and args and not isinstance(args[0], pygame.sprite.Group): mago = args[0] # Positional fallback safe check
        if mago:
            dx = mago.rect.centerx - self.rect.centerx
            dy = mago.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 160: 
                self.vx += (dx / dist) * 0.9
                self.vy += (dy / dist) * 0.9
        
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.top > ALTO: self.kill()

class ParticulaAmbiental(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo="luciernaga"):
        super().__init__()
        size = random.randint(2, 4)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = COLOR_LUCIERNAGA if tipo == "luciernaga" else COLOR_MOTA_MAGICA
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, -1.5) if tipo == "luciernaga" else random.uniform(-1, 1)
        self.alpha, self.estado_alpha = 0, 1

    def update(self, *args, **kwargs):
        self.rect.x += self.vx; self.rect.y += self.vy
        if self.estado_alpha == 1:
            self.alpha += 3
            if self.alpha >= 200: self.estado_alpha = -1
        else:
            self.alpha -= 2
            if self.alpha <= 0: self.kill()
        self.image.set_alpha(self.alpha)
        if random.random() < 0.05: self.vx += random.uniform(-0.1, 0.1)

class Orbital(pygame.sprite.Sprite):
    def __init__(self, centro_x, centro_y, radio_orbita, velocidad_angular):
        super().__init__()
        self.radio = 8
        self.image = pygame.Surface((self.radio*2, self.radio*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ROJO_ORBITAL, (self.radio, self.radio), self.radio)
        pygame.draw.circle(self.image, BLANCO, (self.radio, self.radio), self.radio // 2)
        self.rect = self.image.get_rect()
        self.centro_x, self.centro_y, self.radio_orbita = centro_x, centro_y, radio_orbita
        self.angulo, self.velocidad_angular, self.danio = 0, velocidad_angular, 5 

    def update(self, *args, **kwargs):
        centro_nuevo_x = kwargs.get('centro_nuevo_x', None)
        centro_nuevo_y = kwargs.get('centro_nuevo_y', None)
        if not centro_nuevo_x and len(args) >= 2:
             centro_nuevo_x, centro_nuevo_y = args[0], args[1]
        if centro_nuevo_x is not None:
            self.centro_x, self.centro_y = centro_nuevo_x, centro_nuevo_y
        self.angulo += self.velocidad_angular
        if self.angulo >= 360: self.angulo -= 360
        rad = math.radians(self.angulo)
        self.rect.centerx = self.centro_x + math.cos(rad) * self.radio_orbita
        self.rect.centery = self.centro_y + math.sin(rad) * self.radio_orbita

class Proyectil(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, danio, color=CIAN_MAGIA, es_explosivo=False, es_enemigo=False, es_potenciado=False, rebotes=0, penetracion=0, radio_custom=None, es_homing=False, target=None, es_hielo=False, es_fragmentacion=False, es_quemadura=False, es_bomba=False, furia_ignea=False, tirador_sombra=False, es_critico=False, proyectil_grande=False):
        super().__init__()
        self.danio, self.es_explosivo, self.es_enemigo = danio, es_explosivo, es_enemigo
        self.rebotes, self.penetracion, self.es_homing, self.es_hielo, self.es_fragmentacion = rebotes, penetracion, es_homing, es_hielo, es_fragmentacion
        self.target, self.es_bomba = target, es_bomba 
        self.es_quemadura = es_quemadura
        self.furia_ignea = furia_ignea
        self.tirador_sombra = tirador_sombra
        self.color_original, self.es_potenciado = color, es_potenciado
        self.es_critico = es_critico
        
        # Ajuste de tamaño
        radio_defecto = 4 if es_enemigo else (10 if es_explosivo else 5)
        # SINERGIA: Proyectil Grande
        if proyectil_grande:
            radio_defecto = int(radio_defecto * 1.8)
        radio = radio_custom if radio_custom else radio_defecto
        
        if es_enemigo:
            c = color if color != MORADO_OSCURO else COLOR_PROYECTIL_ENEMIGO
            if radio > 20: c = MORADO_CARGADO 
            if color == BOSS_FUEGO_COLOR: c = BOSS_FUEGO_COLOR
            
            # Glow Effect
            glow_surf = pygame.Surface((radio*4, radio*4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*COLOR_GLOW_ENEMIGO, 100), (radio*2, radio*2), radio*2)
            self.image = pygame.Surface((radio*4, radio*4), pygame.SRCALPHA)
            self.image.blit(glow_surf, (0,0))
            pygame.draw.circle(self.image, c, (radio*2, radio*2), radio)
            self.rect = self.image.get_rect(center=(x, y))
        else:
            self.image = pygame.Surface((radio*2+6, radio*2+6), pygame.SRCALPHA)
            c = ORO_PODER if es_potenciado else color
            if self.es_homing: c = AZUL_HOMING 
            if self.es_hielo: c = AZUL_CONGELADO
            if self.es_fragmentacion: c = NARANJA_FUEGO
            if self.es_quemadura: c = ROJO_VIDA # Visual Fuego
            if self.penetracion > 0: c = (255, 255, 200) # Visual Perforante (Mas blanco brillante)

            pygame.draw.circle(self.image, c, (radio+3, radio+3), radio)
            if es_explosivo or self.es_hielo: pygame.draw.circle(self.image, BLANCO, (radio+3, radio+3), radio//3)
            # Efecto adicional para hielo: borde brillante animado
            if self.es_hielo:
                pygame.draw.circle(self.image, (200, 240, 255), (radio+3, radio+3), radio, width=2)
            self.rect = self.image.get_rect(center=(x, y))
        
        self.vx, self.vy = vx, vy
        self.velocidad_total = math.hypot(vx, vy)

    def update(self, *args, **kwargs):
        monstruos = kwargs.get('monstruos', None)
        if not monstruos and args and isinstance(args[0], pygame.sprite.Group): monstruos = args[0]
        
        if self.es_homing:
            if (not self.target or not self.target.alive()):
                if monstruos:
                    self.target = self.buscar_target(monstruos)
            
            if self.target and self.target.alive():
                dx, dy = self.target.rect.centerx - self.rect.centerx, self.target.rect.centery - self.rect.centery
                angulo_target = math.atan2(dy, dx)
                angulo_actual = math.atan2(self.vy, self.vx)
                diff = angulo_target - angulo_actual
                while diff <= -math.pi: diff += 2*math.pi
                while diff > math.pi: diff -= 2*math.pi
                
                nueva_dir = angulo_actual + diff * 0.15
                self.vx = math.cos(nueva_dir) * self.velocidad_total
                self.vy = math.sin(nueva_dir) * self.velocidad_total

        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.rebotes > 0 and (self.rect.left <= 0 or self.rect.right >= ANCHO):
            self.vx *= -1
            self.rebotes -= 1

        if (self.rect.bottom < 0 or self.rect.top > ALTO or 
            (self.rebotes <= 0 and (self.rect.left > ANCHO or self.rect.right < 0))):
            self.kill()

    def buscar_target(self, monstruos):
        target, d_min = None, 9999
        for m in monstruos:
            if m.alive() and m.rect.centery < self.rect.centery: 
                d = math.hypot(m.rect.centerx - self.rect.centerx, m.rect.centery - self.rect.centery)
                if d < d_min:
                    d_min, target = d, m
        return target

    def rebotar(self, monstruos, ignorar=None):
        nuevo_target = None
        d_min = 9999
        for m in monstruos:
            if m.alive() and m != ignorar:
                d = math.hypot(m.rect.centerx - self.rect.centerx, m.rect.centery - self.rect.centery)
                if d < d_min:
                    d_min, nuevo_target = d, m
        
        if nuevo_target:
            dx, dy = nuevo_target.rect.centerx - self.rect.centerx, nuevo_target.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.vx = (dx / dist) * self.velocidad_total
                self.vy = (dy / dist) * self.velocidad_total
                self.rebotes -= 1
                return True
        return False

    def fragmentar(self, grupo_s, grupo_b, multi=1):
        for i in range(6):
            rad = math.radians(i * 60)
            vx, vy = math.cos(rad) * 6, math.sin(rad) * 6
            
            f = Proyectil(self.rect.centerx, self.rect.centery, vx, vy, 4 * multi, 
                          color=self.color_original, es_potenciado=(multi > 1),
                          es_hielo=self.es_hielo, es_quemadura=self.es_quemadura)
            grupo_s.add(f); grupo_b.add(f)

class Rayo(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.es_rayo, self.danio = True, 9999
        self.image = pygame.Surface((20, 120), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(x, y)); self.vy = -22; self.anim_timer = 0
        self.dibujar_zigzag()

    def dibujar_zigzag(self):
        self.image.fill((0,0,0,0)); pts = []
        for i in range(9): pts.append((10 + random.randint(-8,8), i * (120/8)))
        if len(pts)>1: pygame.draw.lines(self.image, AZUL_RAYO, False, pts, 5)

    def update(self, *args, **kwargs):
        self.rect.y += self.vy; self.anim_timer += 1
        if self.anim_timer % 3 == 0: self.dibujar_zigzag()
        if self.rect.bottom < 0: self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, nivel, dificultad, variante=BOSS_TIPO_NORMAL):
        super().__init__()
        self.dificultad, self.variante = dificultad, variante
        mult_hp = 0.8 if self.variante == BOSS_TIPO_HIELO else (1.3 if self.variante == BOSS_TIPO_TOXICO else 1.0)
        self.hp_max = int(HP_BOSS_BASE * (1 + (nivel // 10)) * mult_hp)
        self.hp = self.hp_max
        self.color_base = (100, 200, 255) if self.variante == BOSS_TIPO_HIELO else ((50, 200, 50) if self.variante == BOSS_TIPO_TOXICO else (BOSS_FUEGO_COLOR if self.variante == BOSS_TIPO_FUEGO else MORADO_OSCURO))
        self.cargar_imagen()
        self.image = self.image_original.copy()
        self.rect = self.image.get_rect(midtop=(ANCHO//2, -180)); self.rect.inflate_ip(-40, -10)
        self.pos_x, self.pos_y = float(self.rect.x), float(self.rect.y)
        self.vx, self.vy = VEL_BOSS_X_MAX, VEL_BOSS_Y_MAX
        if self.dificultad == MODO_DIFICIL: self.vx *= BOSS_VEL_MULT_DIFICIL; self.vy *= BOSS_VEL_MULT_DIFICIL
        self.timer_ia = self.ultimo_arco = self.ultimo_rafaga = self.ultimo_ataque_cargado = 0
        self.en_rafaga = self.preparando_ataque = self.destruyendo = self.congelado = False
        self.balas_rafaga = self.timer_preparacion_inicio = self.timer_muerte = self.timer_descongelar = 0
        self.recoil_y = 0; self.alpha_muerte = 255

    def cargar_imagen(self):
        try:
            img = pygame.image.load(resolver_ruta(PATH_BOSS_SPRITE)).convert_alpha()
            self.image_original = pygame.transform.scale(img, (160, 140))
            
            # Cargar ataque opcional
            try:
                img_atk = pygame.image.load(resolver_ruta(PATH_BOSS_ATAQUE)).convert_alpha()
                self.image_ataque = pygame.transform.scale(img_atk, (160, 140))
            except: self.image_ataque = self.image_original # Fallback
            
            # Cargar muerte opcional
            try:
                img_mue = pygame.image.load(resolver_ruta(PATH_BOSS_MUERTE)).convert_alpha()
                self.image_muerte = pygame.transform.scale(img_mue, (160, 140))
            except: self.image_muerte = self.image_original # Fallback

            if self.variante != BOSS_TIPO_NORMAL:
                for img_s in [self.image_original, self.image_ataque, self.image_muerte]:
                    if img_s:
                        c_surf = pygame.Surface(img_s.get_size(), pygame.SRCALPHA)
                        c_surf.fill((*self.color_base, 100)); img_s.blit(c_surf, (0,0), special_flags=pygame.BLEND_MULT)
        except:
            self.image_original = pygame.Surface((160, 140), pygame.SRCALPHA)
            pygame.draw.rect(self.image_original, self.color_base, [0,0,160,140], border_radius=35)
            self.image_ataque = self.image_original
            self.image_muerte = self.image_original
            pygame.draw.circle(self.image_original, BLANCO, (50, 60), 15)
            pygame.draw.circle(self.image_original, NEGRO, (50, 60), 5)
            pygame.draw.circle(self.image_original, BLANCO, (110, 60), 15)
            pygame.draw.circle(self.image_original, NEGRO, (110, 60), 5)

    def iniciar_muerte(self):
        if not self.destruyendo: 
            self.destruyendo, self.timer_muerte, self.vx, self.vy = True, pygame.time.get_ticks() + 2500, 0, 0
            self.image = self.image_muerte.copy()

    def congelar(self):
        self.congelado = True
        self.timer_descongelar = pygame.time.get_ticks() + DURACION_CONGELACION_BOSS
        self.image = self.image_original.copy()
        tinte = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        tinte.fill((*AZUL_CONGELADO, 120)); self.image.blit(tinte, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

    def aplicar_glow(self, surf, color, intensity=0.5):
        glow_surf = pygame.mask.from_surface(surf).to_surface(setcolor=(*color, int(255 * intensity)), unsetcolor=(0,0,0,0))
        for i in range(2):
             surf.blit(glow_surf, (random.randint(-3, 3), random.randint(-3, 3)), special_flags=pygame.BLEND_RGBA_ADD)
        return surf

    def aplicar_tint(self, surf, color):
        tinte = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        tinte.fill((*color, 120))
        surf.blit(tinte, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
        return surf

    def update(self, *args, **kwargs):
        ahora = kwargs.get('ahora', pygame.time.get_ticks())
        grupo_s = kwargs.get('grupo_s', None)
        grupo_b = kwargs.get('grupo_b', None)
        if not grupo_s and args: # Positional fallback
            if len(args) >= 1: ahora = args[0]
            if len(args) >= 2: grupo_s = args[1]
            if len(args) >= 3: grupo_b = args[2]
        if ahora is None or grupo_s is None or grupo_b is None: return
        if self.congelado:
            if ahora > self.timer_descongelar: self.congelado, self.image = False, self.image_original.copy()
            else: return
        if self.destruyendo:
            self.alpha_muerte = max(0, self.alpha_muerte - 2)
            self.image.set_alpha(self.alpha_muerte)
            jitter = 8 if self.alpha_muerte > 100 else 4
            self.rect.center = (self.pos_x + random.randint(-jitter,jitter) + 80, self.pos_y + random.randint(-jitter,jitter) + 70)
            if ahora > self.timer_muerte or self.alpha_muerte <= 0: self.kill()
            return
        if self.preparando_ataque:
            self.image = self.image_ataque.copy()
            if ((ahora - self.timer_preparacion_inicio) // 100) % 2 == 0: self.image.set_alpha(150)
            else: self.image.set_alpha(255)
            if ahora - self.timer_preparacion_inicio >= BOSS_TIEMPO_TELEGRAFO:
                self.preparando_ataque = False
                self.image = self.image_original.copy()
                self.ultimo_ataque_cargado = ahora
                self.recoil_y = -30 # Retroceso fuerte
                c_p = self.color_base
                p = Proyectil(self.rect.centerx, self.rect.bottom + 20, 0, 9.0, 4, es_enemigo=True, color=c_p, radio_custom=55, es_bomba=True)
                grupo_s.add(p); grupo_b.add(p)
            return
        
        # Suavizar retroceso
        if self.recoil_y < 0: self.recoil_y += 2
        elif self.recoil_y > 0: self.recoil_y = 0
        if self.rect.top < 50: self.pos_y += 2
        else:
            self.pos_x += self.vx; self.pos_y += self.vy
            if self.pos_x <= 10 or self.pos_x + 160 >= ANCHO - 10: self.vx *= -1
            if self.pos_y <= 20 or self.pos_y + 140 >= LIMITE_INFERIOR_BOSS: self.vy *= -1
            if ahora > self.timer_ia: self.vx, self.vy = random.uniform(-4, 4), random.uniform(-2, 2); self.timer_ia = ahora + 3000
        self.rect.x, self.rect.y = int(self.pos_x), int(self.pos_y + self.recoil_y)
        
        # --- PATRONES DE ATAQUE POR VARIANTE ---
        cd_arco = BOSS_CD_ARCO
        cd_rafaga = BOSS_CD_RAFAGA
        cd_bomb = 12000 if self.dificultad == MODO_DIFICIL else 15000
        cant_balas_rafaga = 12 if self.dificultad == MODO_DIFICIL else 8
        
        if self.variante == BOSS_TIPO_FUEGO:
            cd_rafaga *= 0.6 # Más ráfagas
            cd_arco *= 1.5   # Menos arcos
            cant_balas_rafaga += 4
        elif self.variante == BOSS_TIPO_HIELO:
            cd_arco *= 0.7   # Más arcos (congelantes)
            cd_rafaga *= 1.2 # Menos ráfagas
        elif self.variante == BOSS_TIPO_TOXICO:
            cd_bomb *= 0.6   # Más bombas (ataque cargado)
            cd_rafaga *= 1.4 # Muy pocas ráfagas
        
        if ahora - self.ultimo_arco > cd_arco:
            self.ultimo_arco = ahora
            self.recoil_y = -15 # Retroceso medio
            for a in [-25, 0, 25]:
                r = math.radians(a+90); vx, vy = math.cos(r)*4.5, math.sin(r)*4.5
                b_color = self.color_base
                # Jefe Hielo tiene arco congelante
                es_hielo = (self.variante == BOSS_TIPO_HIELO)
                p = Proyectil(self.rect.centerx, self.rect.bottom, vx, vy, 1, es_enemigo=True, color=b_color, radio_custom=14, es_hielo=es_hielo)
                grupo_s.add(p); grupo_b.add(p)

        if self.en_rafaga:
            if ahora - self.ultimo_rafaga > 150:
                self.ultimo_rafaga = ahora
                p = Proyectil(self.rect.centerx + random.randint(-40, 40), self.rect.bottom, 0, 7.5, 1, es_enemigo=True, radio_custom=9)
                grupo_s.add(p); grupo_b.add(p)
                self.balas_rafaga -= 1
                if self.balas_rafaga <= 0: self.en_rafaga = False
        elif ahora - self.ultimo_rafaga > cd_rafaga:
            self.en_rafaga, self.balas_rafaga, self.ultimo_rafaga = True, cant_balas_rafaga, ahora
        
        # ATAQUE CARGADO (BOMBA) - Solo en modo difícil
        if self.dificultad == MODO_DIFICIL:
            if ahora - self.ultimo_ataque_cargado > cd_bomb and not self.preparando_ataque:
                self.preparando_ataque = True
                self.timer_preparacion_inicio = ahora

class Mago(pygame.sprite.Sprite):
    def __init__(self, grupo_s, grupo_b, snd_disparo=None, tipo_personaje="MAGO", meta_mejoras=None):
        super().__init__()
        self.grupo_s, self.grupo_b, self.snd_disparo, self.tipo = grupo_s, grupo_b, snd_disparo, tipo_personaje
        
        # Cargar configuración de balanceo
        self.config = CONFIG_PERSONAJES.get(tipo_personaje, CONFIG_PERSONAJES["MAGO"])
        self.datos = DATOS_PERSONAJES.get(tipo_personaje, DATOS_PERSONAJES["MAGO"])
        
        if meta_mejoras is None: meta_mejoras = {"vida_base": 0, "danio_base": 0, "critico": 0, "maestria_hielo": 0}
        self.nivel_hielo = meta_mejoras.get("maestria_hielo", 0)
        
        # Configurar stats usando el nuevo sistema de balanceo
        cfg = self.config
        self.stats = {
            "danio_multi": cfg["danio_multi"] + (meta_mejoras.get("danio_base", 0) * cfg["danio_escalado_por_nivel"]),
            "velocidad_ataque_multi": CADENCIA_BASE / cfg["cadencia_base_ms"],
            "velocidad_proyectil": cfg["velocidad_proyectil"],
            "proyectiles_extra": cfg["proyectiles_extra"],
            "rebotes": 0, 
            "penetracion": 0, 
            "chance_critico": cfg["chance_critico"] + meta_mejoras.get("critico", 0) * 0.05, 
            "danio_critico": cfg["danio_critico"],
            "velocidad_movimiento": cfg["velocidad_movimiento"]
        }
        
        self.modificadores = {
            "explosivo": "explosivo" in cfg["modificadores_iniciales"], 
            "arco": "arco" in cfg["modificadores_iniciales"], 
            "fragmentacion": False,
            "homing": False,
            "proyectil_grande": False
        }
        
        # Contador de mejoras picked (para mejoras que apilan)
        self.mejoras_contador = {
            "vida": 0,
            "danio": 0,
            "vel_atk": 0,
            "multidisparo": 0,
            "rebote": 0,
            "perforante": 0,
            "hielo_perma": 0,
            "proyectil_grande": 0,
            "homing_perma": 0
        }
        
        self.cargar_assets(cfg["color"])
        self.rect = self.image.get_rect(midbottom=(ANCHO // 2, ALTO - 40))
        self.hitbox = self.rect.inflate(-self.rect.width/2, -self.rect.height/2)

        
        # Vida usando configuración de balanceo
        self.max_vidas = cfg["vida_maxima"] + meta_mejoras.get("vida_base", 0)
        self.vidas = self.max_vidas
        
        self.xp_actual, self.xp_requerida, self.nivel_run, self.oleada_actual = 0, XP_BASE_REQUERIDA, 1, 1
        self.ultimo_disparo = self.fin_powerup = self.cargas = self.fin_doble_danio = self.fin_escudo = 0
        self.powerup_actual = "normal"; self.doble_danio_activo = self.esta_disparando = self.escudo_activo = self.invulnerable = False
        self.fin_animacion_disparo = self.fin_invulnerable = self.radio_escudo = 140
        self.orbitales_grupo = pygame.sprite.Group(); self.orbital_activo = False; self.fin_orbital = 0
        
        # ESCUDO ESPECIAL NIVEL 5 (HABILIDAD ÚNICA DEL PERSONAJE)
        self.escudo_especial = None
        self.escudo_especial_desbloqueado = False
        
        # DASH - Usando configuración de balanceo
        self.dashing = False
        self.fin_dash = 0
        self.dash_cd = 0
        self.dash_dir = 0
        self.dash_velocidad = cfg["dash_velocidad"]
        self.dash_duracion = cfg["dash_duracion_ms"]
        self.dash_cooldown = cfg["dash_cooldown_ms"]
        
        self.escudo_pendiente = False
        self.fin_ralentizado = 0
        self.resbalando = False; self.momentum_x = 0
        
        # SKILLS DE CLASE
        self.skill_shield = False; self.shield_hp = 0; self.shield_regen_timer = 0
        self.shield_regen_cd = 45000 # 45s base
        self.shield_max_hp = 1
        
        # Habilidad especial del personaje (se desbloquea en boss nivel 5)
        self.habilidad_especial = cfg["habilidad_especial"]
        self.skill_burn = False  # Solo se activa al matar boss nivel 5
        self.burn_exp_damage = 0
        self.burn_exp_radius = 0
        
        self.skill_pierce = False; self.shots_fired = 0
        self.pierce_freq = 4
        self.pierce_count = 3
        
        self.skill_cancel_prob = 0.0
        
        # HABILIDAD ESPECIAL NIVEL 5
        self.furia_ignea = False  # Piromante: probabilidad de quemar
        self.tirador_sombra = False  # Cazador: probabilidad de atravesar todos
        
        # Sistema de Carga (SNAKE)
        self.carga = 0
        self.max_carga = cfg.get("tiempo_carga_max_ms", 1000)
        self.cargando = False
        self.danio_carga_max = cfg.get("danio_carga_max", 3.0)
        self.velocidad_carga_max = cfg.get("velocidad_carga_max", 1.5)
        self.velocidad_carga = cfg.get("velocidad_carga", cfg.get("velocidad_movimiento", 6.5))
        
        # MODO DEBUG - Aplicar boosts
        if settings.DEBUG_MODE:
            self._aplicar_debug_boosts()

        # Atributos para control táctil
        self.mover_izquierda = False
        self.mover_derecha = False
        self.disparando_tactil = False
        self.direccion_touch = 0

    def _aplicar_debug_boosts(self):
        """Aplica boosts de estadísticas para modo debug"""
        if settings.DEBUG_MAX_STATS:
            # Stats superpoderosas
            self.stats["danio_multi"] = 10.0
            self.stats["velocidad_ataque_multi"] = 5.0
            self.stats["velocidad_proyectil"] = 15.0
            self.stats["proyectiles_extra"] = 5
            self.stats["rebotes"] = 5
            self.stats["penetracion"] = 5
            self.stats["chance_critico"] = 1.0  # 100% crítico
            self.stats["danio_critico"] = 5.0
            self.stats["velocidad_movimiento"] = 12.0
            self.nivel_hielo = 20  # 100% chance de congelar
            
        if settings.DEBUG_GOD_MODE:
            self.max_vidas = 999
            self.vidas = 999
            self.invulnerable = True  # Siempre invulnerable
            
        if settings.DEBUG_ALL_POWERUPS:
            # Todos los modificadores permanentes
            self.modificadores["explosivo"] = True
            self.modificadores["arco"] = True
            self.modificadores["fragmentacion"] = True
            
            # Todas las skills desbloqueadas
            self.skill_shield = True
            self.shield_hp = 999
            self.shield_max_hp = 999
            self.skill_burn = True
            self.skill_pierce = True
            self.skill_cancel_prob = 1.0  # 100% cancelación

    def cargar_assets(self, color):
        scale_factor = 1.5
        w, h = int(MAGO_ANCHO * scale_factor), int(MAGO_ALTO * scale_factor)
        
        try:
            raw_normal = pygame.image.load(resolver_ruta(self.datos["sprite"])).convert_alpha()
            raw_disparo = pygame.image.load(resolver_ruta(self.datos["sprite_disparo"])).convert_alpha()
            self.imagen_normal = pygame.transform.scale(raw_normal, (w, h))
            self.imagen_disparo = pygame.transform.scale(raw_disparo, (w, h))
        except:
            self.imagen_normal = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.polygon(self.imagen_normal, color, [(w//2, 0), (0, h), (w, h)])
            pygame.draw.circle(self.imagen_normal, BLANCO, (w//3, h//2), 3)
            pygame.draw.circle(self.imagen_normal, BLANCO, (2*w//3, h//2), 3)
            self.imagen_disparo = self.imagen_normal.copy()
            pygame.draw.rect(self.imagen_disparo, CIAN_MAGIA, [0, 0, w, h], 2)
        
        # Add subtle Glow
        pad = 4
        glow_surf = pygame.Surface((w+pad*2, h+pad*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 255, 255, 35), ((w+pad*2)//2, (h+pad*2)//2), w//2 + 2)
        
        final_normal = pygame.Surface((w+pad*2, h+pad*2), pygame.SRCALPHA)
        final_normal.blit(glow_surf, (0,0))
        final_normal.blit(self.imagen_normal, (pad, pad))
        self.imagen_normal = final_normal
        
        final_disparo = pygame.Surface((w+pad*2, h+pad*2), pygame.SRCALPHA)
        final_disparo.blit(glow_surf, (0,0))
        final_disparo.blit(self.imagen_disparo, (pad, pad))
        self.imagen_disparo = final_disparo

        self.image = self.imagen_normal

    def dash(self):
        ahora = pygame.time.get_ticks()
        if ahora > self.dash_cd and self.dash_dir != 0:
            self.dashing, self.fin_dash, self.dash_cd, self.invulnerable = True, ahora + self.dash_duracion, ahora + self.dash_cooldown, True
            self.fin_invulnerable = ahora + self.dash_duracion + 100

    def ganar_xp(self, cantidad):
        self.xp_actual += cantidad
        if self.xp_actual >= self.xp_requerida:
            self.xp_actual -= self.xp_requerida; self.nivel_run += 1
            self.xp_requerida = int(self.xp_requerida * XP_FACTOR_ESCALADO); return True
        return False

    def aplicar_powerup(self, tipo):
        ahora = pygame.time.get_ticks()
        stats = POWERUPS_STATS.get(tipo, {})
        if tipo == "escudo":
            self.escudo_pendiente = True
            return
        if tipo == "orbital":
            self.orbital_activo = True
            self.fin_orbital = ahora + stats.get("duracion", 15000)
            self.orbitales_grupo.empty()
            for i in range(3):
                self.orbitales_grupo.add(Orbital(self.rect.centerx, self.rect.centery, 80, 4 + i))
            return
        if tipo == "doble_danio":
            self.doble_danio_activo = True
            self.fin_doble_danio = ahora + stats.get("duracion", 9000)
            return

        self.powerup_actual = tipo
        if "duracion" in stats:
            self.fin_powerup = ahora + stats["duracion"]
            self.cargas = 0
        elif "cargas" in stats:
            self.cargas = stats["cargas"]
            self.fin_powerup = 0

    def activar_escudo(self):
        self.escudo_pendiente = False
        self.escudo_activo = True
        self.fin_escudo = pygame.time.get_ticks() + 8000

    def cargar(self):
        if self.tipo == "snake":
            self.cargando = True
            # La carga escala con la velocidad de ataque
            esc_cad = self.config.get("cadencia_escalado", ESCALADO_CADENCIA_POR_NIVEL)
            cadencia = (CADENCIA_BASE * (esc_cad ** self.oleada_actual)) / self.stats["velocidad_ataque_multi"]
            # SINERGIA: Powerup de cadencia carga más rápido
            if self.powerup_actual == "cadencia": cadencia *= 0.4
            # Reducción de cadencia por powerups de disparo múltiple (también carga más rápido)
            if self.powerup_actual == "disparo_doble": cadencia *= 0.67
            elif self.powerup_actual == "disparo_triple": cadencia *= 0.5
            # SINERGIA: Multiplicador de velocidad de carga por stats
            vel_carga_multi = self.stats.get("velocidad_carga_multi", 1.0)
            self.carga = min(self.carga + (20 * (CADENCIA_BASE / cadencia) * vel_carga_multi), self.max_carga)

    def liberar_carga(self, grupo_b):
        if self.tipo == "snake" and self.cargando:
            potencia_carga = self.carga / self.max_carga
            potencia = max(0.25, potencia_carga)
            
            # SOLO disparar cuando la carga está al 100%
            if self.carga >= self.max_carga:
                if self.snd_disparo: self.snd_disparo.play()
                
                multi_danio = self.stats.get("danio_multi", 1.0)
                multi_doble_danio = 2.0 if self.doble_danio_activo else 1.0
                
                # SINERGIAS DE DAÑO
                if self.powerup_actual == "disparo_doble": multi_danio *= 1.25
                elif self.powerup_actual == "disparo_triple": multi_danio *= 1.4
                elif self.powerup_actual == "explosivo": multi_danio *= 1.3
                
                danio_base = self.stats.get("danio_base", 0.15)
                danio_carga_max = self.stats.get("danio_carga_max", 0.5)
                danio_carga_minimo = self.stats.get("danio_carga_minimo", 0.08)
                danio_rayo = danio_base + (danio_carga_max - danio_base) * potencia_carga
                danio_rayo = max(danio_carga_minimo, danio_rayo) * multi_danio * multi_doble_danio
                
                # SINERGIAS DE LONGITUD
                longitud_base = 150
                longitud_bonus = 0
                if self.powerup_actual == "arco": longitud_bonus += 100
                if self.powerup_actual == "explosivo": longitud_bonus += 80
                longitud_rayo = int(longitud_base + (550 * potencia) + longitud_bonus)
                
                duracion = 1000
                
                # SINERGIAS: Rebotes y Homing
                num_rebotes = 0
                es_homing = False
                if self.powerup_actual == "rebote" and self.cargas > 0:
                    num_rebotes = 2
                elif self.modificadores.get("rebotes", 0) > 0:
                    num_rebotes = self.modificadores["rebotes"]
                
                if self.powerup_actual == "homing" and self.cargas > 0:
                    es_homing = True
                
                # Color del rayo según powerup
                color_rayo = (255, 0, 150)  # Rosa por defecto
                if self.powerup_actual == "arco": color_rayo = (255, 165, 0)
                elif self.powerup_actual == "rebote": color_rayo = (0, 255, 255)
                elif self.powerup_actual == "explosivo": color_rayo = (255, 100, 0)
                elif self.powerup_actual == "homing": color_rayo = (50, 255, 50)
                
                r = RayoPlayer(self.rect.centerx, self.rect.top, mago=self, duracion=duracion, 
                              potencia=potencia, longitud_max=longitud_rayo, danio=danio_rayo,
                              rebotes=num_rebotes, es_homing=es_homing, color=color_rayo)
                self.grupo_s.add(r)
                grupo_b.add(r)
            self.carga = 0
            self.cargando = False

    def disparar(self, monstruos=None):
        # SNAKE: Sistema de carga único
        if self.tipo == "snake":
            self.cargar()
            return
        
        ahora = pygame.time.get_ticks()
        esc_cad = self.config.get("cadencia_escalado", ESCALADO_CADENCIA_POR_NIVEL)
        cadencia = (CADENCIA_BASE * (esc_cad ** self.oleada_actual)) / self.stats["velocidad_ataque_multi"]
        if self.powerup_actual == "cadencia": cadencia *= 0.4
        elif self.powerup_actual == "disparo_doble": cadencia *= 1.25
        elif self.powerup_actual == "disparo_triple": cadencia *= 1.67
        cadencia = min(cadencia, 2500)
        
        if ahora - self.ultimo_disparo > cadencia:
            self.ultimo_disparo, self.esta_disparando, self.fin_animacion_disparo = ahora, True, ahora + 150
            if self.snd_disparo: self.snd_disparo.play()
            
            es_critico = random.random() < self.stats["chance_critico"]
            multi_critico = self.stats["danio_critico"] if es_critico else 1
            danio = DANIO_BASE_MAGO * self.stats["danio_multi"] * (2 if self.doble_danio_activo else 1) * multi_critico
            
            if self.powerup_actual == "rayo" and self.cargas > 0:
                r = Rayo(self.rect.centerx, self.rect.top)
                self.grupo_s.add(r); self.grupo_b.add(r)
                self.cargas -= 1; return
            
            es_exp = self.modificadores["explosivo"] or (self.powerup_actual == "explosivo" and self.cargas > 0)
            es_frag = self.modificadores["fragmentacion"] 

            if self.powerup_actual == "explosivo": 
                if not (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES): self.cargas -= 1
            
            target = None
            if self.powerup_actual == "homing" and self.cargas > 0:
                if not (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES): self.cargas -= 1
                d_min = 9999
                for m in monstruos:
                    d = math.hypot(m.rect.centerx - self.rect.centerx, m.rect.centery - self.rect.centery)
                    if d < d_min and m.rect.y < self.rect.y: d_min, target = d, m
            
            es_hielo = random.random() < (self.nivel_hielo * 0.05)
            es_homing = self.powerup_actual == "homing" and (self.cargas > 0 or (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES))
            num = 1 + self.stats["proyectiles_extra"] + (1 if self.powerup_actual == "disparo_doble" and (self.cargas > 0 or (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES)) else 0) + (1 if self.powerup_actual == "disparo_triple" and (self.cargas > 0 or (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES)) else 0)

            if self.powerup_actual == "disparo_doble":
                if not (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES): self.cargas -= 1
            elif self.powerup_actual == "disparo_triple":
                if not (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES): self.cargas -= 1
            
            # --- CLASS SKILLS LOGIC ---
            es_quemadura = self.skill_burn or self.furia_ignea
            
            penetracion = 0
            # TIRADOR DE SOMBRA: probabilidad de atravesar todos (30%)
            if self.tirador_sombra and random.random() < 0.30:
                penetracion = 999  # Atraviesa todos los enemigos
            elif self.skill_pierce:
                self.shots_fired += 1
                if self.shots_fired % self.pierce_freq == 0:
                     penetracion = self.pierce_count
            
            ang_start = -90 - (5 * (num-1))
            vel_p = self.stats["velocidad_proyectil"]
            for i in range(num):
                rad = math.radians(ang_start + (10 * i))
                self.crear_bala(math.cos(rad)*vel_p, math.sin(rad)*vel_p, danio, es_exp, target, es_hielo, es_frag, es_quemadura=es_quemadura, penetracion=penetracion, es_homing=es_homing, es_critico=es_critico)
            
            if self.modificadores["arco"] or (self.powerup_actual == "arco" and (self.cargas > 0 or (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES))):
                v_arc_x = vel_p * 0.38 # Proporcional a la velocidad total
                v_arc_y = -vel_p * 0.88
                
                # Diferenciación Arco: 15% bounce, 15% pierce 1
                p_arco_bounce = 1 if random.random() < 0.15 else 0
                p_arco_pierce = 1 if random.random() < 0.15 else 0
                
                self.crear_bala(-v_arc_x, v_arc_y, danio, es_exp, target, es_hielo, es_frag, es_quemadura=es_quemadura, penetracion=p_arco_pierce, rebotes=p_arco_bounce, es_homing=es_homing, es_critico=es_critico)
                self.crear_bala(v_arc_x, v_arc_y, danio, es_exp, target, es_hielo, es_frag, es_quemadura=es_quemadura, penetracion=p_arco_pierce, rebotes=p_arco_bounce, es_homing=es_homing, es_critico=es_critico)
                if self.powerup_actual == "arco": 
                    if not (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES): self.cargas -= 1
            
            if self.cargas <= 0 and not (settings.DEBUG_MODE and settings.DEBUG_INFINITE_CHARGES) and self.powerup_actual in ["arco", "disparo_doble", "disparo_triple", "explosivo", "rayo", "homing"]: 
                self.powerup_actual = "normal"

    def crear_bala(self, vx, vy, danio, es_exp, target, es_hielo, es_frag, es_quemadura=False, penetracion=0, rebotes=0, es_homing=False, es_critico=False):
        c = NARANJA_FUEGO if es_exp else ((100, 255, 100) if self.stats["rebotes"] > 0 else CIAN_MAGIA)
        pen_total = self.stats["penetracion"] + penetracion
        furia = self.furia_ignea
        sombra = self.tirador_sombra
        
        # SINERGIA: Homing Permamente - alta probabilidad de auto-apuntado
        es_homing_perma = False
        if self.modificadores.get("homing", False):
            prob_homing = 0.4 + (self.mejoras_contador.get("homing_perma", 0) * 0.05)
            if random.random() < prob_homing:
                es_homing_perma = True
        
        b = Proyectil(self.rect.centerx, self.rect.top, vx, vy, danio, color=c, es_explosivo=es_exp, es_potenciado=self.doble_danio_activo, rebotes=self.stats["rebotes"], penetracion=pen_total, target=target, es_hielo=es_hielo, es_fragmentacion=es_frag, es_quemadura=es_quemadura, es_homing=es_homing or es_homing_perma, furia_ignea=furia, tirador_sombra=sombra, es_critico=es_critico, proyectil_grande=self.modificadores.get("proyectil_grande", False))
        self.grupo_s.add(b); self.grupo_b.add(b)

    def recibir_danio(self):
        if not self.invulnerable and not self.escudo_activo and not self.dashing:
            # Shield Check
            if self.skill_shield and self.shield_hp > 0:
                self.shield_hp -= 1
                self.shield_regen_timer = pygame.time.get_ticks() + self.shield_regen_cd
                self.invulnerable, self.fin_invulnerable = True, pygame.time.get_ticks() + 1000 # Breve invuln
                return False

            self.vidas -= 1; self.invulnerable, self.fin_invulnerable = True, pygame.time.get_ticks() + 2000; return True
        return False

    def update(self, *args, **kwargs):
        ahora = pygame.time.get_ticks()
        teclas = pygame.key.get_pressed()

        # Combinar entrada de teclado y táctil
        dash_from_key = -1 if teclas[pygame.K_LEFT] else (1 if teclas[pygame.K_RIGHT] else 0)
        self.dash_dir = dash_from_key

        # Si hay input táctil,用它覆盖 el teclado
        if self.mover_izquierda:
            self.dash_dir = -1
        elif self.mover_derecha:
            self.dash_dir = 1

        factor_vel = 1.0
        if self.fin_ralentizado > 0: factor_vel = FACTOR_RALENTIZADO

        # Movimiento Normal vs Resbalando (Hielo)
        speed = self.stats["velocidad_movimiento"] * factor_vel

        # SNAKE: Reducir velocidad mientras carga
        if self.cargando and self.tipo == "snake":
            speed = self.velocidad_carga

        target_vx = 0
        if self.resbalando:
            # En hielo, baja friccion. Mantiene momentum.
            if self.dash_dir != 0: self.momentum_x += self.dash_dir * 0.2 # Aceleracion lenta
            self.momentum_x *= 0.98 # Friccion muy baja
        else:
            # Control normal
            if self.dashing: speed = self.dash_velocidad
            if self.dash_dir != 0: target_vx = self.dash_dir * speed
            # Aproximacion instantanea (sin inercia normal)
            self.momentum_x = target_vx

        # Cap de velocidad en hielo
        if self.resbalando:
            max_slide = speed * 1.5
            if self.momentum_x > max_slide: self.momentum_x = max_slide
            if self.momentum_x < -max_slide: self.momentum_x = -max_slide

        # Aplicar movimiento
        if self.momentum_x != 0:
            new_x = self.rect.x + self.momentum_x
            if 0 <= new_x <= ANCHO - self.rect.width:
                self.rect.x = int(new_x)
            else:
                 self.momentum_x = 0 # Choque con pared

        if self.dashing and ahora > self.fin_dash: self.dashing = False
        self.resbalando = False # Reset flag por frame, se actíva si colisiona con charco
        
        # Check slow
        if self.fin_ralentizado > 0 and ahora > self.fin_ralentizado:
            self.fin_ralentizado = 0
            
        # ACTUALIZAR ESCUDO ESPECIAL
        if self.escudo_especial:
            self.escudo_especial.update()
        
        # REGENERACION ESCUDO MAGICO (APRENDIZ)
        if self.skill_shield and self.shield_hp < self.shield_max_hp:
            if ahora > self.shield_regen_timer:
                self.shield_hp += 1
                if self.shield_hp < self.shield_max_hp:
                    self.shield_regen_timer = ahora + self.shield_regen_cd

        self.image = self.imagen_disparo if self.esta_disparando and ahora < self.fin_animacion_disparo else self.imagen_normal
        if self.invulnerable and ahora > self.fin_invulnerable: self.invulnerable = False; self.image.set_alpha(255)
        elif self.invulnerable: self.image.set_alpha(100 if (ahora // 100) % 2 == 0 else 255)
        
        if self.fin_powerup > 0 and ahora > self.fin_powerup:
            self.powerup_actual = "normal"; self.fin_powerup = 0
        if self.doble_danio_activo and ahora > self.fin_doble_danio:
            self.doble_danio_activo = False
        if self.escudo_activo and ahora > self.fin_escudo:
            self.escudo_activo = False

        if self.orbital_activo:
            if ahora > self.fin_orbital: 
                self.orbital_activo = False
                for o in self.orbitales_grupo: o.kill()
            else: 
                self.orbitales_grupo.update(self.rect.centerx, self.rect.centery)
        
        # Sync hitbox
        if hasattr(self, 'hitbox'):
             self.hitbox.center = self.rect.center

    def aplicar_ralentizacion(self):
        self.fin_ralentizado = pygame.time.get_ticks() + DURACION_RALENTIZADO

class Monstruo(pygame.sprite.Sprite):
    def __init__(self, x, y, fila, vel_x, desc, mult_f, nivel=1, tipo=TIPO_ENEMIGO_NORMAL):
        super().__init__()
        self.fila_original = fila 
        self.tipo, idx = tipo, min(fila, 3)
        
        # HP Escalado
        base_hp = HP_POR_FILA[idx]
        if tipo == TIPO_ENEMIGO_TANQUE: base_hp *= 3.0
        elif tipo == TIPO_ENEMIGO_ELITE: base_hp *= 4.5
        elif tipo == TIPO_ENEMIGO_RAPIDO: base_hp *= 0.8
        self.hp = int(base_hp * (1 + (nivel * MULT_VIDA_POR_NIVEL)))

        self.color = GRIS_ELITE if tipo == TIPO_ENEMIGO_ELITE else COLORES_POR_FILA[idx]
        
        v_base = vel_x
        if tipo == TIPO_ENEMIGO_RAPIDO: v_base *= 1.8
        
        self.vel_x, self.desc, self.dir, self.congelado = v_base, desc, 1, False
        self.quemado = False; self.quemado_timer = 0
        self.ultimo_dano_quemadura = 0
        self.murio_por_quemadura = False
        self.furia_ignea_activa = False
        self.frames = []
        self.image_index = 0
        self.anim_timer = 0
        self.anim_delay = 500 # ms para cambiar de frame
        if tipo == TIPO_ENEMIGO_RAPIDO: self.anim_delay = 300 # Mueven patas más rápido

        # --- CARGA DE SPRITES (A y B) ---
        try:
            # Usamos idx (0-3) para mapear a las imágenes
            path_a = resolver_ruta(f"assets/monstruo_{idx}_A.png")
            path_b = resolver_ruta(f"assets/monstruo_{idx}_B.png")
            
            img_a = pygame.image.load(path_a).convert_alpha()
            img_b = pygame.image.load(path_b).convert_alpha()
            
            # Game Feel: Reducido aun más (26->22, 32->28)
            size = 28 if tipo == TIPO_ENEMIGO_ELITE else 22
            img_a = pygame.transform.scale(img_a, (size, size))
            img_b = pygame.transform.scale(img_b, (size, size))
            
            self.frames = [img_a, img_b]
            self.image_original = self.frames[0]
        except Exception as e:
            # Fallback si no encuentra las imágenes
            size = 28 if tipo == TIPO_ENEMIGO_ELITE else 22
            fallback = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(fallback, self.color, [0, 0, size, size], border_radius=4)
            eye_color = NEGRO
            offset = size // 4
            pygame.draw.circle(fallback, BLANCO, (offset, offset), 4)
            pygame.draw.circle(fallback, eye_color, (offset, offset), 2)
            pygame.draw.circle(fallback, BLANCO, (size - offset, offset), 4)
            pygame.draw.circle(fallback, eye_color, (size - offset, offset), 2)
            self.frames = [fallback, fallback]
            self.image_original = fallback

        self.image = self.image_original.copy()
        
        # Draw Border
        border_color = None
        if self.tipo == TIPO_ENEMIGO_TANQUE: border_color = COLOR_BORDE_TANQUE
        elif self.tipo == TIPO_ENEMIGO_ELITE: border_color = COLOR_BORDE_ELITE
        elif self.tipo == TIPO_ENEMIGO_TESORO: border_color = COLOR_BORDE_TESORO
        
        if border_color:
             pygame.draw.rect(self.image, border_color, self.image.get_rect(), 2)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos_x, self.pos_y, self.timer_descongelar, self.mult_f = float(x), float(y), 0, mult_f
        self.rebotes_restantes = 3 if self.tipo == TIPO_ENEMIGO_TESORO else 0

    def intentar_disparar(self, nivel, grupo_s, grupo_e):
        if self.congelado: return
        chance_base = (CHANCE_DISPARO_BASE + (nivel * CHANCE_DISPARO_INCREMENTO)) * self.mult_f
        
        # Aplicar multiplicador por tipo
        multiplicador_tipo = CHANCE_DISPARO_POR_TIPO.get(self.tipo, 1.0)
        chance_final = chance_base * multiplicador_tipo

        if random.random() < chance_final:
            vel_bala = 3.5
            if self.tipo == TIPO_ENEMIGO_ELITE: vel_bala = 5.5
            elif self.tipo == TIPO_ENEMIGO_TESORO: vel_bala = 4.5 # Disparo rápido también
            
            p = Proyectil(self.rect.centerx, self.rect.bottom, 0, vel_bala, 1, es_enemigo=True)
            grupo_s.add(p); grupo_e.add(p)

    def congelar(self):
        self.congelado, self.timer_descongelar = True, pygame.time.get_ticks() + DURACION_CONGELACION_NORMAL
        # Al congelar, aplicamos el tinte sobre el frame actual
        t = pygame.Surface(self.image.get_size(), pygame.SRCALPHA); t.fill((*AZUL_CONGELADO, 150)); self.image.blit(t, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

    def update(self, *args, **kwargs):
        ahora = pygame.time.get_ticks()
        if self.congelado:
            if ahora > self.timer_descongelar: 
                self.congelado = False
                self.image = self.image_original.copy()
            else: return # No se mueve ni anima
        
        # Movimiento Lateral
        self.pos_x += self.vel_x * self.dir
        self.rect.x = int(self.pos_x)
        
        if self.tipo == TIPO_ENEMIGO_TESORO:
            if self.rect.right >= ANCHO or self.rect.left <= 0:
                self.dir *= -1
                self.rebotes_restantes -= 1
                if self.rebotes_restantes <= 0:
                    self.kill()

        # DAÑO POR QUEMADURA (1 daño cada segundo por 5 segundos)
        if self.quemado:
            if ahora - self.ultimo_dano_quemadura > 1000:
                self.hp -= 1
                self.ultimo_dano_quemadura = ahora
                if self.hp <= 0:
                    self.murio_por_quemadura = True
                    if self.furia_ignea_activa:
                        monstruos = kwargs.get('monstruos', None)
                        if monstruos:
                            self.propagar_quemadura(monstruos)
            
            # Expire burn after 5s
            if ahora - self.quemado_timer > 5000: self.quemado = False

        # --- ANIMACIÓN ---
        if ahora - self.anim_timer > self.anim_delay:
            self.anim_timer = ahora
            self.image_index = (self.image_index + 1) % len(self.frames)
            self.image_original = self.frames[self.image_index] # Actualizamos el "original" al frame actual
            self.image = self.image_original.copy()
            
            # Visual Feedback STATUS
            if self.quemado:
                # Tint Rojo
                tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                tint.fill((255, 50, 0, 100))
                self.image.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

    def bajar(self):
        if not self.congelado: 
            self.pos_y += self.desc
            self.rect.y = int(self.pos_y)
            self.dir *= -1
            # Forzar actualización de posición X float para evitar desincronización
            self.pos_x = float(self.rect.x)
    
    def propagar_quemadura(self, monstruos):
        """Propaga la quemadura a enemigos cercanos (FURIA ÍGNEA)"""
        radio_propagacion = 100
        for m in monstruos:
            if m != self and m.alive():
                dist = math.hypot(m.rect.centerx - self.rect.centerx, m.rect.centery - self.rect.centery)
                if dist < radio_propagacion and not m.quemado:
                    m.quemado = True
                    m.quemado_timer = pygame.time.get_ticks()
                    m.ultimo_dano_quemadura = pygame.time.get_ticks()
                    m.furia_ignea_activa = True

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo):
        super().__init__(); self.tipo = tipo
        self.size = 36
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        color = COLORES_PU.get(tipo, BLANCO)
        
        # Glow Effect (Aura externa)
        for r in range(self.size//2, self.size//2 - 6, -1):
            alpha = (self.size//2 - r) * 15
            pygame.draw.circle(self.image, (*color, alpha), (self.size//2, self.size//2), r)
        
        # Cuerpo principal (Cristalizado)
        rect_inner = [6, 6, 24, 24]
        pygame.draw.rect(self.image, color, rect_inner, border_radius=6)
        # Brillo superior
        pygame.draw.rect(self.image, (255, 255, 255, 130), [6, 6, 24, 8], border_radius=6)
        # Borde brillante
        pygame.draw.rect(self.image, BLANCO, rect_inner, 2, border_radius=6)
        
        font_sm = pygame.font.SysFont("Arial", 14, True)
        font_md = pygame.font.SysFont("Arial", 18, True)

        cx, cy = self.size//2, self.size//2

        if tipo == "cadencia":
            s = font_md.render(">>", True, NEGRO)
            self.image.blit(s, s.get_rect(center=(cx, cy)))
        elif tipo == "arco":
            # Icono de arco estilizado
            pygame.draw.arc(self.image, NEGRO, [8, 10, 20, 16], -math.pi/2, math.pi/2, 3)
            pygame.draw.line(self.image, NEGRO, (18, 10), (18, 26), 2)
        elif tipo == "disparo_doble":
            # Icono de 2 balas alineadas (disparo doble)
            for i in range(2):
                pygame.draw.rect(self.image, NEGRO, [cx - 5 + (i*10), cy - 6, 4, 12], border_radius=1)
                pygame.draw.rect(self.image, BLANCO, [cx - 4 + (i*10), cy - 5, 1, 2], border_radius=1)
        elif tipo == "disparo_triple":
            # Icono de 3 balas alineadas (disparo triple)
            for i in range(3):
                pygame.draw.rect(self.image, NEGRO, [cx - 8 + (i*6), cy - 6, 3, 12], border_radius=1)
                pygame.draw.rect(self.image, BLANCO, [cx - 7 + (i*6), cy - 5, 1, 2], border_radius=1)
        elif tipo == "explosivo":
            pygame.draw.circle(self.image, NEGRO, (cx, cy+2), 6)
            pygame.draw.line(self.image, NEGRO, (cx+2, cy-2), (cx+7, cy-7), 2)
            pygame.draw.circle(self.image, ROJO_VIDA, (cx+7, cy-7), 3)
        elif tipo == "escudo":
             # Escudo heráldico/Burbuja
             pygame.draw.circle(self.image, NEGRO, (cx, cy), 10, 3)
             pygame.draw.rect(self.image, NEGRO, [cx-6, cy-5, 12, 12], border_radius=2)
             pygame.draw.line(self.image, BLANCO, (cx-3, cy+1), (cx+3, cy+1), 2)
             pygame.draw.line(self.image, BLANCO, (cx, cy-2), (cx, cy+4), 2)
        elif tipo == "doble_danio":
             s = font_md.render("x2", True, NEGRO)
             self.image.blit(s, s.get_rect(center=(cx, cy)))
        # vida_extra eliminado por redundancia con Corazon()

        elif tipo == "rayo":
            # Rayo más estilizado y grueso
            pts = [(cx+6, cy-11), (cx-4, cy), (cx+4, cy), (cx-6, cy+11)]
            pygame.draw.lines(self.image, NEGRO, False, pts, 4)
            pygame.draw.lines(self.image, (255, 255, 100), False, pts, 1) # Núcleo brillante
        elif tipo == "orbital":
             pygame.draw.circle(self.image, NEGRO, (cx, cy), 4)
             pygame.draw.circle(self.image, NEGRO, (cx, cy), 10, 1)
             pygame.draw.circle(self.image, NEGRO, (cx+10, cy), 3)
        elif tipo == "homing":
             # Flecha curvada
             pygame.draw.arc(self.image, NEGRO, [cx-8, cy-8, 16, 16], 0, math.pi, 2)
             pygame.draw.polygon(self.image, NEGRO, [(cx+8, cy), (cx+4, cy+6), (cx+12, cy+6)])
        elif tipo == "reparar_barreras":
             pygame.draw.rect(self.image, NEGRO, [cx-8, cy-4, 16, 8], border_radius=2)
             pygame.draw.rect(self.image, NEGRO, [cx-4, cy-8, 8, 16], border_radius=2)
        
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, *args, **kwargs):
        self.rect.y += 2.5; 
        if self.rect.top > ALTO: self.kill()

class Corazon(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo="normal"):
        super().__init__(); 
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        color = COLOR_CORAZON
        pygame.draw.circle(self.image, color, (7,7), 7); pygame.draw.circle(self.image, color, (17,7), 7)
        pygame.draw.polygon(self.image, color, [(0,9), (24,9), (12,24)])
        self.rect = self.image.get_rect(center=(x, y))
    def update(self, *args, **kwargs):
        self.rect.y += 3; 
        if self.rect.top > ALTO: self.kill()

class Barrera(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(); self.hp = BARRERA_VIDA_MAX
        self.image = pygame.Surface((BARRERA_ANCHO, BARRERA_ALTO), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.frame = 0
        self.last_anim = 0
        self.actualizar_aspecto()
        
    def update(self, *args, **kwargs):
        now = pygame.time.get_ticks()
        if now - self.last_anim > 120: # 120ms por frame
            self.last_anim = now
            self.frame = 1 - self.frame
            self.actualizar_aspecto()

    def actualizar_aspecto(self):
        p = self.hp/BARRERA_VIDA_MAX
        self.image.fill((0,0,0,0)) # Limpiar
        
        color = COLOR_BARRERA_LLENA
        if p < 0.33: color = COLOR_BARRERA_BAJA
        elif p < 0.66: color = COLOR_BARRERA_MEDIA
        
        # Efecto "Mágico" Base
        pygame.draw.rect(self.image, (*color, 200), [0, 0, BARRERA_ANCHO, BARRERA_ALTO], border_radius=3)
        pygame.draw.rect(self.image, (255, 255, 255, 150), [0, 0, BARRERA_ANCHO, BARRERA_ALTO], 1, border_radius=3)

        # Efecto Eléctrico Animado
        c_rayo = (220, 255, 255, 255)
        points = []
        if self.frame == 0:
            points = [(2, BARRERA_ALTO//2), (10, 2), (20, BARRERA_ALTO-2), (30, 2), (38, BARRERA_ALTO//2)]
        else:
             points = [(2, BARRERA_ALTO//2), (12, BARRERA_ALTO-2), (22, 2), (32, BARRERA_ALTO-2), (38, BARRERA_ALTO//2)]
        
        if len(points) > 1:
            pygame.draw.lines(self.image, c_rayo, False, points, 1)

    def recibir_danio(self):
        self.hp -= 1
        if self.hp <= 0:
            self.kill()
        else:
            if isinstance(self, BossSNAKE):
                self.anim_phase = "danyo"
                self.anim_timer = 0
            self.actualizar_aspecto()

class Charco(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo):
        super().__init__()
        self.tipo = tipo
        self.radio = 45 # Radio del charco
        self.image = pygame.Surface((self.radio*2, self.radio*2), pygame.SRCALPHA)
        
        color = NEGRO
        if tipo == "hielo": color = (*AZUL_CONGELADO, 140)
        elif tipo == "veneno": color = (*VERDE_VENENO, 140)
        elif tipo == "fuego": color = (*BOSS_FUEGO_COLOR, 140)
        
        pygame.draw.circle(self.image, color, (self.radio, self.radio), self.radio)
        pygame.draw.circle(self.image, BLANCO, (self.radio, self.radio), self.radio, 2)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.creacion = pygame.time.get_ticks()
        self.duracion = DURACION_CHARCO

    def update(self, *args, **kwargs):
        if pygame.time.get_ticks() - self.creacion > self.duracion:
            self.kill()

class TextoFlotante(pygame.sprite.Sprite):
    def __init__(self, x, y, texto, color=BLANCO, size=20):
        super().__init__()
        self.fuente = pygame.font.SysFont("Arial", size, True)
        self.image = self.fuente.render(str(texto), True, color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = -2.0
        self.alpha = 255

    def update(self, *args, **kwargs):
        self.rect.y += self.vy
        self.alpha -= 5
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.alpha)

class CriticoHit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.fuente = pygame.font.SysFont("Arial", 24, True)
        self.image = self.fuente.render("X", True, ORO_PODER)
        self.rect = self.image.get_rect(center=(x, y))
        self.fin = pygame.time.get_ticks() + 600
    
    def update(self, **kwargs):
        if pygame.time.get_ticks() > self.fin:
            self.kill()

class RayoImpacto(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x, self.y = x, y
        self.creacion = pygame.time.get_ticks()
        self.duracion = 200
        self.radius = 5
        self.max_radius = 30
        
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
    
    def update(self, **kwargs):
        ahora = pygame.time.get_ticks()
        pasado = ahora - self.creacion
        
        if pasado > self.duracion:
            self.kill()
            return
        
        ratio = pasado / self.duracion
        self.radius = min(self.max_radius * ratio, self.max_radius)
        alpha = int(255 * (1 - ratio))
        
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (255, 200, 255, alpha), (30, 30), int(self.radius))
        pygame.draw.circle(self.image, (255, 255, 255, alpha), (30, 30), int(self.radius * 0.5), 2)

class EscudoEspecial(pygame.sprite.Sprite):
    def __init__(self, mago):
        super().__init__()
        self.mago = mago
        self.ancho = 40
        self.alto = 40
        self.rect = pygame.Rect(0, 0, self.ancho, self.alto)
        self.rebotado = False
        self.cooldown_reaparecer = 16000
        self.timer_desaparicion = 0
        self.timer_reaparicion = 0
        self.activo = False
        self.imagen_escudo = self.crear_imagen_escudo()
        self.actualizar_posicion()

    def crear_imagen_escudo(self):
        imagen = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        pygame.draw.arc(imagen, AZUL_MAGO, [5, 5, 30, 30], 0, math.pi, 3)
        pygame.draw.arc(imagen, CIAN_MAGIA, [10, 10, 20, 20], 0, math.pi, 2)
        return imagen

    def actualizar_posicion(self):
        self.rect.midbottom = (self.mago.rect.centerx, self.mago.rect.top - 10)

    def activar(self):
        self.activo = True
        self.rebotado = False
        self.timer_desaparicion = 0
        self.image = self.imagen_escudo

    def desactivar(self):
        self.activo = False
        self.rebotado = True
        self.timer_reaparicion = pygame.time.get_ticks() + self.cooldown_reaparecer
        self.image = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)

    def update(self, *args, **kwargs):
        self.actualizar_posicion()
        
        if not self.activo:
            ahora = pygame.time.get_ticks()
            if ahora > self.timer_reaparicion:
                self.activar()

class RayoPlayer(pygame.sprite.Sprite):
    def __init__(self, x, y, angulo=-90, duracion=1000, color=(255, 0, 150), mago=None, potencia=1.0, longitud_max=600, danio=None, rebotes=0, es_homing=False):
        super().__init__()
        self.origen_x = x
        self.origen_y = y
        self.angulo = angulo
        self.duracion = duracion
        self.creacion = pygame.time.get_ticks()
        self.color = color
        self.potencia = potencia
        self.longitud_max = longitud_max
        self.mago = mago
        
        if danio is not None:
            self.danio = danio
        else:
            self.danio = (0.5 if mago else 150) * (0.3 + (0.7 * potencia))
        
        self.es_rayo = True
        self.es_rayo_player = True
        # Guardar daño base antes de la reducción contra bosses
        self.danio_original = self.danio
        self.penetracion = 999
        self.enemigos_atacados = []
        
        # SINERGIAS: Rebotes y Homing
        self.rebotes = rebotes
        self.es_homing = es_homing
        
        self.velocidad_rayo = 800
        self.expansion_completa = False
        self.tiempo_expansion_completa = None
        
        # Crear superficie del tamaño exacto que necesitamos
        self.image = pygame.Surface((100, longitud_max + 10), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        # El rect debe estar posicionado para que el rayo salga desde (x, y) hacia arriba
        self.rect.left = x - 50
        self.rect.top = y - longitud_max

    def update(self, *args, **kwargs):
        ahora = pygame.time.get_ticks()
        pasado = ahora - self.creacion
        
        if not self.expansion_completa:
            self.longitud_actual = min(pasado * self.velocidad_rayo / 1000, self.longitud_max)
            if self.longitud_actual >= self.longitud_max:
                self.expansion_completa = True
                self.tiempo_expansion_completa = ahora
        else:
            self.longitud_actual = self.longitud_max
        
        if self.expansion_completa:
            tiempo_desde_expansion = ahora - self.tiempo_expansion_completa
            if tiempo_desde_expansion > 200:
                ratio_desvanecimiento = min((tiempo_desde_expansion - 200) / 300, 1.0)
                if ratio_desvanecimiento >= 1.0:
                    self.kill()
                    return
            else:
                ratio_desvanecimiento = 0.0
        else:
            ratio_desvanecimiento = 0.0

        self.image.fill((0, 0, 0, 0))
        
        ancho_base = int(40 * self.potencia)
        pulso = math.sin(ahora * 0.03) * 10
        ancho = ancho_base * (1 - ratio_desvanecimiento) + pulso
        if ancho < 5: ancho = 5

        # Dibujar el rayo desde el origen hacia arriba
        # El origen está en la parte inferior-central de la superficie
        inicio_x = 50  # Centro horizontal de la superficie (100px de ancho)
        inicio_y = self.longitud_actual  # El inicio se mueve con la longitud
        fin_x = 50
        fin_y = 0  # Fin en la parte superior

        # Dibujar el rayo
        alpha_base = int(220 * (1 - ratio_desvanecimiento))
        for i in range(4):
            a = int(ancho / (i + 1))
            alpha = int(alpha_base / (i + 1))
            pygame.draw.line(self.image, (*self.color, alpha), (inicio_x, inicio_y), (fin_x, fin_y), a)
        
        # Núcleo blanco
        pygame.draw.line(self.image, (255, 255, 255, int(255 * (1 - ratio_desvanecimiento))), 
                        (inicio_x, inicio_y), (fin_x, fin_y), int(ancho/4))
        
        # Actualizar rect para colisiones - el rayo está entre y=y-longitud e y=y
        self.rect.left = self.origen_x - 50
        self.rect.top = self.origen_y - self.longitud_actual
        self.rect.width = 100
        self.rect.height = self.longitud_actual

class LaserSNAKE(pygame.sprite.Sprite):
    def __init__(self, x, y, angulo, duracion=2000, color=(255, 0, 100)):
        super().__init__()
        self.x, self.y = x, y
        self.angulo = angulo # 90 es hacia abajo
        self.duracion = duracion
        self.creacion = pygame.time.get_ticks()
        self.color = color
        self.ancho_max = 40
        self.image = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.puntos_colision = []

    def update(self, *args, **kwargs):
        ahora = pygame.time.get_ticks()
        pasado = ahora - self.creacion
        if pasado > self.duracion:
            self.kill()
            return

        # Efecto de pulso y desvanecimiento
        ratio = pasado / self.duracion
        self.image.fill((0, 0, 0, 0))
        
        # Calcular ancho del láser (pulso)
        pulso = math.sin(ahora * 0.02) * 5
        ancho = self.ancho_max * (1 - ratio) + pulso
        if ancho < 5: ancho = 5

        # Dibujar rayo
        rad = math.radians(self.angulo)
        fin_x = self.x + math.cos(rad) * 1000
        fin_y = self.y + math.sin(rad) * 1000

        # Dibujar múltiples capas para efecto neon
        for i in range(3):
            a = int(ancho / (i + 1))
            alpha = int(200 * (1 - ratio))
            pygame.draw.line(self.image, (*self.color, alpha), (self.x, self.y), (fin_x, fin_y), a)
        
        # El núcleo del láser es blanco
        pygame.draw.line(self.image, (255, 255, 255, int(255 * (1-ratio))), (self.x, self.y), (fin_x, fin_y), int(ancho/4))

class AdvertenciaLaser(pygame.sprite.Sprite):
    """Muestra una línea de advertencia antes de que salga el láser"""
    def __init__(self, x, y, angulo, duracion_ms=1500):
        super().__init__()
        self.x = x
        self.y = y
        self.angulo = angulo
        self.duracion_total = duracion_ms
        self.tiempo_inicio = pygame.time.get_ticks()
        self.parpadeo_rapido = False
        
        # Crear imagen grande para la línea
        self.image = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        
    def update(self, *args, **kwargs):
        tiempo_actual = pygame.time.get_ticks()
        tiempo_transcurrido = tiempo_actual - self.tiempo_inicio
        tiempo_restante = self.duracion_total - tiempo_transcurrido
        
        if tiempo_restante <= 0:
            self.kill()
            return
            
        # Limpiar imagen
        self.image.fill((0, 0, 0, 0))
        
        # Calcular punto final de la línea
        rad = math.radians(self.angulo)
        fin_x = self.x + math.cos(rad) * 1000
        fin_y = self.y + math.sin(rad) * 1000
        
        # Progreso de la advertencia (0 a 1)
        progreso = tiempo_transcurrido / self.duracion_total
        
        # Parpadeo acelerado al final
        if tiempo_restante < 400:
            parpadeo = (tiempo_actual // 50) % 2 == 0
            alpha = 200 if parpadeo else 50
            grosor = 4
        elif tiempo_restante < 800:
            parpadeo = (tiempo_actual // 100) % 2 == 0
            alpha = 150 if parpadeo else 80
            grosor = 3
        else:
            parpadeo = (tiempo_actual // 150) % 2 == 0
            alpha = 120 if parpadeo else 60
            grosor = 2
        
        # Dibujar línea de advertencia roja punteada
        color = (255, 50, 50)  # Rojo para láseres
        
        # Línea principal punteada
        distancia_total = math.hypot(fin_x - self.x, fin_y - self.y)
        segmentos = int(distancia_total / 20)
        for i in range(segmentos):
            inicio_seg = i / segmentos
            fin_seg = (i + 0.5) / segmentos
            x1 = self.x + (fin_x - self.x) * inicio_seg
            y1 = self.y + (fin_y - self.y) * inicio_seg
            x2 = self.x + (fin_x - self.x) * fin_seg
            y2 = self.y + (fin_y - self.y) * fin_seg
            pygame.draw.line(self.image, (*color, alpha), (x1, y1), (x2, y2), grosor)
        
        # Círculo en el origen
        pygame.draw.circle(self.image, (*color, alpha + 50), (int(self.x), int(self.y)), 8 + int(progreso * 4))
        pygame.draw.circle(self.image, (255, 200, 200, alpha), (int(self.x), int(self.y)), 4)
        
        # Texto de advertencia "!" flotante cerca del origen
        if parpadeo and tiempo_restante < 1000:
            # Pequeño indicador de exclamación
            offset_x = math.sin(tiempo_actual * 0.01) * 10
            excla_x = int(self.x + offset_x)
            excla_y = int(self.y - 25)
            pygame.draw.circle(self.image, (255, 0, 0, 255), (excla_x, excla_y - 5), 3)
            pygame.draw.rect(self.image, (255, 0, 0, 255), (excla_x - 1, excla_y, 2, 8))

class BossSNAKE(Boss):
    def __init__(self, dificultad=MODO_NORMAL, nivel=10):
        super().__init__(nivel=nivel, dificultad=dificultad, variante=BOSS_TIPO_SNAKE)
        self.hp_max = HP_BOSS_SNAKE
        if dificultad == MODO_DIFICIL: self.hp_max *= 1.5
        self.hp = self.hp_max
        self.color_base = (100, 50, 150)
        self.timer_mov_erratico = 0
        self.ultimo_laser = 0
        self.laser_activo = False
        self.segunda_fase = False
        self.angulo_SNAKE = 0

        # Posiciones de ojos (relativas al sprite)
        self.ojo_izq_pos = (130, 80)
        self.ojo_der_pos = (175, 80)

        # Ataque de embestida (solo difícil)
        self.embestiendo = False
        self.timer_advertencia = 0
        self.direccion_embestida = None
        self.velocidad_embestida = 12  # REDUCIDO: De 16 a 12 para ser más esquivable y menos espacio
        self.ultimo_ataque_embestida = -10000
        self.cooldown_embestida = 3000  # AUMENTADO: De 2500 a 3000ms para menos spam
        self.distancia_min_embestida = 350  # AUMENTADO: De 300 a 350, no embestir si está muy cerca
        self.distancia_max_embestida = 600  # NUEVO: No embestir si está muy lejos
        self.tiempo_advertencia_ms = 2500  # NUEVO: 2.5 segundos de advertencia (antes era 1500)
        self.distancia_embestida_maxima = 400  # Máxima distancia que recorre en embestida
        
        # Control de proximidad al jugador (máximo 1 segundo cerca)
        self.tiempo_cerca_jugador = 0
        self.ultimo_tiempo_cerca = 0
        self.distancia_cerca = 200  # AUMENTADO: De 150 a 200
        self.max_tiempo_cerca = 1000  # REDUCIDO: De 1.5s a 1.0s
        self.forzar_alejamiento = False
        
        # Aviso para láseres
        self.advertencia_laser_activa = False
        self.tiempo_advertencia_laser = 0
        self.duracion_advertencia_laser = 1500  # 1.5 segundos de aviso
        self.advertencias_laser_grupo = pygame.sprite.Group()  # Grupo para las líneas de advertencia
        self.angulos_laser_pendientes = []  # Guardar ángulos para las advertencias
        
        # Inicializar posiciones de láser guardadas
        self.laser_pos_x = 0
        self.laser_pos_y = 0
        self.laser_angulo = 0
        self.laser_ojo_izq_x = 0
        self.laser_ojo_izq_y = 0
        self.laser_ojo_der_x = 0
        self.laser_ojo_der_y = 0
        
        # Inicializar posición inicial de embestida
        self.pos_inicial_embestida = (0, 0)

        # Variables de animación
        self.anim_timer = 0
        self.anim_phase = "idle"
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.glow_intensity = 0
        self.float_offset = 0
        
    def cargar_imagen(self):
        imagen_personalizada = None
        try:
            ruta_img = resolver_ruta("assets/boss_snake.png")
            if os.path.exists(ruta_img):
                imagen_personalizada = pygame.image.load(ruta_img).convert_alpha()
                print(f"Boss SNAKE: Imagen personalizada cargada desde {ruta_img}")
        except Exception as e:
            print(f"Boss SNAKE: No se pudo cargar imagen personalizada: {e}")

        if imagen_personalizada:
            self.image_original = pygame.Surface((200, 180), pygame.SRCALPHA)
            img_scaled = pygame.transform.scale(imagen_personalizada, (200, 180))
            self.image_original.blit(img_scaled, (0, 0))
        else:
            self.image_original = pygame.Surface((200, 180), pygame.SRCALPHA)
            for i in range(5, 0, -1):
                alpha = 150 + (i * 20)
                size = 50 + (i * 12)
                y_offset = 90 - (i * 3)
                color_seg = (max(30, self.color_base[0] - i * 15), max(20, self.color_base[1] - i * 10), max(40, self.color_base[2] - i * 20))
                pygame.draw.ellipse(self.image_original, (*color_seg, alpha), [i * 25, y_offset, size, size - 20])

            pygame.draw.ellipse(self.image_original, self.color_base, [80, 50, 120, 90])
            pygame.draw.ellipse(self.image_original, (80, 40, 100), [90, 60, 100, 70])

            for i in range(3):
                for j in range(2):
                    pygame.draw.circle(self.image_original, (max(50, self.color_base[0] - 20), max(30, self.color_base[1] - 15), max(60, self.color_base[2] - 20)),
                                      (120 + j * 30, 75 + i * 20), 8)

            self.ojo_izq_pos = (130, 80)
            self.ojo_der_pos = (175, 80)
            pygame.draw.circle(self.image_original, (255, 200, 50), self.ojo_izq_pos, 18)
            pygame.draw.circle(self.image_original, (255, 200, 50), self.ojo_der_pos, 18)
            pygame.draw.circle(self.image_original, (255, 0, 0), self.ojo_izq_pos, 12)
            pygame.draw.circle(self.image_original, (255, 0, 0), self.ojo_der_pos, 12)
            pygame.draw.rect(self.image_original, NEGRO, [self.ojo_izq_pos[0] - 2, self.ojo_izq_pos[1] - 6, 4, 12])
            pygame.draw.rect(self.image_original, NEGRO, [self.ojo_der_pos[0] - 2, self.ojo_der_pos[1] - 6, 4, 12])

            pygame.draw.polygon(self.image_original, (40, 10, 10), [(160, 95), (200, 100), (195, 120), (155, 115)])
            pygame.draw.polygon(self.image_original, BLANCO, [(165, 100), (170, 125), (175, 100)])
            pygame.draw.polygon(self.image_original, BLANCO, [(180, 100), (185, 125), (190, 100)])

            pygame.draw.line(self.image_original, (200, 50, 50), (200, 115), (230, 110), 3)
            pygame.draw.line(self.image_original, (200, 50, 50), (230, 110), (240, 100), 2)
            pygame.draw.line(self.image_original, (200, 50, 50), (230, 110), (240, 120), 2)

        self.image_advertencia = self.image_original.copy()
        pygame.draw.polygon(self.image_advertencia, ROJO_VIDA, [(100, 10), (130, 50), (70, 50)])
        pygame.draw.polygon(self.image_advertencia, NARANJA_FUEGO, [(100, 15), (125, 45), (75, 45)])

        self.image_ataque = self.image_original.copy()
        self.image_muerte = self.image_original.copy()

        self.anim_timer = 0
        self.anim_phase = "idle"
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.glow_intensity = 0
        self.float_offset = 0

    def animacion_idle(self):
        efecto = self.image_original.copy()
        
        self.float_offset += 0.08
        float_y = int(math.sin(self.float_offset) * 5)
        
        if float_y != 0:
            temp = pygame.Surface((200, 180 + abs(float_y) * 2), pygame.SRCALPHA)
            temp.blit(efecto, (0, abs(float_y) if float_y > 0 else 0))
            efecto = temp
        
        self.anim_timer += 1
        breath = 1.0 + math.sin(self.anim_timer * 0.1) * 0.03
        efecto = pygame.transform.scale(efecto, (int(200 * breath), int(180 / breath)))
        
        if self.segunda_fase:
            tint = (255, 100 + int(math.sin(self.anim_timer * 0.2) * 50), 100)
            efecto = self.aplicar_tint(efecto, tint)
        
        return efecto

    def animacion_ataque(self):
        efecto = self.image_original.copy()
        
        stretch = 1.15
        efecto = pygame.transform.scale(efecto, (int(200 * stretch), int(180 / stretch)))
        
        self.glow_intensity = min(1.0, self.glow_intensity + 0.2)
        if self.glow_intensity > 0:
            efecto = self.aplicar_glow(efecto, (255, 100, 50), self.glow_intensity)
        
        return efecto

    def animacion_embestida(self):
        efecto = self.image_original.copy()
        
        stretch = 1.4
        squash = 0.7
        efecto = pygame.transform.scale(efecto, (int(200 * stretch), int(180 * squash)))
        
        efecto = self.aplicar_glow(efecto, (255, 50, 0), 0.8)
        
        shake = random.randint(-3, 3)
        temp = pygame.Surface((200 + abs(shake) * 2, 180), pygame.SRCALPHA)
        temp.blit(efecto, (abs(shake) if shake < 0 else 0, 0))
        efecto = temp
        
        return efecto

    def animacion_danyo(self):
        efecto = self.image_original.copy()

        flash = (255, 255, 255)
        return self.aplicar_tint(efecto, flash)

    def animacion_muerte(self):
        efecto = self.image_original.copy()

        shrink = max(0.1, 1.0 - (self.anim_timer * 0.05))
        try:
            efecto = pygame.transform.scale(efecto, (int(200 * shrink), int(180 * shrink)))
        except:
            efecto = self.image_original.copy()

        fade = 1.0 - shrink
        if fade > 0:
            try:
                efecto.set_alpha(int(255 * (1 - fade)))
            except:
                pass

        if self.anim_timer % 4 < 2:
            efecto = self.aplicar_tint(efecto, (255, 0, 0))

        return efecto

    def animacion_advertencia(self):
        efecto = self.image_advertencia.copy()

        blink_speed = 0.5 + math.sin(self.anim_timer * 0.3) * 0.3
        efecto.set_alpha(int(150 + blink_speed * 100))

        pulse = 1.0 + math.sin(self.anim_timer * 0.5) * 0.05
        efecto = pygame.transform.scale(efecto, (int(200 * pulse), int(180 * pulse)))

        return efecto

    def obtener_imagen_animada(self, phase=None):
        if phase:
            self.anim_phase = phase
        
        if self.anim_phase == "ataque":
            img = self.animacion_ataque()
        elif self.anim_phase == "embestida":
            img = self.animacion_embestida()
        elif self.anim_phase == "danyo":
            img = self.animacion_danyo()
            self.anim_phase = "idle"
        elif self.anim_phase == "muerte":
            img = self.animacion_muerte()
        else:
            img = self.animacion_idle()
            if self.anim_timer > 100:
                self.anim_timer = 0
        
        if self.anim_phase not in ["danyo", "muerte"]:
            self.anim_phase = "idle"
        
        return img
    
    def update(self, *args, **kwargs):
        ahora = kwargs.get('ahora', pygame.time.get_ticks())
        grupo_s = kwargs.get('grupo_s', None)
        grupo_b = kwargs.get('grupo_b', None)
        mago = kwargs.get('mago', None)

        if self.destruyendo or self.congelado:
            # Limpiar advertencias de láser al morir
            for adv in self.advertencias_laser_grupo:
                adv.kill()
            self.advertencias_laser_grupo.empty()
            self.image = self.obtener_imagen_animada("muerte")
            super().update(*args, **kwargs)
            return

        if self.hp < self.hp_max * 0.3 and not self.segunda_fase:
            self.segunda_fase = True
            self.color_base = (180, 40, 40)
            self.cargar_imagen()

        if self.embestiendo:
            self.pos_x += self.direccion_embestida[0] * self.velocidad_embestida
            self.pos_y += self.direccion_embestida[1] * self.velocidad_embestida
            self.rect.x, self.rect.y = int(self.pos_x), int(self.pos_y)
            self.image = self.obtener_imagen_animada("embestida")
            
            # Verificar si recorrió la distancia máxima de embestida
            distancia_recorrida = math.hypot(self.pos_x - self.pos_inicial_embestida[0], 
                                            self.pos_y - self.pos_inicial_embestida[1])
            
            if self.rect.right < 0 or self.rect.left > ANCHO or self.rect.top > ALTO or distancia_recorrida > self.distancia_embestida_maxima:
                self.embestiendo = False
                self.direccion_embestida = None
            return

        if self.dificultad == MODO_DIFICIL and self.timer_advertencia > 0:
            if ahora > self.timer_advertencia:
                self.timer_advertencia = 0
                self.image = self.image_original.copy()
                dx = mago.rect.centerx - self.rect.centerx
                dy = mago.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    # Calcular dirección hacia donde está mirando el jugador (predicción)
                    # En lugar de ir directo al jugador, va a donde el jugador estaba cuando empezó la carga
                    self.direccion_embestida = (dx / dist, dy / dist)
                    self.embestiendo = True
                    self.ultimo_ataque_embestida = ahora
            else:
                # MEJORADO: Parpadeo más rápido e intenso durante la carga
                tiempo_restante = self.timer_advertencia - ahora
                # Cuando falta menos tiempo, parpadea más rápido
                if tiempo_restante < 500:
                    velocidad_parpadeo = 100  # Muy rápido al final
                elif tiempo_restante < 1500:
                    velocidad_parpadeo = 200  # Rápido
                else:
                    velocidad_parpadeo = 300  # Normal al inicio
                    
                if (ahora // velocidad_parpadeo) % 2 == 0:
                    self.image = self.obtener_imagen_animada("ataque")
                else:
                    self.image = self.obtener_imagen_animada("advertencia")
            return

        # Solo puede hacer ataque cargado si está suficientemente arriba (pos_y < 180)
        puede_embestir = self.pos_y < 180
        
        if self.dificultad == MODO_DIFICIL and self.timer_advertencia == 0 and not self.embestiendo and puede_embestir:
            ahora = pygame.time.get_ticks()
            dx = mago.rect.centerx - self.rect.centerx
            dy = mago.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            # Verificar que esté a distancia apropiada: ni muy cerca ni muy lejos
            if random.random() < 0.002 and ahora - self.ultimo_ataque_embestida > self.cooldown_embestida and self.distancia_min_embestida < dist < self.distancia_max_embestida:
                self.timer_advertencia = ahora + self.tiempo_advertencia_ms
                # Guardar posición inicial para limitar distancia de embestida
                self.pos_inicial_embestida = (self.pos_x, self.pos_y)

        # Calcular distancia al jugador
        distancia = 9999
        if mago:
            dx = mago.rect.centerx - self.rect.centerx
            dy = mago.rect.centery - self.rect.centery
            distancia = math.hypot(dx, dy)
            
            # Control de proximidad: no más de 1.5 segundos cerca
            if distancia < self.distancia_cerca:
                if self.ultimo_tiempo_cerca == 0:
                    self.ultimo_tiempo_cerca = ahora
                else:
                    self.tiempo_cerca_jugador = ahora - self.ultimo_tiempo_cerca
                    
                if self.tiempo_cerca_jugador >= self.max_tiempo_cerca:
                    self.forzar_alejamiento = True
            else:
                # Resetear contador cuando se aleja
                self.tiempo_cerca_jugador = 0
                self.ultimo_tiempo_cerca = 0
                self.forzar_alejamiento = False
        
        # Movimiento normal o alejamiento forzado
        if self.forzar_alejamiento and mago:
            # Alejarse muy rápidamente del jugador
            dx = self.rect.centerx - mago.rect.centerx
            dy = self.rect.centery - mago.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                # AUMENTADO: Velocidad de alejamiento de 8 a 15
                self.pos_x += (dx / dist) * 15
                self.pos_y += (dy / dist) * 15
            
            # Dejar de forzar alejamiento cuando esté lo suficientemente lejos
            if distancia >= self.distancia_cerca * 1.5:
                self.forzar_alejamiento = False
                self.tiempo_cerca_jugador = 0
                self.ultimo_tiempo_cerca = 0
        else:
            # Movimiento normal
            self.angulo_SNAKE += 0.05
            self.pos_x += math.sin(self.angulo_SNAKE) * 3
            self.pos_y += math.cos(self.angulo_SNAKE * 0.5) * 1.5

        if self.pos_x < 30: self.vx = abs(self.vx)
        if self.pos_x > ANCHO - 230: self.vx = -abs(self.vx)
        if self.pos_y < 20: self.vy = abs(self.vy)
        # Limitar al boss a la parte superior de la pantalla (máximo Y = 200)
        if self.pos_y > 200: 
            self.pos_y = 200
            self.vy = -abs(self.vy)

        self.image = self.obtener_imagen_animada("idle")

        # BossSNAKE no usa el ataque cargado de bomba de la clase Boss
        # Solo llamamos a update de Sprite, no de Boss
        pygame.sprite.Sprite.update(self, *args, **kwargs)

        if self.segunda_fase:
            # Fase 2: Lluvia de proyectiles en abanico
            if ahora % 800 < 50:
                 for a in range(45, 135, 15):
                     rad = math.radians(a)
                     vx, vy = math.cos(rad) * 6, math.sin(rad) * 6
                     p = Proyectil(self.rect.centerx, self.rect.bottom, vx, vy, 1, es_enemigo=True, color=(255, 50, 50))
                     grupo_s.add(p); grupo_b.add(p)
        else:
            # Fase 1: Láseres con aviso previo visual
            if not self.advertencia_laser_activa and ahora - self.ultimo_laser > 5000:
                # Iniciar advertencia 1.5 segundos antes del láser
                self.advertencia_laser_activa = True
                self.tiempo_advertencia_laser = ahora + self.duracion_advertencia_laser
                self.tipo_laser_pendiente = random.choice(["boca", "ojos"])
                
                # Crear líneas de advertencia visuales inmediatamente
                # Guardar posiciones exactas para que el láser salga exactamente donde se muestra la advertencia
                if 0 < self.rect.centerx < ANCHO and 0 < self.rect.centery < ALTO:
                    if self.tipo_laser_pendiente == "boca":
                        # Láser desde la boca apuntando al jugador
                        dx = mago.rect.centerx - self.rect.centerx
                        dy = mago.rect.centery - self.rect.centery
                        ang = math.degrees(math.atan2(dy, dx))
                        # Guardar posición y ángulo exactos
                        self.laser_pos_x = self.rect.centerx
                        self.laser_pos_y = self.rect.centery + 40
                        self.laser_angulo = ang
                        adv = AdvertenciaLaser(self.laser_pos_x, self.laser_pos_y, self.laser_angulo, self.duracion_advertencia_laser)
                        self.advertencias_laser_grupo.add(adv)
                        grupo_s.add(adv)
                    else:
                        # Dos láseres desde los ojos en ángulos fijos
                        ojo_izq_x = self.rect.x + self.ojo_izq_pos[0]
                        ojo_izq_y = self.rect.y + self.ojo_izq_pos[1]
                        ojo_der_x = self.rect.x + self.ojo_der_pos[0]
                        ojo_der_y = self.rect.y + self.ojo_der_pos[1]
                        
                        # Guardar posiciones exactas
                        self.laser_ojo_izq_x = ojo_izq_x
                        self.laser_ojo_izq_y = ojo_izq_y
                        self.laser_ojo_der_x = ojo_der_x
                        self.laser_ojo_der_y = ojo_der_y
                        
                        if 0 < ojo_izq_x < ANCHO and 0 < ojo_izq_y < ALTO:
                            adv1 = AdvertenciaLaser(ojo_izq_x, ojo_izq_y, 70, self.duracion_advertencia_laser)
                            self.advertencias_laser_grupo.add(adv1)
                            grupo_s.add(adv1)
                        if 0 < ojo_der_x < ANCHO and 0 < ojo_der_y < ALTO:
                            adv2 = AdvertenciaLaser(ojo_der_x, ojo_der_y, 110, self.duracion_advertencia_laser)
                            self.advertencias_laser_grupo.add(adv2)
                            grupo_s.add(adv2)
            
            # Actualizar y lanzar láser cuando termine la advertencia
            self.advertencias_laser_grupo.update()
            
            if self.advertencia_laser_activa:
                if ahora >= self.tiempo_advertencia_laser:
                    # Lanzar el láser ahora
                    self.advertencia_laser_activa = False
                    self.ultimo_laser = ahora
                    
                    # Usar las posiciones guardadas (no recalcular) para que coincida exactamente con la advertencia
                    if self.tipo_laser_pendiente == "boca":
                        # Láser desde la boca usando posición guardada
                        l = LaserSNAKE(self.laser_pos_x, self.laser_pos_y, self.laser_angulo)
                        grupo_s.add(l)
                    else:
                        # Dos láseres desde los ojos usando posiciones guardadas
                        if 0 < self.laser_ojo_izq_x < ANCHO and 0 < self.laser_ojo_izq_y < ALTO:
                            l1 = LaserSNAKE(self.laser_ojo_izq_x, self.laser_ojo_izq_y, 70)
                            grupo_s.add(l1)
                        if 0 < self.laser_ojo_der_x < ANCHO and 0 < self.laser_ojo_der_y < ALTO:
                            l2 = LaserSNAKE(self.laser_ojo_der_x, self.laser_ojo_der_y, 110)
                            grupo_s.add(l2)
                else:
                    # Durante la advertencia, el boss brilla ligeramente en rojo
                    tiempo_restante = self.tiempo_advertencia_laser - ahora
                    # Efecto de brillo rojo creciente
                    brillo = int(50 + (1 - tiempo_restante / self.duracion_advertencia_laser) * 100)
                    tinte = (255, 100, 100)
                    temp = self.image.copy()
                    overlay = pygame.Surface(temp.get_size(), pygame.SRCALPHA)
                    overlay.fill((*tinte, brillo))
                    temp.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                    self.image = temp
