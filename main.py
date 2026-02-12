import asyncio
import pygame
import sys
import random
import math
import os
import json
import webbrowser
import settings
from settings import *
from sprites import Mago, Monstruo, PowerUp, Barrera, Particula, Boss, Corazon, ParticulaAmbiental, Proyectil, OrbeXP, Rayo, Orbital, Charco, BossSNAKE, LaserSNAKE, EscudoEspecial, CriticoHit, RayoImpacto, TextoFlotante

# Mixer pre-init ajustado
pygame.mixer.pre_init(44100, -16, 2, 2048)


# --- HELPER DE COLISION ---
def collided_hitbox(left, right):
    rect_left = getattr(left, 'hitbox', left.rect)
    rect_right = getattr(right, 'hitbox', right.rect)
    return rect_left.colliderect(rect_right)

class GestorDatos:
    def __init__(self):
        self.archivo = resolver_ruta("save_data_rogue.json")
        self.es_web = sys.platform == 'emscripten'
        self.datos = {
            "cristales": 0,
            "high_score": 0,
            "boss_kills": 0,
            "mejoras": {
                "vida_base": 0,
                "danio_base": 0,
                "critico": 0,
            },
            "habilidades_especiales": {
                "MAGO": False,
                "piromante": False,
                "cazador": False,
                "el_loco": False,
                "snake": False
            }
        }
        self.cargar()

    def cargar(self):
        if self.es_web:
            try:
                import js
                data_str = js.localStorage.getItem("mago_defence_save")
                if data_str:
                    data = json.loads(data_str)
                    self._fusionar_datos(data)
            except: pass
        else:
            if os.path.exists(self.archivo):
                try:
                    with open(self.archivo, 'r') as f:
                        data = json.load(f)
                        self._fusionar_datos(data)
                except: pass

    def _fusionar_datos(self, data):
        for k, v in data.items():
            if k == "mejoras":
                for mk, mv in v.items():
                    if mk in self.datos["mejoras"]:
                        self.datos["mejoras"][mk] = mv
            elif k == "habilidades_especiales":
                if not isinstance(v, dict): continue
                for hk, hv in v.items():
                    if hk in self.datos["habilidades_especiales"]:
                        self.datos["habilidades_especiales"][hk] = hv
            else:
                self.datos[k] = v
        
        # Garantizar claves de desbloqueo
        for key in ["unlocked_loco", "unlocked_snake"]:
            if key not in self.datos:
                self.datos[key] = False

    def guardar(self):
        if self.es_web:
            try:
                import js
                js.localStorage.setItem("mago_defence_save", json.dumps(self.datos))
            except: pass
        else:
            try:
                with open(self.archivo, 'w') as f:
                    json.dump(self.datos, f)
            except: pass

    def reiniciar_datos(self):
        self.datos = {
            "cristales": 0, 
            "high_score": 0, 
            "boss_kills": 0, 
            "mejoras": {
                "vida_base": 0,
                "danio_base": 0,
                "critico": 0,
            },
            "habilidades_especiales": {
                "MAGO": False,
                "piromante": False,
                "cazador": False,
                "el_loco": False,
                "snake": False
            }
        }
        self.guardar()

    def agregar_cristales(self, cantidad):
        self.datos["cristales"] += cantidad
        self.guardar()

    def registrar_boss_kill(self):
        self.datos["boss_kills"] += 1
        self.guardar()
    
    def comprar_mejora(self, clave):
        if clave not in self.datos["mejoras"]: return False
        nivel_actual = self.datos["mejoras"][clave]
        info = PRECIOS_TIENDA[clave]
        if nivel_actual >= info["max"]: return False 
        
        # Usar precios personalizados si existen (ej: vida_base)
        if "precios_custom" in info:
            costo = info["precios_custom"][nivel_actual]
        else:
            costo = int(info["base"] * (FACTOR_COSTO_TIENDA ** nivel_actual))
        
        if self.datos["cristales"] >= costo:
            self.datos["cristales"] -= costo
            self.datos["mejoras"][clave] += 1
            self.guardar()
            return True
        return False
        
    def actualizar_highscore(self, score):
        if score > self.datos["high_score"]:
            self.datos["high_score"] = score
            self.guardar()

    def exportar_save_json(self):
        """Exporta los datos actuales a un archivo JSON."""
        data_str = json.dumps(self.datos, indent=4)
        if self.es_web:
            try:
                import js
                from js import document, Blob, URL
                
                # Crear un blob con los datos
                blob = Blob.new([data_str], { "type": "application/json" })
                url = URL.createObjectURL(blob)
                
                # Crear un link temporal
                a = document.createElement("a")
                a.style.display = "none"
                a.href = url
                a.download = "save_data_rogue.json"
                document.body.appendChild(a)
                a.click()
                
                # Limpiar
                document.body.removeChild(a)
                URL.revokeObjectURL(url)
                print("Exportación web iniciada.")
            except Exception as e:
                print(f"Error al exportar en web: {e}")
        else:
            try:
                import tkinter as tk
                from tkinter import filedialog
                import traceback
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                root.lift()
                ruta = filedialog.asksaveasfilename(defaultextension=".json", initialfile="save_data_rogue.json", title="Exportar Partida")
                root.destroy()
                if ruta:
                    with open(ruta, 'w') as f:
                        f.write(data_str)
                    print(f"Partida exportada a: {ruta}")
            except Exception as e:
                import traceback
                print(f"Error al exportar localmente: {e}")
                traceback.print_exc()
                # Fallback simple
                try:
                    with open("export_save_data.json", 'w') as f:
                        f.write(data_str)
                    print("Guardado en archivo de emergencia: export_save_data.json")
                except: pass

    def importar_save_json(self, juego_callback=None):
        """Importa datos desde un archivo JSON."""
        if self.es_web:
            try:
                import js
                from js import document, FileReader
                from pyodide.ffi import create_proxy
                
                def on_load(event):
                    try:
                        res = event.target.result
                        data = json.loads(res)
                        self._fusionar_datos(data)
                        self.guardar()
                        print("Datos importados con éxito en web.")
                        if juego_callback:
                            juego_callback()
                    except Exception as e:
                        print(f"Error al procesar archivo importado: {e}")

                # Proxies para Pyodide
                on_load_proxy = create_proxy(on_load)

                def on_change(event):
                    files = event.target.files
                    if files.length > 0:
                        reader = FileReader.new()
                        reader.onload = on_load_proxy
                        reader.readAsText(files.item(0))
                    # Limpiar proxy de change después de activarse
                    on_change_proxy.destroy()

                on_change_proxy = create_proxy(on_change)

                # Crear input file invisible
                file_input = document.createElement("input")
                file_input.type = "file"
                file_input.accept = ".json"
                file_input.style.display = "none"
                document.body.appendChild(file_input)
                
                file_input.onchange = on_change_proxy
                file_input.click()
                
                # Remover después de click para no ensuciar el DOM
                # (El diálogo de archivos ya está abierto)
                document.body.removeChild(file_input)
            except Exception as e:
                print(f"Error crítico al importar en web: {e}")
        else:
            try:
                import tkinter as tk
                from tkinter import filedialog
                import traceback
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                root.lift()
                ruta = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title="Importar Partida")
                root.destroy()
                if ruta and os.path.exists(ruta):
                    with open(ruta, 'r') as f:
                        data = json.load(f)
                        self._fusionar_datos(data)
                        self.guardar()
                        print(f"Partida importada desde: {ruta}")
                        if juego_callback:
                            juego_callback()
            except Exception as e:
                import traceback
                print(f"Error al importar localmente: {e}")
                traceback.print_exc()

class Juego:
    def __init__(self):
        pygame.init()
        try: pygame.mixer.init()
        except: pass

        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Mago Defence Roguelite")
        self.reloj = pygame.time.Clock()
        self.fuente_lg = pygame.font.SysFont("Arial", 48, True)
        self.fuente_md = pygame.font.SysFont("Arial", 26, True)
        self.fuente_sm = pygame.font.SysFont("Arial", 18, True)
        self.fuente_xs = pygame.font.SysFont("Arial", 16, True) 
        
        self.gestor_datos = GestorDatos()
        self.estado = ESTADO_MENU
        self.tiempo_estado_inicio = 0
        self.screen_shake = 0
        self.flash_alpha = 0
        self.notificacion_powerup = None
        self.tiempo_notificacion_powerup = 0

        self.juego_silenciado = False
        self.puntuacion, self.nivel, self.corriendo = 0, 1, True
        self.dificultad = MODO_NORMAL

        self.tipo_personaje_seleccionado = "MAGO"
        self.toques_activos = {}
        self.controles_tactiles_activados = self.detectar_dispositivo_tactil()

        self.es_dispositivo_tactil = self.controles_tactiles_activados
        self.ha_intentado_spawn_tesoro = False
        self.tiempo_sin_powerup = 0
        self.ultimo_spawn_powerup_cielo = 0

        self.confirmando_borrado = False
        self.timer_confirmacion_borrado = 0

        btn_size = 50  # Muy pequeño
        btn_y = ALTO - btn_size - 10
        spacing = 8

        self.rect_btn_izq = pygame.Rect(8, btn_y, btn_size, btn_size)
        self.rect_btn_der = pygame.Rect(8 + btn_size + spacing, btn_y, btn_size, btn_size)

        disparo_size = 55
        self.rect_btn_disparo = pygame.Rect(ANCHO - disparo_size - 8, ALTO - disparo_size - 8, disparo_size, disparo_size)

        # Variables para controles "escondidos" hasta tocar
        self.controles_ocultos = True
        self.zona_izq_activada = False
        self.zona_der_activada = False
        self.zona_disparo_activada = False

        # Zonas de toque más grandes que los botones visibles (hitbox)
        self.zona_toque_izq = pygame.Rect(0, ALTO - 150, ANCHO // 3, 150)
        self.zona_toque_der = pygame.Rect(ANCHO // 3 * 2, ALTO - 150, ANCHO // 3, 150)
        self.zona_toque_disparo = pygame.Rect(ANCHO - 180, ALTO - 150, 180, 150)

        self.rect_btn_toggle_tactil = pygame.Rect(ANCHO - 230, 20, 210, 45)
        self.rect_btn_mute = pygame.Rect(10, ALTO - 55, 50, 50)
        
        self.rect_btn_jugar = pygame.Rect(ANCHO//2 - 120, 340, 240, 60)
        self.rect_btn_diff_normal = pygame.Rect(ANCHO//2 - 120, 410, 115, 40)
        self.rect_btn_diff_dificil = pygame.Rect(ANCHO//2 + 5, 410, 115, 40)
        self.rect_btn_ir_tienda = pygame.Rect(ANCHO//2 - 80, 460, 160, 40)
        self.rect_btn_borrar = pygame.Rect(ANCHO - 140, ALTO - 40, 130, 30)

        self.rect_char_1 = pygame.Rect(ANCHO//2 - 370, ALTO//2 - 50, 170, 240)
        self.rect_char_2 = pygame.Rect(ANCHO//2 - 190, ALTO//2 - 50, 170, 240)
        self.rect_char_3 = pygame.Rect(ANCHO//2 - 10, ALTO//2 - 50, 170, 240)
        self.rect_char_4 = pygame.Rect(ANCHO//2 + 170, ALTO//2 - 50, 170, 240)
        self.rect_char_5 = pygame.Rect(ANCHO//2 + 350, ALTO//2 - 50, 170, 240)  # snake
        
        # Boton "Donar" en Tienda
        self.rect_btn_donacion = pygame.Rect(ANCHO//2 - 100, ALTO - 120, 200, 40)

        self.rect_mejora_1 = pygame.Rect(ANCHO//2 - 250, ALTO//2 - 50, 150, 200)
        self.rect_mejora_2 = pygame.Rect(ANCHO//2 - 75, ALTO//2 - 50, 150, 200)
        self.rect_mejora_3 = pygame.Rect(ANCHO//2 + 100, ALTO//2 - 50, 150, 200)
        
        self.rect_tienda_item_1 = pygame.Rect(ANCHO//2 - 250, 120, 160, 180)
        self.rect_tienda_item_2 = pygame.Rect(ANCHO//2 - 80, 120, 160, 180)
        self.rect_tienda_item_3 = pygame.Rect(ANCHO//2 + 90, 120, 160, 180)
        self.rect_btn_volver_tienda = pygame.Rect(ANCHO//2 - 100, ALTO - 60, 200, 40)
        
        # Botones de Exportar/Importar en Menú Principal (Movidos para evitar overlaps)
        btn_w_si = 130
        self.rect_btn_exportar = pygame.Rect(10, 140, btn_w_si, 35)
        self.rect_btn_importar = pygame.Rect(10, 185, btn_w_si, 35)
        
        # Botones del menú DEBUG
        btn_w, btn_h = 250, 40
        start_y = 150
        gap = 50
        self.rect_debug_toggle = pygame.Rect(ANCHO//2 - btn_w//2, start_y, btn_w, btn_h)
        self.rect_debug_god = pygame.Rect(ANCHO//2 - btn_w//2, start_y + gap*1, btn_w, btn_h)
        self.rect_debug_stats = pygame.Rect(ANCHO//2 - btn_w//2, start_y + gap*2, btn_w, btn_h)
        self.rect_debug_unlock = pygame.Rect(ANCHO//2 - btn_w//2, start_y + gap*3, btn_w, btn_h)
        self.rect_debug_powerups = pygame.Rect(ANCHO//2 - btn_w//2, start_y + gap*4, btn_w, btn_h)
        self.rect_debug_charges = pygame.Rect(ANCHO//2 - btn_w//2, start_y + gap*5, btn_w, btn_h)
        self.rect_debug_nivel_prev = pygame.Rect(ANCHO//2 - 160, start_y + gap*6, 60, btn_h)
        self.rect_debug_nivel_next = pygame.Rect(ANCHO//2 + 100, start_y + gap*6, 60, btn_h)
        self.rect_debug_cerrar = pygame.Rect(ANCHO//2 - 100, start_y + gap*7.5, 200, btn_h)
        
        # Botones directos a bosses
        btn_w_small = 120
        self.rect_debug_boss5 = pygame.Rect(ANCHO//2 - btn_w_small - 70, start_y + gap*8.8, btn_w_small, 35)
        self.rect_debug_boss10 = pygame.Rect(ANCHO//2 + 70, start_y + gap*8.8, btn_w_small, 35)

        self.snd_disparo, self.snd_muerte, self.snd_powerup, self.snd_nivel = None, None, None, None
        self.cargar_recursos()
        self.fondo_img = None
        self.cargar_fondo()
        self.boss_instancia = None
        self.inicializar_grupos()
        
        self.fondo_cache = None     
        self.niebla_capas = []
        for i in range(3):
            self.niebla_capas.append({
                'x': random.randint(0, ANCHO), 'y': random.randint(50, ALTO-100), 
                'vel': random.uniform(0.1, 0.4), 'ancho': random.randint(300, 600)
            })
        self.particulas_ambiente = pygame.sprite.Group()
        self.opciones_mejora_actuales = [] 
        
        # OPTIMIZACION: Cache de texto
        self.text_cache = {}
        
        # UI PAUSA
        self.rect_btn_reiniciar = pygame.Rect(ANCHO//2 - 100, ALTO//2 + 80, 200, 40) 

    def cargar_recursos(self):
        try:
            r_disp = resolver_ruta(PATH_SND_DISPARO)
            if os.path.exists(r_disp): self.snd_disparo = pygame.mixer.Sound(r_disp)
            r_muer = resolver_ruta(PATH_SND_MUERTE)
            if os.path.exists(r_muer): self.snd_muerte = pygame.mixer.Sound(r_muer)
            r_pow = resolver_ruta(PATH_SND_POWERUP)
            if os.path.exists(r_pow): self.snd_powerup = pygame.mixer.Sound(r_pow)
            r_niv = resolver_ruta(PATH_SND_NIVEL)
            if os.path.exists(r_niv): self.snd_nivel = pygame.mixer.Sound(r_niv)
            for s in [self.snd_disparo, self.snd_muerte, self.snd_powerup, self.snd_nivel]:
                if s: s.set_volume(0.25)
            r_mus = resolver_ruta(PATH_MUSIC)
            if os.path.exists(r_mus):
                pygame.mixer.music.load(r_mus)
                pygame.mixer.music.set_volume(0.18)
        except: pass

    def alternar_mute(self):
        self.juego_silenciado = not self.juego_silenciado
        vol = 0 if self.juego_silenciado else 1
        try: pygame.mixer.music.set_volume(0.18 * vol)
        except: pass

    def abrir_enlace(self, url):
        if sys.platform == 'emscripten':
            try:
                import js
                js.window.open(url, '_blank')
            except: pass
        else:
            webbrowser.open(url)

    def detectar_dispositivo_tactil(self):
        # En emscripten (web), verificar múltiples indicadores de dispositivo táctil
        if sys.platform == 'emscripten':
            try:
                import js
                # Verificar maxTouchPoints
                max_touch = js.navigator.maxTouchPoints
                has_touch = max_touch > 0

                # Verificar ontouchstart en window
                has_touch_start = 'ontouchstart' in js.window

                # Verificar user agent para dispositivos móviles
                user_agent = js.navigator.userAgent.lower()
                is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent or 'ipod' in user_agent

                # Verificar soporta eventos táctiles
                supports_touch_events = 'touchstart' in js.window or 'touchmove' in js.window

                return has_touch or has_touch_start or is_mobile or supports_touch_events
            except:
                return False

        # En otras plataformas, verificar pygame
        try:
            # Intentar obtener información de dispositivos de entrada
            import pygame
            if pygame.display.get_init():
                # Verificar si hay dispositivos táctiles disponibles
                num_devices = pygame.joystick.get_count()
                for i in range(num_devices):
                    try:
                        joystick = pygame.joystick.Joystick(i)
                        if joystick.get_name():
                            # Algunos dispositivos táctiles se reportan como joysticks
                            return True
                    except:
                        pass
        except:
            pass

        # Verificar variable de entorno para testing
        import os
        return os.environ.get('FORCE_TOUCH', 'false').lower() == 'true'
        # En desktop, verificar si hay pantallas táctiles disponibles
        try:
            import pygame
            return pygame.display.is_init() and len(pygame.display.get_wm_info().get('windows', [])) > 0
        except:
            pass
        return False

    def procesar_botones_tactiles_continuos(self):
        """Procesa los botones táctiles continuamente mientras el usuario los mantiene presionados"""
        if not self.controles_tactiles_activados or self.estado != ESTADO_JUGANDO:
            return

        # Verificar cada toque activo contra las zonas grandes
        for touch_id, (tx, ty) in self.toques_activos.items():
            # Zona izquierda - mover a la izquierda
            if self.zona_toque_izq.collidepoint(tx, ty):
                self.mago.mover_izquierda = True
                self.mago.mover_derecha = False
                self.zona_izq_activada = True

            # Zona derecha - mover a la derecha
            if self.zona_toque_der.collidepoint(tx, ty):
                self.mago.mover_derecha = True
                self.mago.mover_izquierda = False
                self.zona_der_activada = True

            # Zona de disparo
            if self.zona_toque_disparo.collidepoint(tx, ty):
                self.mago.disparando_tactil = True
                self.zona_disparo_activada = True

    def resetear_movimiento_tactil(self):
        """Resetea el estado de movimiento táctil cuando no hay toques en las zonas"""
        if not self.controles_tactiles_activados:
            return

        # Verificar si hay algún toque en las zonas
        hay_toque_izquierdo = False
        hay_toque_derecho = False
        hay_toque_disparo = False

        for touch_id, (tx, ty) in self.toques_activos.items():
            if self.zona_toque_izq.collidepoint(tx, ty):
                hay_toque_izquierdo = True
            if self.zona_toque_der.collidepoint(tx, ty):
                hay_toque_derecho = True
            if self.zona_toque_disparo.collidepoint(tx, ty):
                hay_toque_disparo = True

        # Actualizar estados de las zonas
        self.zona_izq_activada = hay_toque_izquierdo
        self.zona_der_activada = hay_toque_derecho
        self.zona_disparo_activada = hay_toque_disparo

        # Resetear movimiento si no hay toques
        if not hay_toque_izquierdo:
            self.mago.mover_izquierda = False
        if not hay_toque_derecho:
            self.mago.mover_derecha = False
        if not hay_toque_disparo:
            self.mago.disparando_tactil = False
            # Para Snake: liberar carga cuando se suelta el dedo del disparo
            if self.mago.tipo == "snake" and self.mago.cargando:
                self.mago.liberar_carga(self.proyectiles_mago)

    def cargar_fondo(self):
        try:
            p = resolver_ruta("assets/fondo.png")
            if os.path.exists(p):
                self.fondo_img = pygame.image.load(p).convert(); self.fondo_img = pygame.transform.scale(self.fondo_img, (ANCHO, ALTO))
        except: pass

    def inicializar_grupos(self):
        self.todos_sprites = pygame.sprite.Group()
        self.monstruos = pygame.sprite.Group()
        self.proyectiles_mago = pygame.sprite.Group()
        self.proyectiles_enemigos = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.corazones = pygame.sprite.Group()
        self.barreras = pygame.sprite.Group()
        self.particulas = pygame.sprite.Group()
        self.orbes_xp = pygame.sprite.Group()
        self.charcos = pygame.sprite.Group()
        self.mago = Mago(self.todos_sprites, self.proyectiles_mago, self.snd_disparo, "MAGO")
        self.todos_sprites.add(self.mago)

    def ir_a_seleccion_personaje(self, diff):
        self.dificultad = diff
        self.estado = ESTADO_SELECCION_PERSONAJE

    def iniciar_partida(self, tipo_personaje):
        self.tipo_personaje_seleccionado = tipo_personaje
        self.puntuacion = 0
        self.nivel = settings.DEBUG_NIVEL_INICIO if settings.DEBUG_MODE else 1
        self.tiempo_sin_powerup = 0
        self.ultimo_spawn_powerup_cielo = 0
        self.inicializar_grupos()
        self.mago.kill() 
        mejoras = self.gestor_datos.datos["mejoras"]
        self.mago = Mago(self.todos_sprites, self.proyectiles_mago, self.snd_disparo, tipo_personaje, mejoras)
        self.todos_sprites.add(self.mago)
        
        self.crear_barreras(); self.crear_horda()
        self.estado = ESTADO_JUGANDO
        self.fondo_cache = None 
        try:
            if not self.juego_silenciado: pygame.mixer.music.play(-1)
        except: pass

    def crear_barreras(self):
        for b in self.barreras: b.kill()
        intervalo = ANCHO // (CANTIDAD_GRUPOS_BARRERAS + 1)
        for i in range(1, CANTIDAD_GRUPOS_BARRERAS + 1):
            cx = i * intervalo
            b1, b2 = Barrera(cx - 35, ALTO - 120), Barrera(cx + 35, ALTO - 120)
            self.barreras.add(b1, b2); self.todos_sprites.add(b1, b2)

    def crear_horda(self):
        self.crear_barreras()
        self.ha_intentado_spawn_tesoro = False 
        self.mago.oleada_actual = self.nivel
        
        # Limpiar todos los proyectiles, powerups y elementos del nivel anterior
        # (excepto el mago que conserva sus powerups equipados)
        for sprite in self.proyectiles_mago:
            sprite.kill()
        for sprite in self.proyectiles_enemigos:
            sprite.kill()
        for sprite in self.orbes_xp:
            sprite.kill()
        for sprite in self.powerups:
            sprite.kill()
        for sprite in self.corazones:
            sprite.kill()
        for sprite in self.charcos:
            sprite.kill()
        # Nota: Los lasers del boss están en todos_sprites y se limpian con el boss
        
        # Asegurar que no haya boss anterior
        if self.boss_instancia:
            self.boss_instancia.kill()
            self.boss_instancia = None
        
        if self.nivel % FRECUENCIA_BOSS == 0:
            if self.nivel == 10:
                # BOSS FINAL: SNAKE ASTRAL (Sustituye al boss normal en nivel 10)
                # Asegurar que no quede ningún boss anterior
                for sprite in self.todos_sprites:
                    if isinstance(sprite, (Boss, BossSNAKE)):
                        sprite.kill()
                self.boss_instancia = BossSNAKE(self.dificultad, self.nivel)
                self.todos_sprites.add(self.boss_instancia)
            else:
                # Lógica de variantes: Solo en Difícil
                if self.dificultad == MODO_NORMAL:
                    variante = BOSS_TIPO_NORMAL
                else:
                    # En difícil, cualquier boss (incluso el primero) puede ser variante
                    variante = random.choice([BOSS_TIPO_HIELO, BOSS_TIPO_TOXICO, BOSS_TIPO_FUEGO, BOSS_TIPO_NORMAL])
                
                self.boss_instancia = Boss(self.nivel, self.dificultad, variante)
                self.todos_sprites.add(self.boss_instancia)
        else:
            self.boss_instancia = None
            vx = (VEL_MONSTRUO_BASE_X + (self.nivel * INCREMENTO_VEL_X_POR_NIVEL)) * (MULT_VEL_DIFICIL if self.dificultad == MODO_DIFICIL else 1)
            desc = DISTANCIA_DESCENSO_BASE + ((self.nivel // 5) * INCREMENTO_DESCENSO_CADA_5)
            mf = MULT_DISPARO_DIFICIL if self.dificultad == MODO_DIFICIL else 1.0
            
            # Espaciado Aumentado 
            espacio_x = 52 
            espacio_y = 48 
            mx = (ANCHO - (COLUMNAS_MONSTRUOS * espacio_x)) // 2
            
            for f in range(FILAS_MONSTRUOS):
                for c in range(COLUMNAS_MONSTRUOS):
                    tipo = TIPO_ENEMIGO_NORMAL
                    roll = random.random()
                    if self.nivel >= 3 and roll < 0.2: tipo = TIPO_ENEMIGO_RAPIDO
                    elif self.nivel >= 5 and roll < 0.05: tipo = TIPO_ENEMIGO_ELITE
                    elif self.nivel >= 6 and roll < 0.1: tipo = TIPO_ENEMIGO_TANQUE
                    m = Monstruo(mx + c * espacio_x, 90 + f * espacio_y, (FILAS_MONSTRUOS - 1 - f), vx, desc, mf, self.nivel, tipo)
                    self.todos_sprites.add(m); self.monstruos.add(m)

    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado
        self.tiempo_estado_inicio = pygame.time.get_ticks()
        # Resetear efectos visuales al volver al menú
        if nuevo_estado == ESTADO_MENU:
            self.flash_alpha = 0
            self.screen_shake = 0
        # FIX: Resetear estado de carga de Snake al cambiar de estado
        # para evitar que se quede ralentizado permanentemente
        if hasattr(self, 'mago') and self.mago and self.mago.tipo == "snake" and self.mago.cargando:
            self.mago.liberar_carga(self.proyectiles_mago)
        if nuevo_estado == ESTADO_SELECCION_MEJORA: self.generar_opciones_mejora()
        elif nuevo_estado == ESTADO_SELECCION_RECOMPENSA_BOSS: self.generar_opciones_boss()
        elif nuevo_estado == ESTADO_GAMEOVER:
            self.gestor_datos.actualizar_highscore(self.puntuacion)
            self.verificar_desbloqueos()
        elif nuevo_estado == ESTADO_MENU:
            self.verificar_desbloqueos()

    def verificar_desbloqueos(self):
        """Verifica y activa el desbloqueo de personajes según las condiciones."""
        hubo_cambio = False
        
        # EL LOCO: Se desbloquea al llegar al nivel 10
        # Chequeamos tanto el nivel de la oleada como el nivel de run del mago
        if (self.nivel >= 10 or self.mago.nivel_run >= 10) and not self.gestor_datos.datos.get("unlocked_loco", False):
            self.gestor_datos.datos["unlocked_loco"] = True
            self.notificacion_powerup = "¡EL LOCO DESBLOQUEADO!"
            self.tiempo_notificacion_powerup = pygame.time.get_ticks()
            hubo_cambio = True

        # SNAKE: Se desbloquea al vencer al boss final en difícil
        # (Esto se maneja principalmente en la colisión del boss, pero protegemos aquí)
        if hubo_cambio:
            self.gestor_datos.guardar()

    def recompensar_boss(self):
        self.xp_pendiente_boss = (FILAS_MONSTRUOS * COLUMNAS_MONSTRUOS * XP_POR_ENEMIGO) // 2
        # Guardar flag antes de que el nivel se incremente
        self.es_boss_nivel_5 = (self.nivel == 5)
        self.generar_opciones_boss()
        self.cambiar_estado(ESTADO_SELECCION_RECOMPENSA_BOSS)
        if self.mago.vidas < self.mago.max_vidas: self.mago.vidas += 1

    def generar_opciones_boss(self):
        self.opciones_boss = []
        
        # HABILIDAD ESPECIAL UNICA DEL PERSONAJE (Solo en Nivel 5)
        if getattr(self, 'es_boss_nivel_5', False):
            if self.mago.tipo == "MAGO":
                self.opciones_boss = [{"id": "unlock_escudo_especial", "titulo": "ESPEJO ARCANO", "desc": "Escudo que rebota proyectiles (30s CD, 2x dano).", "color": AZUL_MAGO}]
            elif self.mago.tipo == "piromante":
                self.opciones_boss = [{"id": "unlock_furia_ignea", "titulo": "FURIA IGNEA", "desc": "Quema enemigos 5s (1 dmg/s). Muertos propagan.", "color": NARANJA_FUEGO}]
            elif self.mago.tipo == "cazador":
                self.opciones_boss = [{"id": "unlock_tirador_sombra", "titulo": "TIRADOR DE SOMBRA", "desc": "30% de atravesar todo +15% critico.", "color": VERDE_BARRERA}]
            elif self.mago.tipo == "el_loco":
                self.opciones_boss = [{"id": "unlock_tormenta_caos", "titulo": "FUERZA BRUTA", "desc": "+1 punto de Dano.", "color": (200, 255, 0)}]
            elif self.mago.tipo == "snake":
                self.opciones_boss = [{"id": "unlock_serpentina", "titulo": "SANGRE DE SERPIENTE", "desc": "+1 Vida, Cura, Velocidad disparo x2.", "color": (0, 200, 0)}]
        
        # Si no es nivel 5, no hay opciones (solo XP y heal automatico)
        
    def aplicar_recompensa_boss(self, indice):
        if indice >= len(self.opciones_boss):
            # No hay opciones (boss no-nivel-5): solo dar XP
            if hasattr(self, 'xp_pendiente_boss') and self.xp_pendiente_boss > 0:
                if self.mago.ganar_xp(self.xp_pendiente_boss):
                    self.cambiar_estado(ESTADO_SELECCION_MEJORA)
                    if self.snd_nivel and not self.juego_silenciado: self.snd_nivel.play()
                self.xp_pendiente_boss = 0
            else:
                if self.boss_instancia and self.boss_instancia.destruyendo:
                    self.boss_instancia.kill()
                    self.boss_instancia = None
                self.estado = ESTADO_JUGANDO
            return
        
        opt = self.opciones_boss[indice]
        tid = opt["id"]
        
        if tid == "unlock_escudo_especial":
            self.mago.escudo_especial_desbloqueado = True
            self.mago.escudo_especial = EscudoEspecial(self.mago)
            self.mago.escudo_especial.activar()
            self.mago.shield_regen_cd = 16000  # 16 segundos de cooldown
            self.todos_sprites.add(self.mago.escudo_especial)
            self.notificacion_powerup = "ESPEJO ARCANO DESBLOQUEADO!"
            self.tiempo_notificacion_powerup = pygame.time.get_ticks()
        elif tid == "unlock_furia_ignea":
            self.mago.furia_ignea = True
            self.mago.skill_burn = True
            self.mago.burn_exp_damage = 1.0  # 1 dmg por tick
            self.mago.burn_exp_radius = 100
            self.mago.burn_duration = 5000  # 5 segundos
            self.notificacion_powerup = "FURIA IGNEA DESBLOQUEADA!"
            self.tiempo_notificacion_powerup = pygame.time.get_ticks()
        elif tid == "unlock_tirador_sombra":
            self.mago.tirador_sombra = True
            self.mago.skill_pierce = True
            self.mago.pierce_freq = 1  # Cada disparo tiene chance
            self.mago.pierce_count = 999  # Atraviesa todos
            self.mago.stats["chance_critico"] += 0.15  # +15% crit
            self.notificacion_powerup = "TIRADOR DE SOMBRA DESBLOQUEADO!"
            self.tiempo_notificacion_powerup = pygame.time.get_ticks()
        elif tid == "unlock_tormenta_caos":
            self.mago.stats["danio_multi"] += 1.0  # +1 punto de dano
            self.notificacion_powerup = "FUERZA BRUTA DESBLOQUEADA!"
            self.tiempo_notificacion_powerup = pygame.time.get_ticks()
        elif tid == "unlock_serpentina":
            self.mago.max_vidas += 1
            self.mago.vidas = self.mago.max_vidas  # Cura completa
            self.mago.stats["velocidad_ataque_multi"] *= 0.5  # Duplicar velocidad de disparo (reducir intervalo)
            self.notificacion_powerup = "SANGRE DE SERPIENTE DESBLOQUEADA!"
            self.tiempo_notificacion_powerup = pygame.time.get_ticks()
        
        if hasattr(self, 'xp_pendiente_boss') and self.xp_pendiente_boss > 0:
            if self.mago.ganar_xp(self.xp_pendiente_boss):
                self.cambiar_estado(ESTADO_SELECCION_MEJORA)
                if self.snd_nivel and not self.juego_silenciado: self.snd_nivel.play()
            self.xp_pendiente_boss = 0
        else:
            if self.boss_instancia and self.boss_instancia.destruyendo:
                self.boss_instancia.kill()
                self.boss_instancia = None
            self.estado = ESTADO_JUGANDO

    def manejar_colisiones(self):
        if self.estado != ESTADO_JUGANDO: return
        ahora, md = pygame.time.get_ticks(), 2 if self.mago.doble_danio_activo else 1
        
        # Mago recoge XP
        # Mago recoge XP
        for orbe in pygame.sprite.spritecollide(self.mago, self.orbes_xp, True, collided=collided_hitbox):
            if self.mago.ganar_xp(orbe.valor):
                 self.cambiar_estado(ESTADO_SELECCION_MEJORA)
                 if self.snd_nivel and not self.juego_silenciado: self.snd_nivel.play()

        impactos = pygame.sprite.groupcollide(self.proyectiles_mago, self.monstruos, False, False)
        for bala, enemigos in impactos.items():
            es_rayo = getattr(bala, 'es_rayo', False)
            es_hielo = getattr(bala, 'es_hielo', False)
            es_frag = getattr(bala, 'es_fragmentacion', False)
            penetracion = getattr(bala, 'penetracion', 0)
            
            if not es_rayo:
                if penetracion <= 0:
                    # Rebote entre enemigos
                    rebotado = False
                    if getattr(bala, 'rebotes', 0) > 0:
                        rebotado = bala.rebotar(self.monstruos, ignorar=enemigos[0])
                    
                    if not rebotado:
                        bala.kill()
                        if getattr(bala, 'es_explosivo', False): 
                            bala.fragmentar(self.todos_sprites, self.proyectiles_mago, md)
                        if es_frag:
                            bala.fragmentar(self.todos_sprites, self.proyectiles_mago, md)
                else: bala.penetracion -= 1
            
            for e in enemigos:
                # Burn Logic
                if getattr(bala, 'es_quemadura', False):
                     e.quemado = True
                     e.quemado_timer = pygame.time.get_ticks()
                     e.ultimo_dano_quemadura = pygame.time.get_ticks()
                     # FURIA ÍGNEA: Marcar el enemigo para propagar quemadura si muere
                     if getattr(bala, 'furia_ignea', False):
                         e.furia_ignea_activa = True

                e.hp -= bala.danio
                if es_hielo: e.congelar()
                
                # Feedback visual para daño de rayo
                if es_rayo:
                    impacto = RayoImpacto(e.rect.centerx, e.rect.centery)
                    self.todos_sprites.add(impacto)
                
                if getattr(bala, 'es_critico', False):
                    critico = CriticoHit(e.rect.centerx, e.rect.centery)
                    self.todos_sprites.add(critico)
                else:
                    # Floating Text for normal hits
                    tf = TextoFlotante(e.rect.centerx, e.rect.top, str(int(bala.danio)), BLANCO, 16)
                    self.todos_sprites.add(tf)
                
                if e.hp <= 0:
                    # FURIA ÍGNEA: Si el enemigo murió por quemadura, propaga a cercanos
                    if getattr(e, 'murio_por_quemadura', False):
                        e.propagar_quemadura(self.monstruos)
                        self.explosion_efecto(e.rect.centerx, e.rect.centery, NARANJA_FUEGO)
                    
                    # Pyromancer Check (daño de explosión por quemadura)
                    if getattr(e, 'quemado', False) and not e.murio_por_quemadura:
                        for m2 in self.monstruos:
                             if m2 != e and math.hypot(m2.rect.centerx - e.rect.centerx, m2.rect.centery - e.rect.centery) < self.mago.burn_exp_radius:
                                 m2.hp -= bala.danio * self.mago.burn_exp_damage
                                 self.explosion_efecto(m2.rect.centerx, m2.rect.centery, NARANJA_FUEGO)

                    if e.congelado:
                        for i in range(8):
                            rad = math.radians(i * 45); vx_f, vy_f = math.cos(rad) * 7.5, math.sin(rad) * 7.5
                            frag = Proyectil(e.rect.centerx, e.rect.centery, vx_f, vy_f, 5, color=BLANCO_HIELO, es_hielo=False) 
                            self.todos_sprites.add(frag); self.proyectiles_mago.add(frag)
                        self.explosion_efecto(e.rect.centerx, e.rect.centery, BLANCO_HIELO)
                    pts = PUNTOS_POR_FILA.get(e.fila_original, 100)
                    if e.tipo == TIPO_ENEMIGO_ELITE: pts *= 3
                    self.puntuacion += pts
                    self.explosion_efecto(e.rect.centerx, e.rect.centery, e.color)
                    
                    # Soltar XP
                    xp = OrbeXP(e.rect.centerx, e.rect.centery)
                    self.todos_sprites.add(xp); self.orbes_xp.add(xp)
                    
                    drop_cristal = False; cant_cristal = 0
                    if e.tipo == TIPO_ENEMIGO_TESORO: drop_cristal = True; cant_cristal = 5
                    elif e.tipo == TIPO_ENEMIGO_ELITE: drop_cristal = True; cant_cristal = 2
                    elif random.random() < 0.02: drop_cristal = True; cant_cristal = 1
                    if drop_cristal:
                        self.gestor_datos.agregar_cristales(cant_cristal)
                        color_txt = ORO_PODER if cant_cristal > 1 else CIAN_MAGIA
                        self.dibujar_texto(f"+{cant_cristal}", self.fuente_sm, color_txt, e.rect.centerx, e.rect.centery - 20)
                    if self.snd_muerte and not self.juego_silenciado: self.snd_muerte.play()
                    self.drop_powerup_enemigo(e.rect.centerx, e.rect.centery, ahora); e.kill()
        
        if self.mago.orbital_activo:
            impactos_orb = pygame.sprite.groupcollide(self.mago.orbitales_grupo, self.monstruos, False, False)
            for orb, enemigos in impactos_orb.items():
                for e in enemigos:
                     if random.random() < 0.1: self.explosion_efecto(e.rect.centerx, e.rect.centery, ROJO_ORBITAL)
                     e.hp -= orb.danio * 0.2 
                     # Floating Text for orbital
                     if random.random() < 0.3: # Reduce spam
                        tf = TextoFlotante(e.rect.centerx, e.rect.top, str(int(orb.danio * 0.2)), ROJO_ORBITAL, 12)
                        self.todos_sprites.add(tf)

                     if e.hp <= 0:
                         self.puntuacion += 10
                         self.explosion_efecto(e.rect.centerx, e.rect.centery, e.color)
                         e.kill()
            
            # Colisión de orbitales con proyectiles enemigos (ESCUDO)
            impactos_orb_proyectiles = pygame.sprite.groupcollide(self.mago.orbitales_grupo, self.proyectiles_enemigos, False, True)
            for orb, proyectiles in impactos_orb_proyectiles.items():
                for p in proyectiles:
                    self.explosion_efecto(p.rect.centerx, p.rect.centery, ROJO_ORBITAL)

        impactos_bar_mago = pygame.sprite.groupcollide(self.proyectiles_mago, self.barreras, False, False)
        for bala, barreras_golpeadas in impactos_bar_mago.items():
            es_rayo = getattr(bala, 'es_rayo', False)
            if not es_rayo: bala.kill(); [b.recibir_danio() for b in barreras_golpeadas]

        if self.boss_instancia and not self.boss_instancia.destruyendo: 
            h = pygame.sprite.spritecollide(self.boss_instancia, self.proyectiles_mago, False) 
            for b in h:
                if not self.boss_instancia: break  # Verificar que el boss siga existiendo
                es_rayo = getattr(b, 'es_rayo', False)
                es_hielo = getattr(b, 'es_hielo', False)
                if not es_rayo: b.kill()
                if getattr(b, 'es_rayo_player', False):
                    danio = 2 # Daño continuo (por frame)
                else:
                    danio = 15 if es_rayo else b.danio
                self.boss_instancia.hp -= danio
                
                # Floating Text Boss
                tf = TextoFlotante(self.boss_instancia.rect.centerx + random.randint(-40, 40), self.boss_instancia.rect.centery + random.randint(-20, 20), str(int(danio)), ORO_PODER if es_rayo else BLANCO, 24 if es_rayo else 18)
                self.todos_sprites.add(tf)

                if es_hielo: self.boss_instancia.congelar()
                self.explosion_efecto(b.rect.centerx, b.rect.centery, MORADO_OSCURO)
                if self.boss_instancia.hp <= 0: 
                    self.puntuacion += 2000 * (self.nivel // FRECUENCIA_BOSS)
                    self.gestor_datos.agregar_cristales(10) 
                    self.gestor_datos.registrar_boss_kill() 
                    
                    # Victoria final - Boss SNAKE nivel 10
                    if self.nivel == 10 and isinstance(self.boss_instancia, BossSNAKE):
                        if self.boss_instancia:  # Verificar que boss_instancia no sea None
                            self.boss_instancia.kill()
                        self.boss_instancia = None
                        self.gestor_datos.agregar_cristales(100)
                        # DESBLOQUEO DE PERSONAJES
                        self.gestor_datos.datos["unlocked_loco"] = True
                        if self.dificultad == MODO_DIFICIL:
                            self.gestor_datos.datos["unlocked_snake"] = True
                        self.gestor_datos.guardar()
                        self.verificar_desbloqueos() # Notificaciones
                        self.clicks_victoria = 0
                        self.cambiar_estado(ESTADO_VICTORIA_FINAL)
                        break
                    elif self.nivel == 5:
                        # BOSS NIVEL 5: Recompensa especial. Lo matamos y llamamos a recompensar.
                        if self.boss_instancia: self.boss_instancia.kill()
                        self.boss_instancia = None
                        # CAMBIO: Llamar a recompensar ANTES de subir el nivel para que detecte nivel 5
                        self.recompensar_boss()
                        self.nivel += 1
                        break
                    else:
                        # BOSS periodico normal: dar XP directo y avanzar
                        if self.boss_instancia:
                            self.boss_instancia.kill()
                        self.boss_instancia = None
                        xp_boss = (FILAS_MONSTRUOS * COLUMNAS_MONSTRUOS * XP_POR_ENEMIGO) // 2
                        if self.mago.ganar_xp(xp_boss):
                            self.cambiar_estado(ESTADO_SELECCION_MEJORA)
                            if self.snd_nivel and not self.juego_silenciado: self.snd_nivel.play()
                        else:
                            self.nivel += 1; self.cambiar_estado(ESTADO_TRANSICION)
                        if self.mago.vidas < self.mago.max_vidas: self.mago.vidas += 1
            
        if self.boss_instancia and not self.boss_instancia.alive():
            [c.kill() for c in self.charcos] # Limpiar charcos al morir boss
            
            # Victoria final - Boss SNAKE nivel 10
            if self.nivel == 10 and isinstance(self.boss_instancia, BossSNAKE):
                self.boss_instancia = None
                self.gestor_datos.agregar_cristales(100)  # Recompensa de 100 gemas
                # DESBLOQUEO DE PERSONAJES
                self.gestor_datos.datos["unlocked_loco"] = True
                # Desbloquear snake solo si es modo difícil
                if self.dificultad == MODO_DIFICIL:
                    self.gestor_datos.datos["unlocked_snake"] = True
                self.gestor_datos.guardar()
                self.clicks_victoria = 0  # Contador de clicks para volver al menú
                self.cambiar_estado(ESTADO_VICTORIA_FINAL)
            else:
                self.boss_instancia = None; self.nivel += 1; self.cambiar_estado(ESTADO_TRANSICION)

        impactos_bar_enemigo = pygame.sprite.groupcollide(self.proyectiles_enemigos, self.barreras, False, False)
        for p, barreras_golpeadas in impactos_bar_enemigo.items():
            # Bombas de Boss atraviesan o simplemente dejan charco en el suelo de las barreras
            if getattr(p, 'es_bomba', False) and self.boss_instancia:
                tipo_charco = "fuego" if self.boss_instancia.variante == BOSS_TIPO_FUEGO else ("veneno" if self.boss_instancia.variante == BOSS_TIPO_TOXICO else "hielo")
                charco = Charco(p.rect.centerx, ALTO - 50, tipo_charco)
                self.charcos.add(charco); self.todos_sprites.add(charco)
                p.kill()
            else:
                p.kill() # Proyectiles normales se destruyen
            for b in barreras_golpeadas: b.recibir_danio()

        if self.mago.escudo_especial and self.mago.escudo_especial.activo:
            impactos_escudo = pygame.sprite.spritecollide(self.mago.escudo_especial, self.proyectiles_enemigos, False)
            for p in impactos_escudo:
                # Rebotar proyectil con doble de daño del mago
                danio_rebotado = DANIO_BASE_MAGO * self.mago.stats["danio_multi"] * 2
                p.es_enemigo = False
                p.danio = danio_rebotado
                p.vy = -abs(p.vy) # Asegurar que vaya hacia arriba
                p.color = CIAN_MAGIA
                p.es_explosivo = True
                
                # Actualizar imagen del proyectil
                p.image = pygame.Surface((10*2+6, 10*2+6), pygame.SRCALPHA)
                pygame.draw.circle(p.image, CIAN_MAGIA, (10+3, 10+3), 10)
                pygame.draw.circle(p.image, BLANCO, (10+3, 10+3), 10//3)
                p.rect = p.image.get_rect(center=p.rect.center)

                # SINERGIA: Añadir al grupo de proyectiles del mago para dañar enemigos
                self.proyectiles_mago.add(p)
                self.proyectiles_enemigos.remove(p)
                
                # Desactivar escudo por 30 segundos
                self.mago.escudo_especial.desactivar()
        
        # IMPACTO PROYECTIL ENEMIGO -> JUGADOR
        col_list = pygame.sprite.spritecollide(self.mago, self.proyectiles_enemigos, True, collided=collided_hitbox)
        for p in col_list:
             # Spawnear charco si impacta al jugador 
             if getattr(p, 'es_bomba', False) and self.boss_instancia: 
                 tipo_charco = "fuego" if self.boss_instancia.variante == BOSS_TIPO_FUEGO else ("veneno" if self.boss_instancia.variante == BOSS_TIPO_TOXICO else "hielo")
                 charco = Charco(p.rect.centerx, ALTO - 50, tipo_charco) 
                 self.charcos.add(charco); self.todos_sprites.add(charco)
             
             if self.mago.recibir_danio():
                self.screen_shake = 10; self.flash_alpha = 150 
                self.explosion_efecto(self.mago.rect.centerx, self.mago.rect.top, AZUL_MAGO)
                if self.boss_instancia and self.boss_instancia.variante == BOSS_TIPO_HIELO:
                    self.mago.aplicar_ralentizacion() 
                if self.mago.vidas <= 0: self.cambiar_estado(ESTADO_GAMEOVER)

        # CHOQUE DE PROYECTILES (Habilidad de EL LOCO)
        if self.mago.skill_cancel_prob > 0:
            choques = pygame.sprite.groupcollide(self.proyectiles_mago, self.proyectiles_enemigos, False, False)
            for b_m, balas_e in choques.items():
                for b_e in balas_e:
                    if random.random() < self.mago.skill_cancel_prob:
                        self.explosion_efecto(b_e.rect.centerx, b_e.rect.centery, BLANCO)
                        b_m.kill(); b_e.kill()
                        break 

        # OPTIMIZACION: COLISIONES LASER SNAKE
        for s in self.todos_sprites:
            if isinstance(s, LaserSNAKE):
                # Usar clipline para deteccion precisa y rapida
                rad = math.radians(s.angulo)
                fin_x = s.x + math.cos(rad) * 1000
                fin_y = s.y + math.sin(rad) * 1000
                
                # Chequear si la linea del laser cruza el rectangulo del mago (usando hitbox si existe)
                mago_rect = getattr(self.mago, 'hitbox', self.mago.rect)
                clip = mago_rect.clipline(s.x, s.y, fin_x, fin_y)
                if clip:
                    if self.mago.recibir_danio():
                        self.screen_shake = 10; self.flash_alpha = 150
                
                # Chequear barreras
                for b in self.barreras:
                    if b.rect.clipline(s.x, s.y, fin_x, fin_y):
                        # El laser atraviesa barreras? Si, es un laser gigante.
                        pass
        
        # COLISIÓN BOSS SNAKE EMBISTIENDO
        if self.boss_instancia and hasattr(self.boss_instancia, 'embestiendo') and self.boss_instancia.embestiendo:
            if collided_hitbox(self.mago, self.boss_instancia):
                if self.mago.recibir_danio():
                    self.screen_shake = 15; self.flash_alpha = 200
                    self.explosion_efecto(self.mago.rect.centerx, self.mago.rect.top, ROJO_VIDA)

        # CHARCOS EN EL SUELO (Si fallan al jugador/barreras)
        for p in self.proyectiles_enemigos:
            if p.rect.bottom >= ALTO - 50 and (getattr(p, 'es_bomba', False) or getattr(p, 'radio_custom', 0) > 30): 
                if self.boss_instancia:
                    tipo = "fuego" if self.boss_instancia.variante == BOSS_TIPO_FUEGO else ("veneno" if self.boss_instancia.variante == BOSS_TIPO_TOXICO else "hielo")
                    c = Charco(p.rect.centerx, ALTO - 50, tipo); self.charcos.add(c); self.todos_sprites.add(c)
                p.kill() # Destruir proyectil al impactar suelo
                self.explosion_efecto(p.rect.centerx, p.rect.bottom, MORADO_CARGADO)

        # INTERACCION CON CHARCOS
        charcos_pisados = pygame.sprite.spritecollide(self.mago, self.charcos, False, collided=collided_hitbox)
        for c in charcos_pisados:
            if c.tipo == "hielo":
                self.mago.resbalando = True # Activa fisica de hielo
                # Efecto resbalar adicional (un pequeño empuje random)
                if random.random() < 0.1: self.mago.momentum_x += random.choice([-2, 2])
            elif c.tipo == "veneno":
                now = pygame.time.get_ticks()
                if not hasattr(self.mago, "ultimo_veneno"): self.mago.ultimo_veneno = 0
                if now - self.mago.ultimo_veneno > TICK_CHARCO_VENENO:
                    if self.mago.recibir_danio():
                        self.screen_shake = 10; self.flash_alpha = 150
                        self.mago.ultimo_veneno = now
            elif c.tipo == "fuego":
                 now = pygame.time.get_ticks()
                 if not hasattr(self.mago, "ultimo_fuego"): self.mago.ultimo_fuego = 0
                 if now - self.mago.ultimo_fuego > 1000: # Tick cada segundo
                     if self.mago.recibir_danio():
                         self.screen_shake = 10; self.flash_alpha = 150
                         self.mago.ultimo_fuego = now

        for p in pygame.sprite.spritecollide(self.mago, self.powerups, True, collided=collided_hitbox): 
            self.tiempo_sin_powerup = 0
            if p.tipo == "reparar_barreras":
                self.crear_barreras()
                if self.snd_powerup and not self.juego_silenciado: self.snd_powerup.play()
            else:
                self.mago.aplicar_powerup(p.tipo)
                if self.snd_powerup and not self.juego_silenciado: self.snd_powerup.play()
        for c in pygame.sprite.spritecollide(self.mago, self.corazones, True, collided=collided_hitbox):
            if self.mago.vidas < self.mago.max_vidas: self.mago.vidas += 1
            if self.snd_powerup and not self.juego_silenciado: self.snd_powerup.play()

        if self.mago.escudo_pendiente:
            targets = list(self.monstruos) + ([self.boss_instancia] if self.boss_instancia and not self.boss_instancia.destruyendo else [])
            for m in targets:
                if m and math.hypot(self.mago.rect.centerx - m.rect.centerx, self.mago.rect.centery - m.rect.centery) < self.mago.radio_escudo: self.mago.activar_escudo(); break
        if self.mago.escudo_activo:
            for m in list(self.monstruos):
                if math.hypot(self.mago.rect.centerx - m.rect.centerx, self.mago.rect.centery - m.rect.centery) < self.mago.radio_escudo: self.explosion_efecto(m.rect.centerx, m.rect.centery, NARANJA_FUEGO); m.kill()

    def explosion_efecto(self, x, y, color):
        for _ in range(16): p = Particula(x, y, color); self.particulas.add(p); self.todos_sprites.add(p)

    def drop_powerup_enemigo(self, x, y, ahora):
        bonus_prob = 0.0
        if self.tiempo_sin_powerup > TIEMPO_SIN_POWERUP_MS_BONUS:
            tiempo_extra = self.tiempo_sin_powerup - TIEMPO_SIN_POWERUP_MS_BONUS
            bonus_prob = min(BONUS_PROB_MAXIMO, (tiempo_extra / 1000.0) * BONUS_PROB_POR_SEGUNDO)
            if self.boss_instancia and not self.boss_instancia.destruyendo:
                bonus_prob *= BONUS_PROB_BOSS
        
        total_hp_barreras = sum(b.hp for b in self.barreras)
        
        if total_hp_barreras == 0 and random.random() < 0.15:
             p = PowerUp(x, y, "reparar_barreras")
             self.powerups.add(p); self.todos_sprites.add(p); return

        roll = random.random()
        prob_base = PROB_POWERUP_BASE + bonus_prob
        if self.nivel >= 10: prob_base = PROB_POWERUP_ENDGAME + bonus_prob
        
        if roll < PROB_CORAZON:
             c = Corazon(x, y, ahora); self.corazones.add(c); self.todos_sprites.add(c)
        elif roll < PROB_POWERUP_RAYO + bonus_prob:
             p = PowerUp(x, y, "rayo"); self.powerups.add(p); self.todos_sprites.add(p)
        elif roll < prob_base:
             tipos = ["cadencia", "arco", "disparo_doble", "disparo_triple", "explosivo", "escudo", "doble_danio"]
             if self.mago.nivel_run >= UNLOCK_REQ_ORBITAL: tipos.append("orbital")
             if self.mago.nivel_run >= UNLOCK_REQ_HOMING: tipos.append("homing")
             
             t = random.choice(tipos)
             p = PowerUp(x, y, t); self.powerups.add(p); self.todos_sprites.add(p)

    def generar_powerup(self, x, y):
        if random.random() < PROB_POWERUP_RAYO:
            pu = PowerUp(x, y, "rayo"); self.todos_sprites.add(pu); self.powerups.add(pu); return
        opts = list(COLORES_PU.keys())
        if "rayo" in opts: opts.remove("rayo") 
        if self.mago.escudo_activo or self.mago.escudo_pendiente:
            if "escudo" in opts: opts.remove("escudo")
        if self.mago.stats["proyectiles_extra"] > 1 and "disparo_doble" in opts: opts.remove("disparo_doble")
        kills = self.gestor_datos.datos.get("boss_kills", 0)
        if kills < UNLOCK_REQ_ORBITAL and "orbital" in opts: opts.remove("orbital")
        if kills < UNLOCK_REQ_HOMING and "homing" in opts: opts.remove("homing")
        if opts: pu = PowerUp(x, y, random.choice(opts)); self.todos_sprites.add(pu); self.powerups.add(pu)
    
    def generar_opciones_mejora(self):
        posibles = [
            {"id": "vida", "titulo": "VIDA MAX +1", "desc": "Sube vida max y cura todo.", "color": ROJO_VIDA},
            {"id": "danio", "titulo": "DAÑO +20%", "desc": "Aumenta el daño base.", "color": NARANJA_FUEGO},
            {"id": "vel_atk", "titulo": "ATQ VEL +15%", "desc": "Dispara mas rapido.", "color": CIAN_MAGIA},
            {"id": "multidisparo", "titulo": "+1 PROYECTIL", "desc": "Dispara una bala extra permanente.", "color": VERDE_BARRERA},
            {"id": "rebote", "titulo": "REBOTE +1", "desc": "Los proyectiles rebotan.", "color": AZUL_RAYO},
            {"id": "perforante", "titulo": "PERFORACION +1", "desc": "Atraviesa 1 enemigo.", "color": MORADO_OSCURO},
            {"id": "fragmentacion_perma", "titulo": "FRAGMENTACIÓN", "desc": "Balas se dividen al impactar.", "color": NARANJA_FUEGO},
            {"id": "arco_perma", "titulo": "DISPARO ARCO", "desc": "Disparo lateral (Reduce Cadencia y Vel. Bala)", "color": MAGENTA_ARCO},
            {"id": "hielo_perma", "titulo": "TOQUE GELIDO", "desc": "Chance de congelar.", "color": AZUL_CONGELADO},
            {"id": "proyectil_grande", "titulo": "PROYECTIL XXL", "desc": "Balas mas grandes y rapidas (+30% vel).", "color": AMARILLO_DORADO},
            {"id": "homing_perma", "titulo": "MIRA AUTO", "desc": "Alta probabilidad de auto-apuntado.", "color": VERDE_FLUOR},
        ]
        
        # Filtrar ya adquiridos
        if self.mago.modificadores["fragmentacion"]: posibles = [p for p in posibles if p["id"] != "fragmentacion_perma"]
        if self.mago.modificadores["arco"]: posibles = [p for p in posibles if p["id"] != "arco_perma"]
        if self.mago.modificadores["homing"]: posibles = [p for p in posibles if p["id"] != "homing_perma"]
        if self.mago.modificadores["proyectil_grande"]: posibles = [p for p in posibles if p["id"] != "proyectil_grande"]
        
        # Potenciar opciones ya tomadas (más probabilidad)
        potenciados = []
        # Ids con peso extra (aparecen mas seguido)
        ids_peso_extra = {"hielo_perma", "rebote", "perforante"}
        for opcion in posibles:
            id_op = opcion["id"]
            veces = self.mago.mejoras_contador.get(id_op, 0)
            if veces > 0:
                # Añadir múltiples copias para aumentar probabilidad
                for _ in range(veces + 1):
                    potenciados.append(opcion.copy())
            else:
                potenciados.append(opcion)
            
            # Peso extra para power-ups permanentes clave
            if id_op in ids_peso_extra:
                for _ in range(2):
                    potenciados.append(opcion.copy())

        # Seleccionar 3 opciones unicas basándose en pesos (sin repetir)
        self.opciones_mejora_actuales = []
        # Clonamos la lista para no vaciar la original
        pool_temporal = list(potenciados)
        while len(self.opciones_mejora_actuales) < min(3, len(posibles)):
            if not pool_temporal: break
            nueva = random.choice(pool_temporal)
            # Agregar si no está ya seleccionada
            if not any(o["id"] == nueva["id"] for o in self.opciones_mejora_actuales):
                self.opciones_mejora_actuales.append(nueva)
            # Eliminar todas las copias de este ID para no volverlo a elegir
            pool_temporal = [p for p in pool_temporal if p["id"] != nueva["id"]]
    
    def aplicar_mejora_permanente(self, indice):
        if indice < 1 or indice > len(self.opciones_mejora_actuales): return
        tipo = self.opciones_mejora_actuales[indice-1]["id"]
        
        # Incrementar contador de mejora
        self.mago.mejoras_contador[tipo] = self.mago.mejoras_contador.get(tipo, 0) + 1
        
        if tipo == "vida": self.mago.max_vidas += MEJORA_VIDA_MAXIMA; self.mago.vidas = self.mago.max_vidas
        elif tipo == "danio": 
            if self.mago.tipo == "el_loco":
                # El Loco: +0.5 de daño fijo (0.05 * 10)
                self.mago.stats["danio_multi"] += 0.05
            else:
                # Otros: +20% de daño total
                self.mago.stats["danio_multi"] *= 1.20
        elif tipo == "vel_atk": 
            # Bonus por mejora repetida: +2% adicional por cada repetición
            bonus = self.mago.mejoras_contador["vel_atk"] * 0.02
            # Mejora proporcional: cada nivel aumenta la velocidad de ataque base en un 15%
            self.mago.stats["velocidad_ataque_multi"] *= (1.15 + bonus)
        elif tipo == "multidisparo": 
            self.mago.stats["proyectiles_extra"] += 1
            #Bonus por mejora repetida: +1 proyectil extra cada 3 picked
            if self.mago.mejoras_contador["multidisparo"] >= 3:
                self.mago.stats["proyectiles_extra"] += 1
                self.mago.mejoras_contador["multidisparo"] = 0  # Reset counter
        elif tipo == "rebote": self.mago.stats["rebotes"] += 1
        elif tipo == "perforante": self.mago.stats["penetracion"] += 1
        elif tipo == "fragmentacion_perma": self.mago.modificadores["fragmentacion"] = True
        elif tipo == "arco_perma": 
            self.mago.modificadores["arco"] = True
            self.mago.stats["velocidad_ataque_multi"] = max(0.2, self.mago.stats["velocidad_ataque_multi"] - 0.15)
            self.mago.stats["velocidad_proyectil"] = max(3.5, self.mago.stats["velocidad_proyectil"] * 0.85)
        elif tipo == "hielo_perma": self.mago.nivel_hielo += 1
        elif tipo == "proyectil_grande": 
            self.mago.modificadores["proyectil_grande"] = True
            #Bonus por mejora repetida: +10% velocidad adicional
            bonus_vel = self.mago.mejoras_contador["proyectil_grande"] * 0.1
            self.mago.stats["velocidad_proyectil"] *= (1.3 + bonus_vel)
        elif tipo == "homing_perma": 
            self.mago.modificadores["homing"] = True
            #Bonus por mejora repetida: +5% probabilidad de crítico
            bonus_crit = self.mago.mejoras_contador["homing_perma"] * 0.05
            self.mago.stats["chance_critico"] = min(0.5, self.mago.stats["chance_critico"] + 0.05 + bonus_crit)
        
        self.estado = ESTADO_JUGANDO

    def manejar_ambiente(self):
        # Mover niebla
        for capa in self.niebla_capas:
            capa['x'] += capa['vel']
            if capa['x'] > ANCHO:
                capa['x'] = -capa['ancho']
        
        # Generar partículas
        if random.random() < 0.05:
            tipo = "luciernaga" if random.random() < 0.7 else "mota"
            p = ParticulaAmbiental(random.randint(0, ANCHO), random.randint(0, ALTO), tipo)
            self.particulas_ambiente.add(p)
        
        self.particulas_ambiente.update()
        
        # Limpiar partículas viejas
        for p in self.particulas_ambiente:
            if p.alpha <= 0: p.kill()

    def dibujar_fondo_procedural(self):
        # Si tenemos cache y es del tamaño correcto, usarlo
        if self.fondo_cache is None:
            self.fondo_cache = pygame.Surface((ANCHO, ALTO))
            
            # Color base según nivel/bioma (simple logic for now)
            bioma_idx = (self.nivel - 1) // 5 % 3
            paleta = BIOMAS.get(bioma_idx, BIOMAS[0])
            
            self.fondo_cache.fill(paleta["cesped"])
            
            # Dibujar patrones (hierba/piedras)
            for _ in range(200):
                x, y = random.randint(0, ANCHO), random.randint(0, ALTO)
                color = paleta["var1"] if random.random() < 0.5 else paleta["var2"]
                pygame.draw.rect(self.fondo_cache, color, (x, y, 4, 4))
                
            # Árboles fondo
            for _ in range(15):
                x, y = random.randint(0, ANCHO), random.randint(0, 100)
                pygame.draw.circle(self.fondo_cache, paleta["arbol_fondo"], (x, y), random.randint(20, 40))

        self.pantalla.blit(self.fondo_cache, (0, 0))
        
        # Niebla (dinámica, no cacheada)
        s_niebla = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        for capa in self.niebla_capas:
            pygame.draw.ellipse(s_niebla, (*COLOR_NIEBLA_BRUMA, 40), (capa['x'], capa['y'], capa['ancho'], 80))
            # Dibujar copia para loop infinito
            if capa['x'] + capa['ancho'] > ANCHO:
                 pygame.draw.ellipse(s_niebla, (*COLOR_NIEBLA_BRUMA, 40), (capa['x'] - ANCHO - 300, capa['y'], capa['ancho'], 80))

        self.pantalla.blit(s_niebla, (0,0))

    def dibujar_tienda(self):
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); overlay.fill((10, 10, 20, 255)); self.pantalla.blit(overlay, (0,0))
        self.dibujar_texto("TIENDA ARCANA", self.fuente_lg, ORO_PODER, ANCHO//2, 50)
        self.dibujar_texto(f"Tus Cristales: {self.gestor_datos.datos['cristales']}", self.fuente_md, CIAN_MAGIA, ANCHO//2, 90)
        
        items = ["vida_base", "danio_base", "critico"] 
        rects = [self.rect_tienda_item_1, self.rect_tienda_item_2, self.rect_tienda_item_3]
        
        for i, clave in enumerate(items):
            info = PRECIOS_TIENDA[clave]
            lvl = self.gestor_datos.datos["mejoras"].get(clave, 0) 
            r = rects[i]
            pygame.draw.rect(self.pantalla, GRIS_TARJETA, r, border_radius=15)
            pygame.draw.rect(self.pantalla, BORDE_TARJETA, r, 3, border_radius=15)
            # Ajustar nombre si es muy largo
            self.dibujar_texto_ajustado(info["nombre"], self.fuente_md, BLANCO, pygame.Rect(r.x + 5, r.top + 15, r.width - 10, 30))
            self.dibujar_texto(f"Nivel: {lvl}/{info['max']}", self.fuente_sm, ORO_PODER, r.centerx, r.top + 60)
            costo = int(info["base"] * (FACTOR_COSTO_TIENDA ** lvl))
            if lvl >= info["max"]: 
                txt_costo = "AGOTADO"
                c_precio = GRIS_DESACTIVADO
                # Visualmente indicar que esta maxed
                pygame.draw.rect(self.pantalla, (0, 0, 0, 100), r, border_radius=15)
            else: 
                txt_costo = f"{costo} Gemas"
                c_precio = CIAN_MAGIA if self.gestor_datos.datos['cristales'] >= costo else ROJO_VIDA
            
            self.dibujar_texto_ajustado(txt_costo, self.fuente_md, c_precio, pygame.Rect(r.x + 5, r.bottom - 45, r.width - 10, 30))
            
        pygame.draw.rect(self.pantalla, ROJO_VIDA, self.rect_btn_volver_tienda, border_radius=10)
        self.dibujar_texto("VOLVER AL MENU", self.fuente_md, BLANCO, self.rect_btn_volver_tienda.centerx, self.rect_btn_volver_tienda.centery)

        # Boton Donacion (Amarillo BuyMeACoffee)
        pygame.draw.rect(self.pantalla, (255, 221, 0), self.rect_btn_donacion, border_radius=10)
        self.dibujar_texto("Buy me a coffee", self.fuente_md, (0, 0, 0), self.rect_btn_donacion.centerx, self.rect_btn_donacion.centery)

    def dibujar_menu_debug(self):
        """Dibuja el menú de configuración de debug"""
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((10, 10, 30, 240))
        self.pantalla.blit(overlay, (0,0))
        
        self.dibujar_texto("MENÚ DEBUG", self.fuente_lg, (255, 0, 255), ANCHO//2, 50)
        self.dibujar_texto(f"Nivel Actual: {self.nivel}", self.fuente_md, CIAN_MAGIA, ANCHO//2, 100)
        
        # Función helper para dibujar botón toggle
        def dibujar_boton_toggle(rect, texto, activo, color_activo=(0, 255, 100), color_inactivo=(255, 50, 50)):
            color = color_activo if activo else color_inactivo
            pygame.draw.rect(self.pantalla, color, rect, border_radius=8)
            estado = "ON" if activo else "OFF"
            self.dibujar_texto(f"{texto}: {estado}", self.fuente_md, BLANCO, rect.centerx, rect.centery)
        
        # Botones de opciones
        dibujar_boton_toggle(self.rect_debug_toggle, "Modo Debug", settings.DEBUG_MODE)
        dibujar_boton_toggle(self.rect_debug_god, "God Mode", settings.DEBUG_GOD_MODE)
        dibujar_boton_toggle(self.rect_debug_stats, "Max Stats", settings.DEBUG_MAX_STATS)
        dibujar_boton_toggle(self.rect_debug_unlock, "All Unlocked", settings.DEBUG_ALL_UNLOCKED)
        dibujar_boton_toggle(self.rect_debug_powerups, "All Powerups", settings.DEBUG_ALL_POWERUPS)
        dibujar_boton_toggle(self.rect_debug_charges, "Cargas Infinitas", settings.DEBUG_INFINITE_CHARGES)
        
        # Botones de nivel
        pygame.draw.rect(self.pantalla, (100, 100, 100), self.rect_debug_nivel_prev, border_radius=8)
        self.dibujar_texto("<<", self.fuente_md, BLANCO, self.rect_debug_nivel_prev.centerx, self.rect_debug_nivel_prev.centery)
        
        pygame.draw.rect(self.pantalla, (100, 100, 100), self.rect_debug_nivel_next, border_radius=8)
        self.dibujar_texto(">>", self.fuente_md, BLANCO, self.rect_debug_nivel_next.centerx, self.rect_debug_nivel_next.centery)
        
        self.dibujar_texto("Cambiar Nivel", self.fuente_sm, BLANCO, ANCHO//2, self.rect_debug_nivel_prev.centery)
        
        # Botón cerrar
        pygame.draw.rect(self.pantalla, ROJO_VIDA, self.rect_debug_cerrar, border_radius=10)
        self.dibujar_texto("CERRAR (F12)", self.fuente_md, BLANCO, self.rect_debug_cerrar.centerx, self.rect_debug_cerrar.centery)
        
        # Botones directos a bosses
        pygame.draw.rect(self.pantalla, (150, 50, 150), self.rect_debug_boss5, border_radius=8)
        self.dibujar_texto("BOSS Lv5", self.fuente_sm, BLANCO, self.rect_debug_boss5.centerx, self.rect_debug_boss5.centery)
        
        pygame.draw.rect(self.pantalla, (200, 100, 0), self.rect_debug_boss10, border_radius=8)
        self.dibujar_texto("BOSS Lv10", self.fuente_sm, BLANCO, self.rect_debug_boss10.centerx, self.rect_debug_boss10.centery)
        
        # Instrucciones
        self.dibujar_texto("Presiona F12 para abrir/cerrar este menú", self.fuente_sm, (200, 200, 200), ANCHO//2, ALTO - 30)

    def _manejar_click_menu_debug(self, x, y):
        """Maneja los clicks en el menú de debug"""
        if self.rect_debug_toggle.collidepoint(x, y):
            settings.DEBUG_MODE = not settings.DEBUG_MODE
            if not settings.DEBUG_MODE:
                # Al desactivar DEBUG_MODE, desactivar todas las opciones
                settings.DEBUG_GOD_MODE = False
                settings.DEBUG_MAX_STATS = False
                settings.DEBUG_ALL_UNLOCKED = False
                settings.DEBUG_ALL_POWERUPS = False
                settings.DEBUG_INFINITE_CHARGES = False
                self._revertir_debug_effects()
        elif self.rect_debug_god.collidepoint(x, y):
            settings.DEBUG_GOD_MODE = not settings.DEBUG_GOD_MODE
            if self.mago:
                if settings.DEBUG_GOD_MODE:
                    self.mago.invulnerable = True
                    self.mago.max_vidas = 999
                    self.mago.vidas = 999
                else:
                    self.mago.invulnerable = False
                    self.mago.max_vidas = 3
                    self.mago.vidas = min(self.mago.vidas, 3)
        elif self.rect_debug_stats.collidepoint(x, y):
            settings.DEBUG_MAX_STATS = not settings.DEBUG_MAX_STATS
            if self.mago:
                if settings.DEBUG_MAX_STATS:
                    self._aplicar_max_stats()
                else:
                    self._revertir_max_stats()
        elif self.rect_debug_unlock.collidepoint(x, y):
            settings.DEBUG_ALL_UNLOCKED = not settings.DEBUG_ALL_UNLOCKED
        elif self.rect_debug_powerups.collidepoint(x, y):
            settings.DEBUG_ALL_POWERUPS = not settings.DEBUG_ALL_POWERUPS
        elif self.rect_debug_charges.collidepoint(x, y):
            settings.DEBUG_INFINITE_CHARGES = not settings.DEBUG_INFINITE_CHARGES
        elif self.rect_debug_nivel_prev.collidepoint(x, y):
            self.nivel = max(1, self.nivel - 1)
            self.crear_horda()
        elif self.rect_debug_nivel_next.collidepoint(x, y):
            self.nivel = min(10, self.nivel + 1)
            self.crear_horda()
        elif self.rect_debug_boss5.collidepoint(x, y):
            self.nivel = 5
            settings.DEBUG_NIVEL_INICIO = 5
            self.iniciar_partida(self.tipo_personaje_seleccionado)
        elif self.rect_debug_boss10.collidepoint(x, y):
            self.nivel = 10
            settings.DEBUG_NIVEL_INICIO = 10
            self.iniciar_partida(self.tipo_personaje_seleccionado)
        elif self.rect_debug_cerrar.collidepoint(x, y):
            self.cambiar_estado(ESTADO_JUGANDO)

    def _aplicar_max_stats(self):
        """Aplica stats máximas al mago actual"""
        if self.mago:
            self.mago.stats["danio_multi"] = 10.0
            self.mago.stats["velocidad_ataque_multi"] = 5.0
            self.mago.stats["velocidad_proyectil"] = 15.0
            self.mago.stats["proyectiles_extra"] = 5
            self.mago.stats["rebotes"] = 5
            self.mago.stats["penetracion"] = 5
            self.mago.stats["chance_critico"] = 1.0
            self.mago.stats["danio_critico"] = 5.0
            self.mago.stats["velocidad_movimiento"] = 12.0
            self.mago.nivel_hielo = 20

    def _revertir_max_stats(self):
        """Revierte stats máximas a valores base del personaje"""
        if self.mago:
            datos = self.mago.datos
            s_base = datos["stats_base"]
            self.mago.stats["danio_multi"] = s_base["danio_multi"]
            self.mago.stats["velocidad_ataque_multi"] = s_base["velocidad_ataque_multi"]
            self.mago.stats["velocidad_proyectil"] = 6.0 if self.mago.tipo == "el_loco" else 9.0
            self.mago.stats["proyectiles_extra"] = s_base["proyectiles_extra"]
            self.mago.stats["rebotes"] = 0
            self.mago.stats["penetracion"] = 0
            self.mago.stats["chance_critico"] = 0.10 if self.mago.tipo == "cazador" else 0.05
            self.mago.stats["danio_critico"] = 1.5
            self.mago.stats["velocidad_movimiento"] = s_base["velocidad_movimiento"]
            self.mago.nivel_hielo = 0

    def _revertir_debug_effects(self):
        """Revierte todos los efectos de debug"""
        if self.mago:
            # Revertir god mode
            self.mago.invulnerable = False
            self.mago.max_vidas = 3
            self.mago.vidas = min(self.mago.vidas, 3)
            # Revertir stats
            self._revertir_max_stats()

    def dibujar_tarjeta_mejora(self, rect, titulo, desc, color):
        pygame.draw.rect(self.pantalla, GRIS_TARJETA, rect, border_radius=15)
        pygame.draw.rect(self.pantalla, color, rect, 3, border_radius=15)
        
        # Título ajustado para no salir del cuadro
        self.dibujar_texto_ajustado(titulo, self.fuente_md, color, pygame.Rect(rect.x + 10, rect.top + 20, rect.width - 20, 40))
        
        # Descripción con párrafo real (no manual)
        self.dibujar_texto_parrafo(desc, self.fuente_sm, BLANCO, pygame.Rect(rect.x + 15, rect.top + 60, rect.width - 30, rect.height - 70))

    def dibujar(self):
        off_x, off_y = (random.randint(-4,4), random.randint(-4,4)) if self.screen_shake > 0 else (0,0)
        if self.fondo_img: self.pantalla.blit(self.fondo_img, (0, 0))
        else: self.dibujar_fondo_procedural()
        for p in self.particulas_ambiente: self.pantalla.blit(p.image, p.rect)

        if self.estado == ESTADO_MENU:
            self.dibujar_texto("MAGO DEFENCE", self.fuente_lg, AZUL_MAGO, ANCHO//2, 100)
            self.dibujar_texto("By Jose C Sierra", self.fuente_sm, ORO_PODER, ANCHO//2, 140)
            if self.gestor_datos.datos["high_score"] > 0: self.dibujar_texto(f"RECORD: {self.gestor_datos.datos['high_score']}", self.fuente_md, BLANCO, ANCHO//2, 180)
            self.dibujar_texto(f"CRISTALES: {self.gestor_datos.datos['cristales']}", self.fuente_md, CIAN_MAGIA, ANCHO//2, 220)
            kills = self.gestor_datos.datos.get("boss_kills", 0)
            if kills > 0: self.dibujar_texto(f"Jefes Derrotados: {kills}", self.fuente_sm, MORADO_OSCURO, ANCHO//2, 250)
            
            pygame.draw.rect(self.pantalla, GRIS_BOTON, self.rect_btn_toggle_tactil, border_radius=12)
            self.dibujar_texto("TACTIL: " + ("ON" if self.controles_tactiles_activados else "OFF"), self.fuente_sm, BLANCO, self.rect_btn_toggle_tactil.centerx, self.rect_btn_toggle_tactil.centery)
            
            # BOTON JUGAR
            pygame.draw.rect(self.pantalla, VERDE_JUGAR, self.rect_btn_jugar, border_radius=15)
            pygame.draw.rect(self.pantalla, BLANCO, self.rect_btn_jugar, 3, border_radius=15)
            self.dibujar_texto("JUGAR", self.fuente_md, BLANCO, self.rect_btn_jugar.centerx, self.rect_btn_jugar.centery)
            
            # SELECTOR DIFICULTAD
            c_norm = AMARILLO_SELECCION if self.dificultad == MODO_NORMAL else GRIS_BOTON
            c_dif = ROJO_BORRAR_HOVER if self.dificultad == MODO_DIFICIL else GRIS_BOTON
            pygame.draw.rect(self.pantalla, c_norm, self.rect_btn_diff_normal, border_radius=8)
            self.dibujar_texto("NORMAL", self.fuente_sm, NEGRO if self.dificultad == MODO_NORMAL else BLANCO, self.rect_btn_diff_normal.centerx, self.rect_btn_diff_normal.centery)
            pygame.draw.rect(self.pantalla, c_dif, self.rect_btn_diff_dificil, border_radius=8)
            self.dibujar_texto("DIFICIL", self.fuente_sm, BLANCO, self.rect_btn_diff_dificil.centerx, self.rect_btn_diff_dificil.centery)
            
            # BOTON TIENDA
            pygame.draw.rect(self.pantalla, MORADO_CARGADO, self.rect_btn_ir_tienda, border_radius=10)
            self.dibujar_texto("TIENDA", self.fuente_md, BLANCO, self.rect_btn_ir_tienda.centerx, self.rect_btn_ir_tienda.centery)
            
            # BOTON BORRAR
            c_borrar = ROJO_BORRAR if not self.confirmando_borrado else (255, 0, 0)
            pygame.draw.rect(self.pantalla, c_borrar, self.rect_btn_borrar, border_radius=8)
            txt_borrar = "BORRAR DATOS" if not self.confirmando_borrado else "¿SEGURO?"
            self.dibujar_texto(txt_borrar, self.fuente_sm, BLANCO, self.rect_btn_borrar.centerx, self.rect_btn_borrar.centery)

            # BOTONES EXPORTAR / IMPORTAR
            pygame.draw.rect(self.pantalla, (60, 60, 80), self.rect_btn_exportar, border_radius=6)
            pygame.draw.rect(self.pantalla, (100, 100, 130), self.rect_btn_exportar, 2, border_radius=6)
            self.dibujar_texto("EXPORTAR", self.fuente_xs, BLANCO, self.rect_btn_exportar.centerx, self.rect_btn_exportar.centery)
            
            pygame.draw.rect(self.pantalla, (60, 60, 80), self.rect_btn_importar, border_radius=6)
            pygame.draw.rect(self.pantalla, (100, 100, 130), self.rect_btn_importar, 2, border_radius=6)
            self.dibujar_texto("IMPORTAR", self.fuente_xs, BLANCO, self.rect_btn_importar.centerx, self.rect_btn_importar.centery)

            # VERSION (v1.0.1)
            self.dibujar_texto(f"v{VERSION}", self.fuente_xs, GRIS_BOTON, 45, 20)

        elif self.estado == ESTADO_TIENDA:
            self.dibujar_tienda()
        
        elif self.estado == ESTADO_DEBUG_MENU:
            self.dibujar_menu_debug()

        elif self.estado == ESTADO_SELECCION_PERSONAJE:
            overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); overlay.fill((0, 0, 0, 220)); self.pantalla.blit(overlay, (0,0))
            self.dibujar_texto("ELIGE TU MAGO", self.fuente_lg, BLANCO, ANCHO//2, 60)
            txt_diff = "MODO: NORMAL" if self.dificultad == MODO_NORMAL else "MODO: DIFICIL"
            c_diff = VERDE_BARRERA if self.dificultad == MODO_NORMAL else ROJO_VIDA
            self.dibujar_texto(txt_diff, self.fuente_md, c_diff, ANCHO//2, 100)
            
            def dibujar_char_card(rect, key):
                d = DATOS_PERSONAJES[key]
                s = d["stats_base"]
                unlocked = True
                if key == "el_loco": 
                    unlocked = self.gestor_datos.datos.get("unlocked_loco", False) or (settings.DEBUG_MODE and settings.DEBUG_ALL_UNLOCKED)
                elif key == "snake":
                    unlocked = self.gestor_datos.datos.get("unlocked_snake", False) or (settings.DEBUG_MODE and settings.DEBUG_ALL_UNLOCKED)
                
                # En modo debug, mostrar indicador
                if settings.DEBUG_MODE and settings.DEBUG_ALL_UNLOCKED:
                    unlocked = True
                
                if not unlocked:
                    pygame.draw.rect(self.pantalla, (20, 20, 20), rect, border_radius=15)
                    pygame.draw.rect(self.pantalla, GRIS_DESACTIVADO, rect, 2, border_radius=15)
                    if key == "snake":
                        self.dibujar_texto("???", self.fuente_md, GRIS_DESACTIVADO, rect.centerx, rect.top + 60)
                        self.dibujar_texto("Vence al boss final", self.fuente_xs, GRIS_DESACTIVADO, rect.centerx, rect.top + 100)
                        self.dibujar_texto("en Difícil", self.fuente_xs, GRIS_DESACTIVADO, rect.centerx, rect.top + 120)
                    else:
                        self.dibujar_texto("???", self.fuente_md, GRIS_DESACTIVADO, rect.centerx, rect.top + 60)
                        self.dibujar_texto("Llega a nivel 10", self.fuente_xs, GRIS_DESACTIVADO, rect.centerx, rect.top + 100)
                        self.dibujar_texto("para desbloquear", self.fuente_xs, GRIS_DESACTIVADO, rect.centerx, rect.top + 120)
                    return
                
                pygame.draw.rect(self.pantalla, GRIS_TARJETA, rect, border_radius=15)
                c_borde = ORO_PODER if self.tipo_personaje_seleccionado == key else BORDE_TARJETA
                pygame.draw.rect(self.pantalla, c_borde, rect, 3 if self.tipo_personaje_seleccionado == key else 5, border_radius=15)
                
                # Sprite en la parte superior
                sprite_path = resolver_ruta(d.get("sprite_frente", d["sprite"]))
                if os.path.exists(sprite_path):
                    try:
                        img = pygame.image.load(sprite_path).convert_alpha()
                        img = pygame.transform.scale(img, (70, 70))
                        self.pantalla.blit(img, (rect.centerx - 35, rect.top + 25))
                    except:
                        pass
                
                # Nombre en la parte superior (Ajustado)
                self.dibujar_texto_ajustado(d["nombre"], self.fuente_md, d["color"], pygame.Rect(rect.x + 5, rect.top + 100, rect.width - 10, 30))
                
                # Descripción principal
                self.dibujar_texto_ajustado(d["desc"], self.fuente_sm, BLANCO, pygame.Rect(rect.x + 10, rect.top + 130, rect.width - 20, 20))
                self.dibujar_texto_ajustado(d["detalle"], self.fuente_xs, GRIS_DESACTIVADO, pygame.Rect(rect.x + 10, rect.top + 150, rect.width - 20, 16))
                
                # Línea separadora
                pygame.draw.line(self.pantalla, (80, 80, 90), (rect.left + 15, rect.top + 172), (rect.right - 15, rect.top + 172), 1)
                
                # Stats en la parte inferior
                y_stats = rect.top + 185
                txt_danio = f"Daño: {s['danio_multi']:.1f}x"
                self.dibujar_texto_ajustado(txt_danio, self.fuente_xs, NARANJA_FUEGO, pygame.Rect(rect.x + 5, y_stats, rect.width - 10, 16))
                
                txt_vel = f"Vel: {s['velocidad_ataque_multi']:.1f}x"
                self.dibujar_texto_ajustado(txt_vel, self.fuente_xs, CIAN_MAGIA, pygame.Rect(rect.x + 5, y_stats + 18, rect.width - 10, 16))
                
                # Modificadores y proyectiles
                y_mods = y_stats + 40
                mods_texto = []
                if s["modificadores"]:
                    mods_texto.extend([m.upper() for m in s["modificadores"]])
                if s["proyectiles_extra"] > 0:
                    mods_texto.append(f"MULTI +{s['proyectiles_extra']}")
                if mods_texto:
                    for i, mod in enumerate(mods_texto):
                        self.dibujar_texto(f"[{mod}]", self.fuente_xs, ORO_PODER, rect.centerx, y_mods + (i * 18))

            dibujar_char_card(self.rect_char_1, "MAGO")
            dibujar_char_card(self.rect_char_2, "piromante")
            dibujar_char_card(self.rect_char_3, "cazador")
            dibujar_char_card(self.rect_char_4, "el_loco")
            dibujar_char_card(self.rect_char_5, "snake")
            
            self.dibujar_texto("Presiona click para elegir y comenzar", self.fuente_sm, BLANCO, ANCHO//2, ALTO - 40)

        elif self.estado in [ESTADO_JUGANDO, ESTADO_PAUSA, ESTADO_GAMEOVER, ESTADO_TRANSICION, ESTADO_SELECCION_MEJORA, ESTADO_SELECCION_RECOMPENSA_BOSS, ESTADO_VICTORIA_FINAL]:
            # --- DIBUJAR BALCÓN (LIMITE VISUAL) ---
            y_balcon = ALTO - 50
            # Piso del balcón
            pygame.draw.rect(self.pantalla, (40, 40, 50), [0, y_balcon, ANCHO, ALTO-y_balcon])
            # Borde superior del balcón (Barandilla)
            pygame.draw.line(self.pantalla, (100, 100, 120), (0, y_balcon), (ANCHO, y_balcon), 5)
            # Sombra/Profundidad
            pygame.draw.rect(self.pantalla, (20, 20, 30), [0, y_balcon+5, ANCHO, 10])

            for s in self.todos_sprites: self.pantalla.blit(s.image, (s.rect.x + off_x, s.rect.y + off_y))
            if self.mago.orbital_activo:
                for o in self.mago.orbitales_grupo: self.pantalla.blit(o.image, (o.rect.x + off_x, o.rect.y + off_y))
            
            if self.mago.escudo_pendiente:
                 r = self.mago.radio_escudo
                 pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5 # 0 to 1
                 alpha = int(30 + (pulse * 40))
                 s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                 pygame.draw.circle(s, (*COLOR_ESCUDO_PENDIENTE, alpha), (r, r), r, width=2)
                 self.pantalla.blit(s, (self.mago.rect.centerx - r + off_x, self.mago.rect.centery - r + off_y))

            # Indicador de carga para Snake
            if self.mago.tipo == "snake" and self.mago.cargando:
                barra_ancho = 60
                barra_alto = 8
                barra_x = self.mago.rect.centerx - barra_ancho // 2 + off_x
                barra_y = self.mago.rect.bottom + 10 + off_y
                
                # Fondo de la barra
                pygame.draw.rect(self.pantalla, (50, 50, 50), (barra_x, barra_y, barra_ancho, barra_alto))
                
                # Progreso de carga
                progreso = self.mago.carga / self.mago.max_carga
                color_carga = (0, 255, 0) if progreso >= 1.0 else (255, 200, 0)
                pygame.draw.rect(self.pantalla, color_carga, (barra_x, barra_y, int(barra_ancho * progreso), barra_alto))
                
                # Borde
                pygame.draw.rect(self.pantalla, (255, 255, 255), (barra_x, barra_y, barra_ancho, barra_alto), 1)
                
                # Texto "CARGANDO" o "¡LISTO!"
                texto_carga = "¡LISTO!" if progreso >= 1.0 else "CARGANDO"
                self.dibujar_texto(texto_carga, self.fuente_xs, color_carga, barra_x + barra_ancho // 2, barra_y - 10)

            self.dibujar_hud()
            
            if self.mago.escudo_activo:
                r = self.mago.radio_escudo; s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 120, 0, 95), (r, r), r); self.pantalla.blit(s, (self.mago.rect.centerx - r + off_x, self.mago.rect.centery - r + off_y))
            if self.controles_tactiles_activados and self.estado == ESTADO_JUGANDO: self.dibujar_botones_tactiles()
            
            if self.mago.escudo_activo:
                r = self.mago.radio_escudo; s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 120, 0, 95), (r, r), r); self.pantalla.blit(s, (self.mago.rect.centerx - r + off_x, self.mago.rect.centery - r + off_y))
            if self.controles_tactiles_activados and self.estado == ESTADO_JUGANDO: self.dibujar_botones_tactiles()
            
            if self.estado == ESTADO_PAUSA:
                overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); overlay.fill((0, 0, 0, 190)); self.pantalla.blit(overlay, (0,0))
                self.dibujar_texto("PAUSA", self.fuente_lg, BLANCO, ANCHO//2, ALTO//2 - 40)
                self.dibujar_texto("M: Menú | Esc/P: Volver", self.fuente_sm, BLANCO, ANCHO//2, ALTO//2 + 30)
                
                # Boton Reiniciar
                pygame.draw.rect(self.pantalla, ROJO_BORRAR, self.rect_btn_reiniciar, border_radius=10)
                self.dibujar_texto("REINICIAR RUN", self.fuente_md, BLANCO, self.rect_btn_reiniciar.centerx, self.rect_btn_reiniciar.centery)
            
            if self.estado == ESTADO_TRANSICION:
                 overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); overlay.fill((0, 0, 0, 150)); self.pantalla.blit(overlay, (0,0))
                 self.dibujar_texto(f"¡NIVEL {self.nivel - 1} SUPERADO!", self.fuente_lg, ORO_PODER, ANCHO//2, ALTO//2 - 20)
                 self.dibujar_texto("Preparando siguiente oleada...", self.fuente_sm, BLANCO, ANCHO//2, ALTO//2 + 40)

            elif self.estado in [ESTADO_SELECCION_MEJORA, ESTADO_SELECCION_RECOMPENSA_BOSS]:
                # Fondo desenfocado/oscuro
                s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); s.fill((0, 0, 0, 180)); self.pantalla.blit(s, (0,0))
                fuente_titulo = self.fuente_md
                opciones = self.opciones_mejora_actuales if self.estado == ESTADO_SELECCION_MEJORA else self.opciones_boss
                titulo_seccion = "SUBIDA DE NIVEL" if self.estado == ESTADO_SELECCION_MEJORA else "RECOMPENSA DE BOSS"
                
                self.dibujar_texto(titulo_seccion, self.fuente_lg, ORO_PODER, ANCHO//2, 80)
                self.dibujar_texto("Elige una mejora:" if self.estado == ESTADO_SELECCION_MEJORA else "Elige una recompensa:", self.fuente_md, BLANCO, ANCHO//2, 130)
                
                for i, opt in enumerate(opciones):
                    rect = pygame.Rect(ANCHO//2 - 150, 150 + i * 130, 300, 110)
                    self.dibujar_tarjeta_mejora(rect, opt["titulo"], opt["desc"], opt["color"])
                self.dibujar_texto("(Usa Click o Teclas 1, 2, 3)", self.fuente_sm, BLANCO, ANCHO//2, ALTO - 80)

            if self.estado == ESTADO_GAMEOVER:
                overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); overlay.fill((60, 0, 0, 210)); self.pantalla.blit(overlay, (0,0))
                self.dibujar_texto("GAME OVER", self.fuente_lg, ROJO_VIDA, ANCHO//2, ALTO//2 - 40)
                self.dibujar_texto(f"PUNTOS: {self.puntuacion}", self.fuente_md, BLANCO, ANCHO//2, ALTO//2 + 10)
                rem = max(0, 2000 - (pygame.time.get_ticks() - self.tiempo_estado_inicio))
                if rem > 0: self.dibujar_texto(f"Espere {int(rem/100)+1}...", self.fuente_sm, BLANCO, ANCHO//2, ALTO//2 + 60)
                else: self.dibujar_texto("Toca para volver al Menú", self.fuente_sm, BLANCO, ANCHO//2, ALTO//2 + 60)

            elif self.estado == ESTADO_VICTORIA_FINAL:
                overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); overlay.fill((0, 60, 0, 210)); self.pantalla.blit(overlay, (0,0))
                self.dibujar_texto("¡VICTORIA!", self.fuente_lg, VERDE_BARRERA, ANCHO//2, ALTO//2 - 80)
                self.dibujar_texto("Casa a Salvo", self.fuente_md, BLANCO, ANCHO//2, ALTO//2 - 20)
                self.dibujar_texto(f"+100 GEMAS", self.fuente_md, ORO_PODER, ANCHO//2, ALTO//2 + 30)
                self.dibujar_texto(f"Clics restantes: {3 - getattr(self, 'clicks_victoria', 0)}", self.fuente_sm, BLANCO, ANCHO//2, ALTO//2 + 80)
                self.dibujar_texto("Presiona 3 veces para regresar al menú", self.fuente_sm, (200, 200, 200), ANCHO//2, ALTO//2 + 120)

        if self.flash_alpha > 0:
            f = pygame.Surface((ANCHO, ALTO)); f.fill(BLANCO); f.set_alpha(self.flash_alpha); self.pantalla.blit(f, (0,0))
        c_mute = ROJO_VIDA if self.juego_silenciado else VERDE_BARRERA
        pygame.draw.rect(self.pantalla, c_mute, self.rect_btn_mute, border_radius=6)
        self.dibujar_texto("M", self.fuente_sm, NEGRO, self.rect_btn_mute.centerx, self.rect_btn_mute.centery)
        pygame.display.flip()

    def dibujar_hud(self):
        # Barra Superior de Fondo
        s = pygame.Surface((ANCHO, 70), pygame.SRCALPHA)
        s.fill(COLOR_HUD_BG)
        self.pantalla.blit(s, (0,0))

        # --- MODO DEBUG INDICADOR ---
        if settings.DEBUG_MODE:
            debug_text = "DEBUG MODE"
            if settings.DEBUG_GOD_MODE: debug_text += " [GOD]"
            if settings.DEBUG_INFINITE_CHARGES: debug_text += " [INF]"
            self.dibujar_texto(debug_text, self.fuente_sm, (255, 0, 255), ANCHO//2, 5)

        # --- SECCION IZQUIERDA: NIVEL y GEMAS ---
        # XP Bar mini
        pygame.draw.rect(self.pantalla, GRIS_BOTON, [20, 48, 150, 8])
        px = (self.mago.xp_actual / self.mago.xp_requerida) * 150
        pygame.draw.rect(self.pantalla, VERDE_XP, [20, 48, px, 8])
        
        self.pantalla.blit(self.fuente_md.render(f"NIVEL {self.nivel}", True, BLANCO), (20, 15))
        self.pantalla.blit(self.fuente_sm.render(f"Run Lvl: {self.mago.nivel_run}", True, BLANCO_HIELO), (100, 22))
        self.pantalla.blit(self.fuente_sm.render(f"GEMAS: {self.gestor_datos.datos['cristales']}", True, CIAN_MAGIA), (180, 22))

        # --- CENTRO: PUNTUACION ---
        self.dibujar_texto(f"{self.puntuacion}", self.fuente_lg, ORO_PODER, ANCHO//2, 35)

        # --- DERECHA: SALUD ---
        start_x_hearts = ANCHO - 40
        for i in range(min(10, self.mago.vidas)):
             pygame.draw.circle(self.pantalla, ROJO_VIDA, (start_x_hearts - (i * 25), 25), 10)
        if self.mago.vidas > 10:
             self.dibujar_texto(f"+{self.mago.vidas-10}", self.fuente_sm, ROJO_VIDA, start_x_hearts - 260, 25)

        # --- INFO ESTADO / POWERUPS ---
        ahora = pygame.time.get_ticks()
        info_parts = []
        
        if self.mago.escudo_especial and self.mago.escudo_especial_desbloqueado:
            if self.mago.escudo_especial.activo:
                info_parts.append("ESPEJO ARCANO ACTIVO")
            elif not self.mago.escudo_especial.activo and self.mago.escudo_especial.rebotado:
                cd_restante = max(0, (self.mago.escudo_especial.timer_reaparicion - ahora) // 1000)
                info_parts.append(f"ESPEJO ARCANO: {cd_restante}s")
        
        if self.mago.escudo_pendiente: info_parts.append("ESCUDO LISTO")
        
        p = self.mago.powerup_actual
        if p != "normal":
            txt_p = p.upper()
            if p == "cadencia": txt_p += f" ({max(0, (self.mago.fin_powerup - ahora)//1000)}s)"
            elif self.mago.cargas > 0: txt_p += f" x{self.mago.cargas}"
            info_parts.append(txt_p)
        
        if self.mago.doble_danio_activo:
             info_parts.append(f"2x DMG ({max(0, (self.mago.fin_doble_danio - ahora)//1000)}s)")

        if info_parts:
             full_text = " | ".join(info_parts)
             # Dibujar con escala si es muy largo para que no estorbe
             self.dibujar_texto_ajustado(full_text, self.fuente_sm, CIAN_MAGIA, pygame.Rect(10, 80, ANCHO - 20, 20))
         
        # Boss Bar
        if self.boss_instancia and not self.boss_instancia.destruyendo:
            bw = 180
            w = (self.boss_instancia.hp / self.boss_instancia.hp_max) * bw
            bx = ANCHO - bw - 40 
            by = 52
            
            # Fondo con ligero brillo morado
            pygame.draw.rect(self.pantalla, (40, 0, 80), [bx-2, by-2, bw+4, 14], border_radius=3)
            pygame.draw.rect(self.pantalla, NEGRO, [bx, by, bw, 10], border_radius=2)
            pygame.draw.rect(self.pantalla, MORADO_OSCURO, [bx, by, w, 10], border_radius=2)
            
            if w > 0:
                pygame.draw.rect(self.pantalla, (180, 100, 255), [bx, by, w, 3], border_radius=2)
            
            nombre_boss = "JEFE"
            if self.boss_instancia.variante == BOSS_TIPO_HIELO: nombre_boss = "J. HIELO"
            elif self.boss_instancia.variante == BOSS_TIPO_FUEGO: nombre_boss = "J. FUEGO"
            elif self.boss_instancia.variante == BOSS_TIPO_TOXICO: nombre_boss = "J. TOXICO"
            
            self.dibujar_texto(nombre_boss, self.fuente_sm, BLANCO, bx + bw//2, by - 14)
        
        if self.notificacion_powerup:
            alpha = 255
            tiempo_pasado = pygame.time.get_ticks() - self.tiempo_notificacion_powerup
            if tiempo_pasado > 2500:
                alpha = max(0, 255 - (tiempo_pasado - 2500) * 5)
            s = pygame.Surface((ANCHO, 50), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            self.pantalla.blit(s, (0, ALTO//2 - 25))
            self.dibujar_texto(self.notificacion_powerup, self.fuente_md, ORO_PODER, ANCHO//2, ALTO//2)

    def dibujar_botones_tactiles(self):
        # Solo mostrar indicadores sutiles, no botones grandes
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)

        # Indicador izquierdo (solo cuando se toca)
        if self.zona_izq_activada:
            # Flecha pequeña en el borde izquierdo
            pygame.draw.polygon(s, (100, 200, 255, 180), [
                (25, ALTO - 75),
                (10, ALTO - 60),
                (25, ALTO - 45)
            ], 3)
            # Línea indicadora
            pygame.draw.line(s, (100, 200, 255, 100), (25, ALTO - 60), (5, ALTO - 60), 2)

        # Indicador derecho (solo cuando se toca)
        if self.zona_der_activada:
            # Flecha pequeña en el borde derecho
            pygame.draw.polygon(s, (100, 200, 255, 180), [
                (ANCHO - 25, ALTO - 75),
                (ANCHO - 10, ALTO - 60),
                (ANCHO - 25, ALTO - 45)
            ], 3)
            # Línea indicadora
            pygame.draw.line(s, (100, 200, 255, 100), (ANCHO - 25, ALTO - 60), (ANCHO - 5, ALTO - 60), 2)

        # Indicador de disparo (solo cuando se toca)
        if self.zona_disparo_activada:
            # Punto brillante en la zona de disparo
            pygame.draw.circle(s, (255, 100, 100, 150), (ANCHO - 45, ALTO - 60), 20, 3)
            pygame.draw.circle(s, (255, 100, 100, 80), (ANCHO - 45, ALTO - 60), 12)

        self.pantalla.blit(s, (0, 0))

    def dibujar_texto(self, texto, fuente, color, x, y):
        key = (texto, fuente, color)
        if key not in self.text_cache:
            self.text_cache[key] = fuente.render(str(texto), True, color)
        
        s = self.text_cache[key]
        r = s.get_rect(center=(x, y))
        self.pantalla.blit(s, r)

    def dibujar_texto_ajustado(self, texto, fuente, color, rect, alineacion="center"):
        """Dibuja texto escalándolo para que quepa en el ancho del rect."""
        texto_str = str(texto)
        rendered = fuente.render(texto_str, True, color)
        if rendered.get_width() > rect.width:
            escala = rect.width / rendered.get_width()
            nueva_h = int(rendered.get_height() * escala)
            rendered = pygame.transform.smoothscale(rendered, (rect.width, nueva_h))
        
        if alineacion == "center":
            r = rendered.get_rect(center=rect.center)
        else: # left
            r = rendered.get_rect(midleft=(rect.x, rect.centery))
        self.pantalla.blit(rendered, r)

    def dibujar_texto_parrafo(self, texto, fuente, color, rect, interlineado=22):
        """Dibuja un párrafo con wrap automático basado en píxeles."""
        palabras = str(texto).split(' ')
        lineas = []
        linea_actual = ""
        
        for p in palabras:
            test_linea = linea_actual + p + " "
            if fuente.size(test_linea)[0] < rect.width:
                linea_actual = test_linea
            else:
                lineas.append(linea_actual)
                linea_actual = p + " "
        lineas.append(linea_actual)
        
        y_dibujo = rect.y
        for l in lineas:
            if y_dibujo + interlineado > rect.bottom: break
            surf = fuente.render(l.strip(), True, color)
            self.pantalla.blit(surf, (rect.centerx - surf.get_width()//2, y_dibujo))
            y_dibujo += interlineado

    def update(self):
        self.manejar_ambiente()
        if self.screen_shake > 0: self.screen_shake -= 1
        if self.flash_alpha > 0: self.flash_alpha = max(0, self.flash_alpha - 5)
        if self.notificacion_powerup and pygame.time.get_ticks() - self.tiempo_notificacion_powerup > 3000:
            self.notificacion_powerup = None

        # Procesar controles táctiles continuamente
        self.procesar_botones_tactiles_continuos()

        if self.estado == ESTADO_JUGANDO:
            ahora = pygame.time.get_ticks()
            teclas = pygame.key.get_pressed()
            # Combinar disparo de teclado y táctil
            if teclas[pygame.K_SPACE] or self.mago.disparando_tactil:
                self.mago.disparar(self.monstruos)

            # Resetear estado táctil al final del frame (se volverá a activar si sigue el toque)
            self.resetear_movimiento_tactil()
            
            if self.mago.vidas < self.mago.max_vidas and random.random() < PROB_CORAZON:
                c = Corazon(random.randint(40, ANCHO-40), -30); self.todos_sprites.add(c); self.corazones.add(c)
            
            bonus_prob_cielo = 0.0
            if self.tiempo_sin_powerup > TIEMPO_SIN_POWERUP_MS_BONUS:
                tiempo_extra = self.tiempo_sin_powerup - TIEMPO_SIN_POWERUP_MS_BONUS
                bonus_prob_cielo = min(BONUS_PROB_MAXIMO, (tiempo_extra / 1000.0) * BONUS_PROB_POR_SEGUNDO)
                if self.boss_instancia and not self.boss_instancia.destruyendo:
                    bonus_prob_cielo *= BONUS_PROB_BOSS * 0.5  # Reduce boss bonus multiplier
            
            tiempo_desde_ultimo = ahora - self.ultimo_spawn_powerup_cielo
            if tiempo_desde_ultimo > INTERVALO_MINIMO_POWERUPS:
                prob_cielo = PROB_POWERUP_CIELO + bonus_prob_cielo
                if random.random() < prob_cielo:
                    self.generar_powerup(random.randint(60, ANCHO - 60), -40)
                    self.ultimo_spawn_powerup_cielo = ahora
            
            if not self.boss_instancia:
                if len(self.monstruos) < 4 and not self.ha_intentado_spawn_tesoro and self.nivel % FRECUENCIA_BOSS != 0:
                    self.ha_intentado_spawn_tesoro = True
                    if random.random() < 0.5:
                        lado = random.choice([0, ANCHO - 30]) 
                        vel = VEL_MONSTRUO_BASE_X * 2.5
                        if lado > ANCHO // 2: vel *= -1 
                        m = Monstruo(lado, 130, 0, abs(vel), 0, 1.0, self.nivel, TIPO_ENEMIGO_TESORO)
                        m.vel_x = vel; m.dir = 1 
                        self.todos_sprites.add(m); self.monstruos.add(m)
            
            if self.boss_instancia: self.boss_instancia.update(ahora=ahora, grupo_s=self.todos_sprites, grupo_b=self.proyectiles_enemigos, mago=self.mago)
            else:
                borde = False
                for m in self.monstruos:
                    m.intentar_disparar(self.nivel, self.todos_sprites, self.proyectiles_enemigos)
                    if m.tipo != TIPO_ENEMIGO_TESORO:
                        if (m.rect.right >= ANCHO and m.dir == 1) or (m.rect.left <= 0 and m.dir == -1): borde = True
                if borde: [m.bajar() for m in self.monstruos]
            
            self.todos_sprites.update(mago=self.mago, monstruos=self.monstruos, grupo_s=self.todos_sprites, grupo_b=self.proyectiles_enemigos); self.manejar_colisiones()
            
            if not self.monstruos and not self.boss_instancia and self.estado == ESTADO_JUGANDO:
                # Auto-recoger XP no recolectado antes de pasar de nivel
                for orbe in self.orbes_xp:
                    if self.mago.ganar_xp(orbe.valor):
                        self.cambiar_estado(ESTADO_SELECCION_MEJORA)
                        if self.snd_nivel and not self.juego_silenciado: self.snd_nivel.play()
                        break
                else:
                    # No level up, go to next level
                    self.nivel += 1
                    self.cambiar_estado(ESTADO_TRANSICION)
                    if self.snd_nivel and not self.juego_silenciado: self.snd_nivel.play()
            for m in self.monstruos:
                if m.rect.bottom >= self.mago.rect.top: self.cambiar_estado(ESTADO_GAMEOVER)
            
            # Verificar desbloqueos en tiempo real
            if self.mago.nivel_run >= 10 or self.nivel >= 10:
                self.verificar_desbloqueos()
        
        elif self.estado == ESTADO_TRANSICION:
            if pygame.time.get_ticks() - self.tiempo_estado_inicio > 2000:
                 self.crear_horda(); self.cambiar_estado(ESTADO_JUGANDO)
        
        if self.confirmando_borrado and pygame.time.get_ticks() - self.timer_confirmacion_borrado > 3000:
            self.confirmando_borrado = False

    async def ejecutar(self):
        while self.corriendo:
            self.reloj.tick(FPS); self.mago.direccion_touch = 0
            await asyncio.sleep(0)
            ahora = pygame.time.get_ticks()
            if self.estado == ESTADO_JUGANDO:
                self.tiempo_sin_powerup += self.reloj.get_time()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: self.corriendo = False
                if ev.type == pygame.FINGERDOWN:
                    tx, ty = ev.x * ANCHO, ev.y * ALTO; self.toques_activos[ev.finger_id] = (tx, ty)
                    if self.rect_btn_mute.collidepoint(tx, ty): self.alternar_mute()
                    if self.estado == ESTADO_MENU:
                        if self.rect_btn_toggle_tactil.collidepoint(tx, ty): self.controles_tactiles_activados = not self.controles_tactiles_activados
                        if self.rect_btn_ir_tienda.collidepoint(tx, ty): self.cambiar_estado(ESTADO_TIENDA)
                        if self.rect_btn_jugar.collidepoint(tx, ty): self.ir_a_seleccion_personaje(self.dificultad)
                        if self.rect_btn_diff_normal.collidepoint(tx, ty): self.dificultad = MODO_NORMAL
                        if self.rect_btn_diff_dificil.collidepoint(tx, ty): self.dificultad = MODO_DIFICIL
                        if self.rect_btn_borrar.collidepoint(tx, ty):
                             if self.confirmando_borrado: self.gestor_datos.reiniciar_datos(); self.confirmando_borrado = False
                             else: self.confirmando_borrado, self.timer_confirmacion_borrado = True, pygame.time.get_ticks()
                        if self.rect_btn_exportar.collidepoint(tx, ty): self.gestor_datos.exportar_save_json()
                        if self.rect_btn_importar.collidepoint(tx, ty): self.gestor_datos.importar_save_json(lambda: setattr(self, 'text_cache', {}))
                    elif self.estado == ESTADO_SELECCION_PERSONAJE:
                          if self.rect_char_1.collidepoint(tx, ty): self.iniciar_partida("MAGO")
                          elif self.rect_char_2.collidepoint(tx, ty): self.iniciar_partida("piromante")
                          elif self.rect_char_3.collidepoint(tx, ty): self.iniciar_partida("cazador")
                          elif self.rect_char_4.collidepoint(tx, ty):
                              unlocked = self.gestor_datos.datos.get("unlocked_loco", False) or (DEBUG_MODE and DEBUG_ALL_UNLOCKED)
                              if unlocked: self.iniciar_partida("el_loco")
                          elif self.rect_char_5.collidepoint(tx, ty):
                              unlocked = self.gestor_datos.datos.get("unlocked_snake", False) or (DEBUG_MODE and DEBUG_ALL_UNLOCKED)
                              if unlocked: self.iniciar_partida("snake")
                    elif self.estado == ESTADO_SELECCION_MEJORA:
                        for i in range(len(self.opciones_mejora_actuales)):
                            rect = pygame.Rect(ANCHO//2 - 150, 150 + i * 130, 300, 110)
                            if rect.collidepoint(tx, ty):
                                self.aplicar_mejora_permanente(i + 1)
                                break
                    elif self.estado == ESTADO_SELECCION_RECOMPENSA_BOSS:
                        opcion_seleccionada = False
                        for i in range(len(self.opciones_boss)):
                            rect = pygame.Rect(ANCHO//2 - 150, 150 + i * 130, 300, 110)
                            if rect.collidepoint(tx, ty):
                                self.aplicar_recompensa_boss(i)
                                self.gestor_datos.guardar()
                                opcion_seleccionada = True
                                break
                        if opcion_seleccionada:
                            self.cambiar_estado(ESTADO_TRANSICION)
                    elif self.estado == ESTADO_TIENDA:
                        if self.rect_btn_volver_tienda.collidepoint(tx, ty): self.cambiar_estado(ESTADO_MENU)
                        elif self.rect_tienda_item_1.collidepoint(tx, ty): self.gestor_datos.comprar_mejora("vida_base")
                        elif self.rect_tienda_item_2.collidepoint(tx, ty): self.gestor_datos.comprar_mejora("danio_base")
                        elif self.rect_tienda_item_3.collidepoint(tx, ty): self.gestor_datos.comprar_mejora("critico")
                        elif self.rect_btn_donacion.collidepoint(tx, ty): self.abrir_enlace("https://buymeacoffee.com/srgurem")
                    elif self.estado == ESTADO_DEBUG_MENU:
                        self._manejar_click_menu_debug(tx, ty)
                    elif self.estado == ESTADO_VICTORIA_FINAL:
                        if not hasattr(self, 'clicks_victoria'): self.clicks_victoria = 0
                        self.clicks_victoria += 1
                        if self.clicks_victoria >= 3:
                            self.clicks_victoria = 0
                            self.cambiar_estado(ESTADO_MENU)
                    elif self.estado == ESTADO_TRANSICION: self.crear_horda(); self.cambiar_estado(ESTADO_JUGANDO)
                if ev.type == pygame.FINGERUP and ev.finger_id in self.toques_activos: 
                    # Para Snake: Liberar carga cuando se suelta el dedo del botón de disparo
                    if self.estado == ESTADO_JUGANDO and self.mago.tipo == "snake" and self.mago.cargando:
                        self.mago.liberar_carga(self.proyectiles_mago)
                    del self.toques_activos[ev.finger_id]
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    m_pos = ev.pos # Use m_pos for mouse position
                    self.toques_activos['mouse'] = m_pos
                    if self.rect_btn_mute.collidepoint(m_pos): self.alternar_mute()
                    if self.estado == ESTADO_MENU:
                        if self.rect_btn_toggle_tactil.collidepoint(m_pos): self.controles_tactiles_activados = not self.controles_tactiles_activados
                        elif self.rect_btn_ir_tienda.collidepoint(m_pos): self.cambiar_estado(ESTADO_TIENDA)
                        elif self.rect_btn_jugar.collidepoint(m_pos): self.ir_a_seleccion_personaje(self.dificultad)
                        elif self.rect_btn_diff_normal.collidepoint(m_pos): self.dificultad = MODO_NORMAL
                        elif self.rect_btn_diff_dificil.collidepoint(m_pos): self.dificultad = MODO_DIFICIL
                        elif self.rect_btn_borrar.collidepoint(m_pos):
                            if self.confirmando_borrado: self.gestor_datos.reiniciar_datos(); self.confirmando_borrado = False
                            else: self.confirmando_borrado, self.timer_confirmacion_borrado = True, pygame.time.get_ticks()
                        elif self.rect_btn_exportar.collidepoint(m_pos): self.gestor_datos.exportar_save_json()
                        elif self.rect_btn_importar.collidepoint(m_pos): self.gestor_datos.importar_save_json(lambda: setattr(self, 'text_cache', {}))
                    elif self.estado == ESTADO_SELECCION_PERSONAJE:
                         if self.rect_char_1.collidepoint(m_pos): self.iniciar_partida("MAGO")
                         elif self.rect_char_2.collidepoint(m_pos): self.iniciar_partida("piromante")
                         elif self.rect_char_3.collidepoint(m_pos): self.iniciar_partida("cazador")
                         elif self.rect_char_4.collidepoint(m_pos):
                             unlocked = self.gestor_datos.datos.get("unlocked_loco", False) or (DEBUG_MODE and DEBUG_ALL_UNLOCKED)
                             if unlocked: self.iniciar_partida("el_loco")
                         elif self.rect_char_5.collidepoint(m_pos):
                             unlocked = self.gestor_datos.datos.get("unlocked_snake", False) or (DEBUG_MODE and DEBUG_ALL_UNLOCKED)
                             if unlocked: self.iniciar_partida("snake")
                    elif self.estado == ESTADO_GAMEOVER and ahora - self.tiempo_estado_inicio > 2000: self.cambiar_estado(ESTADO_MENU)
                    elif self.estado == ESTADO_VICTORIA_FINAL:
                        if not hasattr(self, 'clicks_victoria'): self.clicks_victoria = 0
                        self.clicks_victoria += 1
                        if self.clicks_victoria >= 3:
                            self.clicks_victoria = 0
                            self.cambiar_estado(ESTADO_MENU)
                    elif self.estado == ESTADO_TRANSICION: self.crear_horda(); self.cambiar_estado(ESTADO_JUGANDO)
                    elif self.estado == ESTADO_SELECCION_RECOMPENSA_BOSS:
                        opcion_seleccionada = False
                        for i in range(len(self.opciones_boss)):
                            rect = pygame.Rect(ANCHO//2 - 150, 150 + i * 130, 300, 110)
                            if rect.collidepoint(m_pos):
                                self.aplicar_recompensa_boss(i)
                                self.gestor_datos.guardar()
                                opcion_seleccionada = True
                                break
                        # Solo transicionar si se seleccionó una opción
                        if opcion_seleccionada:
                            self.cambiar_estado(ESTADO_TRANSICION)
                    elif self.estado == ESTADO_SELECCION_MEJORA:
                         for i in range(len(self.opciones_mejora_actuales)):
                             rect = pygame.Rect(ANCHO//2 - 150, 150 + i * 130, 300, 110)
                             if rect.collidepoint(m_pos):
                                 self.aplicar_mejora_permanente(i + 1)
                                 break
                    elif self.estado == ESTADO_TIENDA:
                        if self.rect_btn_volver_tienda.collidepoint(m_pos): self.cambiar_estado(ESTADO_MENU)
                        elif self.rect_tienda_item_1.collidepoint(m_pos): self.gestor_datos.comprar_mejora("vida_base")
                        elif self.rect_tienda_item_2.collidepoint(m_pos): self.gestor_datos.comprar_mejora("danio_base")
                        elif self.rect_tienda_item_3.collidepoint(m_pos): self.gestor_datos.comprar_mejora("critico")
                        elif self.rect_btn_donacion.collidepoint(m_pos): self.abrir_enlace("https://buymeacoffee.com/srgurem")
                    elif self.estado == ESTADO_PAUSA:
                        if self.rect_btn_reiniciar.collidepoint(m_pos):
                             self.cambiar_estado(ESTADO_MENU)
                    elif self.estado == ESTADO_DEBUG_MENU:
                        self._manejar_click_menu_debug(m_pos[0], m_pos[1])
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    # Para Snake: Liberar carga cuando se suelta el botón del mouse
                    if self.estado == ESTADO_JUGANDO and self.mago.tipo == "snake" and self.mago.cargando:
                        self.mago.liberar_carga(self.proyectiles_mago)
                    if 'mouse' in self.toques_activos: del self.toques_activos['mouse']
                if ev.type == pygame.KEYUP:
                    # Para Snake: Liberar carga cuando se suelta el espacio
                    if self.estado == ESTADO_JUGANDO and self.mago.tipo == "snake" and ev.key == pygame.K_SPACE:
                        self.mago.liberar_carga(self.proyectiles_mago)
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_m: 
                        if self.estado in [ESTADO_PAUSA, ESTADO_GAMEOVER]: self.cambiar_estado(ESTADO_MENU)
                        else: self.alternar_mute()
                    if ev.key == pygame.K_LSHIFT: self.mago.dash() # DASH CON SHIFT
                    if self.estado == ESTADO_MENU:
                        if ev.key == pygame.K_1: self.dificultad = MODO_NORMAL; self.ir_a_seleccion_personaje(MODO_NORMAL)
                        if ev.key == pygame.K_2: self.dificultad = MODO_DIFICIL; self.ir_a_seleccion_personaje(MODO_DIFICIL)
                    elif self.estado == ESTADO_SELECCION_PERSONAJE:
                        if ev.key == pygame.K_1: self.iniciar_partida("MAGO")
                        if ev.key == pygame.K_2: self.iniciar_partida("piromante")
                        if ev.key == pygame.K_3: self.iniciar_partida("cazador")
                        if ev.key == pygame.K_4:
                            if self.gestor_datos.datos.get("unlocked_loco", False) or (DEBUG_MODE and DEBUG_ALL_UNLOCKED): 
                                self.iniciar_partida("el_loco")
                    elif self.estado == ESTADO_JUGANDO:
                        if ev.key in [pygame.K_ESCAPE, pygame.K_p]: self.cambiar_estado(ESTADO_PAUSA)
                        if ev.key == pygame.K_F12: self.cambiar_estado(ESTADO_DEBUG_MENU)
                        # DEBUG CONTROLS
                        if DEBUG_MODE:
                            if ev.key == pygame.K_F1:  # Nivel anterior
                                self.nivel = max(1, self.nivel - 1)
                                self.crear_horda()
                            if ev.key == pygame.K_F2:  # Nivel siguiente
                                self.nivel = min(10, self.nivel + 1)
                                self.crear_horda()
                            if ev.key == pygame.K_F3:  # Toggle invencibilidad
                                self.mago.invulnerable = not self.mago.invulnerable
                            if ev.key == pygame.K_F4:  # Matar todos los enemigos
                                for m in list(self.monstruos): m.hp = 0; m.kill()
                                if self.boss_instancia: self.boss_instancia.hp = 0
                            if ev.key == pygame.K_F5:  # Spawn powerup
                                tipos_pu = ["cadencia", "arco", "disparo_doble", "disparo_triple", "explosivo", "homing", "rayo"]
                                pu = PowerUp(self.mago.rect.centerx, self.mago.rect.top - 50, random.choice(tipos_pu))
                                self.powerups.add(pu); self.todos_sprites.add(pu)
                    elif self.estado == ESTADO_PAUSA:
                        if ev.key in [pygame.K_ESCAPE, pygame.K_p]: self.cambiar_estado(ESTADO_JUGANDO)
                    elif self.estado == ESTADO_GAMEOVER and ahora - self.tiempo_estado_inicio > 2000:
                        if ev.key == pygame.K_r: self.ir_a_seleccion_personaje(self.dificultad)
                        else: self.cambiar_estado(ESTADO_MENU)
                    elif self.estado == ESTADO_VICTORIA_FINAL:
                        if not hasattr(self, 'clicks_victoria'): self.clicks_victoria = 0
                        self.clicks_victoria += 1
                        if self.clicks_victoria >= 3:
                            self.clicks_victoria = 0
                            self.cambiar_estado(ESTADO_MENU)
                    elif self.estado == ESTADO_TRANSICION: self.crear_horda(); self.cambiar_estado(ESTADO_JUGANDO)
                    elif self.estado == ESTADO_SELECCION_RECOMPENSA_BOSS:
                        if ev.key == pygame.K_1: self.aplicar_recompensa_boss(0)
                        elif ev.key == pygame.K_2: self.aplicar_recompensa_boss(1)
                        elif ev.key == pygame.K_3: self.aplicar_recompensa_boss(2)
                        self.cambiar_estado(ESTADO_TRANSICION)
                    elif self.estado == ESTADO_SELECCION_MEJORA:
                        if ev.key == pygame.K_1: self.aplicar_mejora_permanente(1)
                        elif ev.key == pygame.K_2: self.aplicar_mejora_permanente(2)
                        elif ev.key == pygame.K_3: self.aplicar_mejora_permanente(3)
                    elif self.estado == ESTADO_DEBUG_MENU:
                        if ev.key == pygame.K_F12: self.cambiar_estado(ESTADO_JUGANDO)
            if self.estado == ESTADO_JUGANDO and self.controles_tactiles_activados:
                m_izq = False
                m_der = False
                disparando = False

                for tid in list(self.toques_activos.keys()):
                    if tid in self.toques_activos:
                        tx, ty = self.toques_activos[tid]
                        if tx is None or ty is None:
                            continue
                        if self.zona_toque_izq.collidepoint(tx, ty):
                            m_izq = True
                        if self.zona_toque_der.collidepoint(tx, ty):
                            m_der = True
                        if self.zona_toque_disparo.collidepoint(tx, ty):
                            disparando = True

                self.mago.direccion_touch = -1 if m_izq and not m_der else (1 if m_der and not m_izq else 0)

                if disparando and self.mago.puede_disparar():
                    self.mago.disparar(self.monstruos)
            self.update(); self.dibujar()
        pygame.quit(); sys.exit()

if __name__ == "__main__":
    asyncio.run(Juego().ejecutar())