"""
================================================================================
NEON CYBER DASH // 60-Second High-Energy Retro Arcade
================================================================================
Genre: Top-Down Cyber Action / Endless Dodge & Collect
Controls:
    - WASD / Arrow Keys : Smooth 8-Directional Vector Movement
    - Spacebar          : EMP Dash & Shockwave Pulse (3.5s cooldown)
    - R                 : Quick Restart (on Game Over or during play)
    - M                 : Toggle Sound Synthesis
    - Esc               : Quit Game

Rules & Mechanics:
    - 60-Second Match Countdown.
    - Collect Energy Cores (+100 points).
    - Combo Multiplier: Collect items within 3.0s to build multiplier up to 5x!
    - 3 Lives: Collisions trigger 1.5s invulnerability flash and screen shake.
    - Twist: Every 15 seconds, speed & spawn rate increase by 20%, and a
      special "Risk/Reward Bonus Orb" spawns temporarily (+500 * combo).
    - Arcade Initials entry screen & Persistent Local High Scores.
================================================================================
"""

import sys
import math
import random
import json
import os
import pygame

# Initialize Pygame
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except Exception:
    pass

# Display Dimensions & Settings
WIDTH, HEIGHT = 1000, 700
FPS = 60
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON CYBER DASH // Retro Arcade Action")
CLOCK = pygame.time.Clock()

# Neon Palette (Cyberpunk Synthwave)
COLOR_BG = (6, 6, 20)
COLOR_CYAN = (0, 243, 255)
COLOR_MAGENTA = (255, 0, 119)
COLOR_LIME = (57, 255, 20)
COLOR_YELLOW = (255, 230, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (120, 136, 168)
COLOR_RED = (255, 30, 60)
COLOR_DARK_PANEL = (12, 14, 35)

# Fonts
FONT_TITLE = pygame.font.SysApt = pygame.font.SysFont("impact", 54) if "impact" in pygame.font.get_fonts() else pygame.font.Font(None, 64)
FONT_HUD = pygame.font.SysFont("couriernew", 22, bold=True)
FONT_LARGE = pygame.font.SysFont("impact", 36)
FONT_SMALL = pygame.font.SysFont("couriernew", 14, bold=True)
FONT_MED = pygame.font.SysFont("couriernew", 18, bold=True)


# ==============================================================================
# PROCEDURAL RETRO SYNTH AUDIO (Zero external sound files required!)
# ==============================================================================
class SynthAudio:
    """Generates 8-bit / 16-bit retro arcade tones procedurally."""
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self._build_sound_bank()

    def _build_sound_bank(self):
        try:
            self.sounds['pickup'] = self._make_tone([520, 780, 1040], 0.12, 'square', 0.25)
            self.sounds['bonus'] = self._make_tone([523, 659, 784, 1046], 0.25, 'triangle', 0.35)
            self.sounds['hit'] = self._make_noise(0.25, 0.4)
            self.sounds['dash'] = self._make_tone([300, 180, 80], 0.2, 'saw', 0.35)
            self.sounds['surge'] = self._make_tone([380, 520, 380, 520], 0.3, 'square', 0.3)
            self.sounds['tick'] = self._make_tone([900], 0.04, 'sine', 0.15)
        except Exception:
            self.enabled = False

    def _make_tone(self, freq_list, duration, shape='sine', volume=0.3):
        try:
            import numpy as np
            sample_rate = 44100
            total_samples = int(sample_rate * duration)
            samples = np.zeros(total_samples, dtype=np.float32)
            segment_len = total_samples // len(freq_list)

            for idx, freq in enumerate(freq_list):
                start = idx * segment_len
                end = total_samples if idx == len(freq_list) - 1 else (idx + 1) * segment_len
                t = np.linspace(0, (end - start) / sample_rate, end - start, False)
                if shape == 'square':
                    wave = np.sign(np.sin(2 * np.pi * freq * t))
                elif shape == 'triangle':
                    wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
                elif shape == 'saw':
                    wave = 2 * (t * freq - np.floor(t * freq + 0.5))
                else:
                    wave = np.sin(2 * np.pi * freq * t)
                # Exponential decay envelope
                envelope = np.exp(-3.0 * np.linspace(0, 1, end - start))
                samples[start:end] = wave * envelope

            samples = (samples * volume * 32767).astype(np.int16)
            stereo = np.column_stack((samples, samples))
            return pygame.sndarray.make_sound(stereo)
        except Exception:
            return None

    def _make_noise(self, duration, volume=0.3):
        try:
            import numpy as np
            sample_rate = 44100
            total_samples = int(sample_rate * duration)
            samples = np.random.uniform(-1, 1, total_samples).astype(np.float32)
            envelope = np.exp(-4.0 * np.linspace(0, 1, total_samples))
            samples = (samples * envelope * volume * 32767).astype(np.int16)
            stereo = np.column_stack((samples, samples))
            return pygame.sndarray.make_sound(stereo)
        except Exception:
            return None

    def play(self, sound_key):
        if not self.enabled or sound_key not in self.sounds:
            return
        snd = self.sounds.get(sound_key)
        if snd:
            try:
                snd.play()
            except Exception:
                pass


audio = SynthAudio()


# ==============================================================================
# HIGH SCORE & LEADERBOARD MANAGEMENT
# ==============================================================================
SAVE_FILE = "neon_scores.json"

def load_high_scores():
    default_scores = [
        {"initials": "NEO", "score": 35000},
        {"initials": "CYB", "score": 28000},
        {"initials": "RUN", "score": 21500},
        {"initials": "DSH", "score": 16000},
        {"initials": "ACE", "score": 10000}
    ]
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return default_scores

def save_high_scores(scores):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(scores[:5], f, indent=2)
    except Exception:
        pass


# ==============================================================================
# VISUAL EFFECTS (Particles, Shockwaves, Floating Text)
# ==============================================================================
class Particle:
    def __init__(self, x, y, color, speed=4, size=4, life=0.5):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.initial_size = size
        self.life = life
        self.max_life = life
        angle = random.uniform(0, 2 * math.pi)
        spd = random.uniform(1, speed)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.life -= dt
        if self.life > 0:
            self.size = max(1, self.initial_size * (self.life / self.max_life))

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
        surface.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class Shockwave:
    def __init__(self, x, y, max_radius=180, color=COLOR_CYAN, speed=7):
        self.x = x
        self.y = y
        self.radius = 6
        self.max_radius = max_radius
        self.color = color
        self.speed = speed

    def update(self, dt):
        self.radius += self.speed * dt * 60

    def draw(self, surface):
        if self.radius >= self.max_radius:
            return
        alpha = max(0, int(255 * (1.0 - (self.radius / self.max_radius))))
        surf = pygame.Surface((int(self.radius * 2 + 4), int(self.radius * 2 + 4)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (int(self.radius + 2), int(self.radius + 2)), int(self.radius), 2)
        surface.blit(surf, (int(self.x - self.radius - 2), int(self.y - self.radius - 2)))


class FloatingText:
    def __init__(self, text, x, y, color=COLOR_CYAN, size=20):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = 1.0
        self.font = pygame.font.SysFont("impact", size)

    def update(self, dt):
        self.y -= 35 * dt
        self.life -= 1.2 * dt

    def draw(self, surface):
        if self.life <= 0:
            return
        rendered = self.font.render(self.text, True, self.color)
        alpha = max(0, min(255, int(255 * self.life)))
        rendered.set_alpha(alpha)
        surface.blit(rendered, (self.x - rendered.get_width() // 2, self.y))


# ==============================================================================
# GAME ENTITIES
# ==============================================================================
class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.vx = 0.0
        self.vy = 0.0
        self.speed = 360.0
        self.radius = 16
        self.angle = -math.pi / 2
        self.invulnerable_timer = 0.0
        self.dash_active = False
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.dash_cooldown_max = 3.5
        self.trail = []

    def update(self, dt, keys):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.dash_active:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.dash_active = False

        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0

        length = math.hypot(dx, dy)
        curr_speed = self.speed * (2.2 if self.dash_active else 1.0)

        if length > 0:
            self.angle = math.atan2(dy, dx)
            self.vx = (dx / length) * curr_speed
            self.vy = (dy / length) * curr_speed
        else:
            self.vx *= 0.85
            self.vy *= 0.85

        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bounds Clamping
        pad = 24
        self.x = max(pad, min(WIDTH - pad, self.x))
        self.y = max(pad + 40, min(HEIGHT - pad, self.y))

        # Trail recording
        if math.hypot(self.vx, self.vy) > 10 or self.dash_active:
            self.trail.insert(0, (self.x, self.y, self.dash_active))
            if len(self.trail) > 10:
                self.trail.pop()
        elif self.trail:
            self.trail.pop()

    def draw(self, surface):
        # Draw Ghost trail
        for i, (tx, ty, is_dash) in enumerate(self.trail):
            alpha = int((1.0 - i / len(self.trail)) * (160 if is_dash else 80))
            col = COLOR_MAGENTA if is_dash else COLOR_CYAN
            tsurf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(tsurf, (*col, alpha), (15, 15), int(self.radius * (0.8 - i * 0.05)))
            surface.blit(tsurf, (tx - 15, ty - 15))

        # Invulnerability flash
        if self.invulnerable_timer > 0 and int(self.invulnerable_timer * 15) % 2 == 0:
            return

        # Draw sleek cyber vessel
        color = COLOR_MAGENTA if self.dash_active else COLOR_CYAN
        nose = (self.x + math.cos(self.angle) * self.radius * 1.4,
                self.y + math.sin(self.angle) * self.radius * 1.4)
        wing_left = (self.x + math.cos(self.angle + 2.4) * self.radius,
                     self.y + math.sin(self.angle + 2.4) * self.radius)
        wing_right = (self.x + math.cos(self.angle - 2.4) * self.radius,
                      self.y + math.sin(self.angle - 2.4) * self.radius)
        recess = (self.x - math.cos(self.angle) * (self.radius * 0.4),
                  self.y - math.sin(self.angle) * (self.radius * 0.4))

        points = [nose, wing_right, recess, wing_left]
        pygame.draw.polygon(surface, (10, 16, 40), points)
        pygame.draw.polygon(surface, color, points, 2)

        # Cockpit glow
        cockpit = (int(self.x + math.cos(self.angle) * 3), int(self.y + math.sin(self.angle) * 3))
        pygame.draw.circle(surface, COLOR_YELLOW if self.dash_active else COLOR_LIME, cockpit, 4)


class EnergyCore:
    def __init__(self, x=None, y=None):
        self.x = x or random.uniform(60, WIDTH - 60)
        self.y = y or random.uniform(100, HEIGHT - 80)
        self.radius = 12
        self.angle = 0.0

    def update(self, dt):
        self.angle += 3.0 * dt

    def draw(self, surface):
        # Draw rotating neon diamond
        points = []
        for i in range(4):
            th = self.angle + i * (math.pi / 2)
            px = self.x + math.cos(th) * self.radius
            py = self.y + math.sin(th) * self.radius
            points.append((px, py))
        pygame.draw.polygon(surface, COLOR_LIME, points, 2)
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), 4)


class BonusOrb:
    def __init__(self):
        self.x = random.uniform(120, WIDTH - 120)
        self.y = random.uniform(140, HEIGHT - 120)
        self.radius = 18
        self.life_time = 8.0
        self.angle = 0.0

    def update(self, dt):
        self.angle += 3.5 * dt
        self.life_time -= dt

    def draw(self, surface):
        if self.life_time <= 0:
            return
        if self.life_time < 2.5 and int(self.life_time * 8) % 2 == 0:
            return
        # Pulsing golden orb with satellites
        pygame.draw.circle(surface, COLOR_YELLOW, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, COLOR_MAGENTA, (int(self.x), int(self.y)), int(self.radius * 1.4), 2)
        for i in range(3):
            th = self.angle + i * (2 * math.pi / 3)
            ox = self.x + math.cos(th) * (self.radius * 1.4)
            oy = self.y + math.sin(th) * (self.radius * 1.4)
            pygame.draw.circle(surface, COLOR_YELLOW, (int(ox), int(oy)), 4)


class Drone:
    def __init__(self, drone_type='chaser', speed_mult=1.0):
        self.type = drone_type
        self.radius = 14
        self.speed_mult = speed_mult
        self.color = COLOR_MAGENTA

        if random.random() < 0.5:
            self.x = 20 if random.random() < 0.5 else WIDTH - 20
            self.y = random.uniform(80, HEIGHT - 80)
        else:
            self.x = random.uniform(40, WIDTH - 40)
            self.y = 70 if random.random() < 0.5 else HEIGHT - 30

        if self.type == 'chaser':
            self.base_speed = 135
            self.vx, self.vy = 0, 0
        else:
            self.base_speed = 180
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle) * self.base_speed * self.speed_mult
            self.vy = math.sin(angle) * self.base_speed * self.speed_mult
        self.angle = 0.0

    def update(self, dt, player):
        speed = self.base_speed * self.speed_mult
        if self.type == 'chaser':
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.vx = (dx / dist) * speed
                self.vy = (dy / dist) * speed
            self.angle = math.atan2(self.vy, self.vx)
        else:
            if self.x - self.radius <= 10 or self.x + self.radius >= WIDTH - 10:
                self.vx = -self.vx
            if self.y - self.radius <= 60 or self.y + self.radius >= HEIGHT - 10:
                self.vy = -self.vy
            self.angle = math.atan2(self.vy, self.vx)

        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface):
        nose = (self.x + math.cos(self.angle) * self.radius * 1.3,
                self.y + math.sin(self.angle) * self.radius * 1.3)
        right = (self.x + math.cos(self.angle + 2.5) * self.radius,
                 self.y + math.sin(self.angle + 2.5) * self.radius)
        left = (self.x + math.cos(self.angle - 2.5) * self.radius,
                self.y + math.sin(self.angle - 2.5) * self.radius)
        pygame.draw.polygon(surface, (20, 4, 12), [nose, right, left])
        pygame.draw.polygon(surface, self.color, [nose, right, left], 2)
        pygame.draw.circle(surface, COLOR_RED, (int(self.x), int(self.y)), 4)


# ==============================================================================
# MAIN GAME CLASS
# ==============================================================================
class Game:
    def __init__(self):
        self.state = "START"  # "START", "PLAYING", "GAMEOVER"
        self.high_scores = load_high_scores()
        self.player = Player()
        self.energy_cores = []
        self.drones = []
        self.bonus_orb = None
        self.particles = []
        self.shockwaves = []
        self.floating_texts = []

        self.score = 0
        self.match_timer = 60.0
        self.lives = 3
        self.combo_mult = 1
        self.combo_timer = 0.0
        self.combo_window = 3.0
        self.max_combo = 1
        self.cores_collected = 0
        self.surge_stage = 1
        self.enemy_speed_mult = 1.0
        self.spawn_timer = 0.0
        self.spawn_interval = 2.4
        self.next_surge = 45.0
        self.initials = ['A', 'A', 'A']
        self.init_col = 0
        self.gameover_reason = ""
        self.grid_offset = 0

    def start_match(self):
        self.score = 0
        self.match_timer = 60.0
        self.lives = 3
        self.combo_mult = 1
        self.combo_timer = 0.0
        self.max_combo = 1
        self.cores_collected = 0
        self.surge_stage = 1
        self.enemy_speed_mult = 1.0
        self.spawn_timer = 0.0
        self.spawn_interval = 2.4
        self.next_surge = 45.0

        self.player.reset()
        self.energy_cores = [EnergyCore() for _ in range(5)]
        self.drones = [Drone('chaser'), Drone('sweeper')]
        self.bonus_orb = None
        self.particles.clear()
        self.shockwaves.clear()
        self.floating_texts.clear()
        self.state = "PLAYING"

    def trigger_ability(self):
        if self.state != "PLAYING" or self.player.dash_cooldown > 0:
            return
        self.player.dash_active = True
        self.player.dash_timer = 0.35
        self.player.dash_cooldown = self.player.dash_cooldown_max
        self.player.invulnerable_timer = 0.6

        self.shockwaves.append(Shockwave(self.player.x, self.player.y, 220, COLOR_CYAN, 8))
        audio.play('dash')

        # Clear nearby drones
        for d in self.drones[:]:
            dist = math.hypot(d.x - self.player.x, d.y - self.player.y)
            if dist < 200:
                self.drones.remove(d)
                self.spawn_particles(d.x, d.y, COLOR_MAGENTA, 15)
                pts = 150 * self.combo_mult
                self.score += pts
                self.floating_texts.append(FloatingText(f"EMP +{pts}", d.x, d.y, COLOR_CYAN, 20))
                audio.play('hit')

    def spawn_particles(self, x, y, color, count=16):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed=5, size=4, life=0.5))

    def trigger_surge(self):
        self.surge_stage += 1
        self.enemy_speed_mult += 0.20
        self.spawn_interval = max(0.8, self.spawn_interval * 0.82)
        audio.play('surge')

        self.floating_texts.append(FloatingText(f"SURGE STAGE {self.surge_stage}! +20% SPEED", WIDTH // 2, HEIGHT // 2 - 40, COLOR_YELLOW, 28))
        self.bonus_orb = BonusOrb()
        audio.play('bonus')
        self.drones.append(Drone(random.choice(['chaser', 'sweeper']), self.enemy_speed_mult))

    def take_damage(self):
        if self.player.invulnerable_timer > 0:
            return
        self.lives -= 1
        self.player.invulnerable_timer = 1.5
        self.combo_mult = 1
        self.combo_timer = 0.0
        audio.play('hit')
        self.spawn_particles(self.player.x, self.player.y, COLOR_RED, 25)
        self.shockwaves.append(Shockwave(self.player.x, self.player.y, 120, COLOR_RED, 6))
        self.floating_texts.append(FloatingText("-1 LIFE!", self.player.x, self.player.y - 20, COLOR_RED, 24))

        if self.lives <= 0:
            self.end_match("SYSTEM INTEGRITY LOST: ZERO LIVES REMAINING")

    def end_match(self, reason):
        self.state = "GAMEOVER"
        self.gameover_reason = reason
        audio.play('hit')

    def save_current_score(self):
        pilot = "".join(self.initials)
        self.high_scores.append({"initials": pilot, "score": int(self.score)})
        self.high_scores.sort(key=lambda item: item['score'], reverse=True)
        self.high_scores = self.high_scores[:5]
        save_high_scores(self.high_scores)
        audio.play('bonus')

    def update(self, dt):
        keys = pygame.key.get_pressed()

        if self.state == "PLAYING":
            self.match_timer -= dt
            if self.match_timer <= 0:
                self.match_timer = 0
                self.end_match("60-SECOND MATCH COMPLETED!")

            # Low time tick
            if self.match_timer <= 5.0 and int(self.match_timer * 10) % 10 == 0:
                audio.play('tick')

            # 15s Twist Surge
            if self.match_timer <= self.next_surge and self.next_surge > 0:
                self.trigger_surge()
                self.next_surge -= 15.0

            # Combo Timer Decay
            if self.combo_timer > 0:
                self.combo_timer -= dt
                if self.combo_timer <= 0:
                    self.combo_mult = 1
                    self.combo_timer = 0.0

            # Drone Spawn
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0.0
                self.drones.append(Drone(random.choice(['chaser', 'sweeper']), self.enemy_speed_mult))

            # Player update
            self.player.update(dt, keys)

            # Energy Cores
            for core in self.energy_cores[:]:
                core.update(dt)
                if math.hypot(core.x - self.player.x, core.y - self.player.y) < core.radius + self.player.radius:
                    self.cores_collected += 1
                    pts = 100 * self.combo_mult
                    self.score += pts

                    if self.combo_timer > 0:
                        self.combo_mult = min(5, self.combo_mult + 1)
                    else:
                        self.combo_mult = 1
                    self.combo_timer = self.combo_window
                    self.max_combo = max(self.max_combo, self.combo_mult)

                    audio.play('pickup')
                    self.spawn_particles(core.x, core.y, COLOR_LIME, 12)
                    self.floating_texts.append(FloatingText(f"+{pts} (x{self.combo_mult})", core.x, core.y - 10, COLOR_LIME, 18))
                    self.energy_cores.remove(core)
                    self.energy_cores.append(EnergyCore())

            # Bonus Orb
            if self.bonus_orb:
                self.bonus_orb.update(dt)
                if self.bonus_orb.life_time <= 0:
                    self.bonus_orb = None
                elif math.hypot(self.bonus_orb.x - self.player.x, self.bonus_orb.y - self.player.y) < self.bonus_orb.radius + self.player.radius:
                    pts = 500 * self.combo_mult
                    self.score += pts
                    self.combo_mult = 5
                    self.combo_timer = self.combo_window
                    audio.play('bonus')
                    self.spawn_particles(self.bonus_orb.x, self.bonus_orb.y, COLOR_YELLOW, 25)
                    self.shockwaves.append(Shockwave(self.bonus_orb.x, self.bonus_orb.y, 180, COLOR_YELLOW, 7))
                    self.floating_texts.append(FloatingText(f"SUPER BONUS +{pts}!", self.bonus_orb.x, self.bonus_orb.y - 20, COLOR_YELLOW, 24))
                    self.bonus_orb = None

            # Drones Collision
            for drone in self.drones[:]:
                drone.update(dt, self.player)
                if math.hypot(drone.x - self.player.x, drone.y - self.player.y) < drone.radius + self.player.radius:
                    if self.player.dash_active:
                        self.drones.remove(drone)
                        pts = 200 * self.combo_mult
                        self.score += pts
                        audio.play('hit')
                        self.spawn_particles(drone.x, drone.y, COLOR_CYAN, 18)
                        self.floating_texts.append(FloatingText(f"DASH KILL +{pts}", drone.x, drone.y, COLOR_CYAN, 20))
                    else:
                        self.take_damage()

        # Update visuals
        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)
        for sw in self.shockwaves[:]:
            sw.update(dt)
            if sw.radius >= sw.max_radius:
                self.shockwaves.remove(sw)
        for ft in self.floating_texts[:]:
            ft.update(dt)
            if ft.life <= 0:
                self.floating_texts.remove(ft)

    def draw(self, surface):
        surface.fill(COLOR_BG)

        # Draw Grid
        self.grid_offset = (self.grid_offset + 0.5) % 40
        for x in range(0, WIDTH, 40):
            pygame.draw.line(surface, (15, 20, 45), (x, 0), (x, HEIGHT), 1)
        for y in range(int(self.grid_offset), HEIGHT, 40):
            pygame.draw.line(surface, (15, 20, 45), (0, y), (WIDTH, y), 1)

        # Arena Outline
        pygame.draw.rect(surface, (0, 180, 220), (10, 50, WIDTH - 20, HEIGHT - 60), 2)

        # Render Entities
        for sw in self.shockwaves:
            sw.draw(surface)
        for core in self.energy_cores:
            core.draw(surface)
        if self.bonus_orb:
            self.bonus_orb.draw(surface)
        for drone in self.drones:
            drone.draw(surface)
        for p in self.particles:
            p.draw(surface)
        if self.state == "PLAYING":
            self.player.draw(surface)
        for ft in self.floating_texts:
            ft.draw(surface)

        # Render Top HUD
        self.draw_hud(surface)

        # Render Overlays
        if self.state == "START":
            self.draw_start_screen(surface)
        elif self.state == "GAMEOVER":
            self.draw_gameover_screen(surface)

    def draw_hud(self, surface):
        # Top Bar Background Panel
        pygame.draw.rect(surface, COLOR_DARK_PANEL, (0, 0, WIDTH, 50))
        pygame.draw.line(surface, COLOR_CYAN, (0, 50), (WIDTH, 50), 2)

        # Score & High Score
        sc_lbl = FONT_SMALL.render("SCORE", True, COLOR_GRAY)
        sc_val = FONT_HUD.render(f"{int(self.score):06d}", True, COLOR_CYAN)
        surface.blit(sc_lbl, (20, 6))
        surface.blit(sc_val, (20, 22))

        # Lives Remaining
        for i in range(3):
            col = COLOR_MAGENTA if i < self.lives else (50, 20, 35)
            pygame.draw.circle(surface, col, (140 + i * 22, 28), 8)

        # Match Timer Center
        time_col = COLOR_RED if self.match_timer <= 10.0 else COLOR_YELLOW
        time_text = FONT_LARGE.render(f"{max(0.0, self.match_timer):.1f}s", True, time_col)
        surface.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 8))

        # Combo Badge & Decay Bar
        combo_str = f"COMBO {self.combo_mult}x" if self.combo_mult < 5 else "5x MAX!"
        combo_col = COLOR_YELLOW if self.combo_mult >= 5 else (COLOR_LIME if self.combo_mult > 1 else COLOR_GRAY)
        cb_text = FONT_SMALL.render(combo_str, True, combo_col)
        surface.blit(cb_text, (WIDTH // 2 - cb_text.get_width() // 2, 38))

        # Ability Status (Bottom-left)
        ability_col = COLOR_CYAN if self.player.dash_cooldown <= 0 else COLOR_MAGENTA
        ability_status = "READY" if self.player.dash_cooldown <= 0 else f"{self.player.dash_cooldown:.1f}s"
        ability_text = FONT_SMALL.render(f"[SPACE] EMP DASH: {ability_status}", True, ability_col)
        surface.blit(ability_text, (20, HEIGHT - 26))

        # Surge Info (Bottom-right)
        surge_text = FONT_SMALL.render(f"SURGE: STAGE {self.surge_stage} (+{(self.surge_stage-1)*20}%)", True, COLOR_YELLOW)
        surface.blit(surge_text, (WIDTH - surge_text.get_width() - 20, HEIGHT - 26))

    def draw_start_screen(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 4, 16, 220))
        surface.blit(overlay, (0, 0))

        title = FONT_TITLE.render("NEON CYBER DASH", True, COLOR_CYAN)
        sub = FONT_SMALL.render("// 60-SECOND HIGH-ENERGY RETRO ARCADE //", True, COLOR_MAGENTA)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 160))
        surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 230))

        # Info Box
        card = pygame.Rect(WIDTH // 2 - 250, 270, 500, 180)
        pygame.draw.rect(surface, (12, 16, 40), card)
        pygame.draw.rect(surface, COLOR_CYAN, card, 1)

        lines = [
            "• ARROWS / WASD : Smooth Movement",
            "• SPACEBAR      : EMP Dash & Shockwave Blast",
            "• COMBO SYSTEM  : Collect cores within 3s for 5x multiplier",
            "• TWIST         : Every 15s speed +20% & Gold Orb spawns!",
            "• GOAL          : Maximize score in 60s before time expires!"
        ]
        for idx, line in enumerate(lines):
            t = FONT_SMALL.render(line, True, COLOR_WHITE)
            surface.blit(t, (card.x + 20, card.y + 20 + idx * 28))

        btn = FONT_LARGE.render("PRESS [ENTER] TO INITIATE RUN", True, COLOR_LIME)
        surface.blit(btn, (WIDTH // 2 - btn.get_width() // 2, 490))

    def draw_gameover_screen(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 4, 16, 235))
        surface.blit(overlay, (0, 0))

        title = FONT_TITLE.render("MATCH COMPLETED", True, COLOR_RED)
        reason = FONT_SMALL.render(self.gameover_reason, True, COLOR_YELLOW)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))
        surface.blit(reason, (WIDTH // 2 - reason.get_width() // 2, 135))

        # Score Summary Card
        card = pygame.Rect(WIDTH // 2 - 240, 165, 480, 80)
        pygame.draw.rect(surface, (12, 16, 40), card)
        pygame.draw.rect(surface, COLOR_MAGENTA, card, 1)

        s_txt = FONT_HUD.render(f"SCORE: {int(self.score)}", True, COLOR_CYAN)
        c_txt = FONT_HUD.render(f"CORES: {self.cores_collected}", True, COLOR_LIME)
        m_txt = FONT_HUD.render(f"MAX COMBO: {self.max_combo}x", True, COLOR_YELLOW)
        surface.blit(s_txt, (card.x + 20, card.y + 26))
        surface.blit(c_txt, (card.x + 180, card.y + 26))
        surface.blit(m_txt, (card.x + 320, card.y + 26))

        # Initials Picker
        init_box = pygame.Rect(WIDTH // 2 - 160, 260, 320, 100)
        pygame.draw.rect(surface, (10, 14, 35), init_box)
        pygame.draw.rect(surface, COLOR_YELLOW, init_box, 1)

        lbl = FONT_SMALL.render("PILOT INITIALS (LEFT/RIGHT & UP/DOWN)", True, COLOR_YELLOW)
        surface.blit(lbl, (init_box.x + 15, init_box.y + 12))

        for i in range(3):
            char_col = COLOR_YELLOW if i == self.init_col else COLOR_CYAN
            char_surf = FONT_LARGE.render(self.initials[i], True, char_col)
            surface.blit(char_surf, (init_box.x + 70 + i * 65, init_box.y + 45))

        # Leaderboard
        lb_box = pygame.Rect(WIDTH // 2 - 180, 380, 360, 170)
        pygame.draw.rect(surface, (8, 10, 25), lb_box)
        pygame.draw.rect(surface, COLOR_CYAN, lb_box, 1)
        lb_title = FONT_SMALL.render("HALL OF CYBER LEGENDS", True, COLOR_CYAN)
        surface.blit(lb_title, (lb_box.x + 80, lb_box.y + 10))

        for idx, entry in enumerate(self.high_scores):
            col = COLOR_YELLOW if idx == 0 else COLOR_WHITE
            row = FONT_SMALL.render(f"#{idx+1}  {entry['initials']}  ......  {entry['score']:06d}", True, col)
            surface.blit(row, (lb_box.x + 40, lb_box.y + 36 + idx * 24))

        restart_msg = FONT_MED.render("PRESS [R] OR [ENTER] TO PLAY AGAIN", True, COLOR_LIME)
        surface.blit(restart_msg, (WIDTH // 2 - restart_msg.get_width() // 2, 580))


def main():
    game = Game()
    running = True

    while running:
        dt = CLOCK.tick(FPS) / 1000.0
        dt = min(dt, 0.1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if game.state == "START":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        game.start_match()

                elif game.state == "PLAYING":
                    if event.key == pygame.K_SPACE:
                        game.trigger_ability()
                    elif event.key == pygame.K_r:
                        game.start_match()
                    elif event.key == pygame.K_m:
                        audio.enabled = not audio.enabled

                elif game.state == "GAMEOVER":
                    if event.key in (pygame.K_r, pygame.K_RETURN):
                        game.save_current_score()
                        game.start_match()
                    elif event.key == pygame.K_LEFT:
                        game.init_col = (game.init_col - 1) % 3
                    elif event.key == pygame.K_RIGHT:
                        game.init_col = (game.init_col + 1) % 3
                    elif event.key == pygame.K_UP:
                        c = game.initials[game.init_col]
                        game.initials[game.init_col] = chr(65 + ((ord(c) - 65 - 1) % 26))
                    elif event.key == pygame.K_DOWN:
                        c = game.initials[game.init_col]
                        game.initials[game.init_col] = chr(65 + ((ord(c) - 65 + 1) % 26))

        game.update(dt)
        game.draw(SCREEN)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

