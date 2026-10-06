import sys
import math
import random
import array
import asyncio  # لتشغيل اللعبة على المتصفح عبر Pygbag
import pygame

# --- استدعاء محرك الصوت والموسيقى من الملف الخارجي ---
from sound_manager import SoundManager

# --- إعدادات النافذة واللعبة ---
WIDTH = 500
HEIGHT = 700
FPS = 60

WALL_COLOR = (45, 30, 60)
BRICK_LINE = (30, 20, 40)

STAGE_THEMES = [
    {"bg": (12, 18, 45), "platform": (210, 110, 40), "edge": (250, 180, 70), "full": (40, 180, 220), "name": "Tower Base"},
    {"bg": (45, 10, 30), "platform": (180, 40, 90), "edge": (240, 100, 150), "full": (50, 210, 120), "name": "Magma Core"},
    {"bg": (10, 40, 35), "platform": (30, 160, 140), "edge": (100, 230, 210), "full": (220, 180, 40), "name": "Emerald Sky"},
    {"bg": (20, 25, 60), "platform": (140, 70, 200), "edge": (200, 130, 255), "full": (255, 100, 180), "name": "Neon Heights"},
]

WIN_BG_COLOR = (15, 45, 30)
LOSE_BG_COLOR = (45, 15, 15)

SKIN_COLOR = (235, 190, 150)
JACKET_BLUE = (50, 125, 175)
TSHIRT_BLACK = (25, 25, 25)
PANTS_DARK = (40, 50, 65)
CAP_COLOR = (60, 55, 45)


class GameState:
    MENU = 1
    PLAYING = 2
    STAGE_CLEAR = 3
    GAME_OVER = 4


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-4, -1)
        self.color = color
        self.lifetime = random.randint(15, 30)
        self.size = random.randint(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.lifetime -= 1

    def draw(self, surface, camera_y):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y - camera_y)), self.size)


class Player:
    def __init__(self):
        self.width = 36
        self.height = 52
        self.x = WIDTH / 2 - 18
        self.y = HEIGHT - 100
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.rotation = 0.0
        self.is_flipping = False
        self.wall_bounced = False

    def update(self, left, right, snd_bounce, game_ref):
        accel = 0.9
        max_speed = 12.0
        friction = 0.86

        if left:
            self.vx -= accel
            self.facing_right = False
        elif right:
            self.vx += accel
            self.facing_right = True
        else:
            self.vx *= friction

        self.vx = max(-max_speed, min(max_speed, self.vx))
        self.x += self.vx

        # الارتداد من الحوائط
        if self.x < 25:
            self.x = 25
            if abs(self.vx) > 4.0:
                self.vx = abs(self.vx) * 1.2
                self.facing_right = True
                self.wall_bounced = True
                game_ref.trigger_shake(6)
                game_ref.add_particles(self.x, self.y + 20, (255, 255, 255))
                if snd_bounce: snd_bounce.play()
            else:
                self.vx *= -0.4
        elif self.x > WIDTH - self.width - 25:
            self.x = WIDTH - self.width - 25
            if abs(self.vx) > 4.0:
                self.vx = -abs(self.vx) * 1.2
                self.facing_right = False
                self.wall_bounced = True
                game_ref.trigger_shake(6)
                game_ref.add_particles(self.x + self.width, self.y + 20, (255, 255, 255))
                if snd_bounce: snd_bounce.play()
            else:
                self.vx *= -0.4

        # جاذبية القفز
        self.vy += 0.62
        self.y += self.vy

        if self.is_flipping:
            self.rotation += 40 if self.facing_right else -40
            if abs(self.rotation) >= 360:
                self.rotation = 0.0
                self.is_flipping = False
        else:
            self.rotation = 0.0

    def jump(self, sound_effect, super_jump_sound, game_ref):
        if self.on_ground:
            speed_bonus = abs(self.vx) * 0.95
            
            # قفزة عالية وخارقة
            if self.wall_bounced or abs(self.vx) > 7.0:
                self.vy = -(17.5 + speed_bonus)
                self.is_flipping = True
                game_ref.trigger_shake(8)
                game_ref.add_particles(self.x + 18, self.y + 50, (255, 220, 100))
                if super_jump_sound: super_jump_sound.play()
            else:
                self.vy = -(15.0 + speed_bonus)
                if abs(self.vx) > 5.0:
                    self.is_flipping = True
                game_ref.add_particles(self.x + 18, self.y + 50, (200, 200, 200))
                if sound_effect: sound_effect.play()

            self.on_ground = False
            self.wall_bounced = False

    def draw(self, surface, camera_y):
        draw_y = int(self.y - camera_y)
        player_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(player_surface, (255, 255, 255), (4, 46, 12, 6))
        pygame.draw.rect(player_surface, (255, 255, 255), (20, 46, 12, 6))
        pygame.draw.rect(player_surface, PANTS_DARK, (7, 32, 22, 15))
        pygame.draw.rect(player_surface, JACKET_BLUE, (3, 16, 30, 18))
        pygame.draw.rect(player_surface, TSHIRT_BLACK, (13, 17, 10, 17))
        pygame.draw.ellipse(player_surface, SKIN_COLOR, (9, 3, 18, 18))
        eye_x = 22 if self.facing_right else 12
        pygame.draw.rect(player_surface, (0, 0, 0), (eye_x, 10, 3, 3))
        pygame.draw.rect(player_surface, CAP_COLOR, (8, 3, 20, 6))
        peak_x = 20 if self.facing_right else 4
        pygame.draw.ellipse(player_surface, CAP_COLOR, (peak_x, 7, 12, 4))

        if self.rotation != 0:
            rotated_surface = pygame.transform.rotate(player_surface, -self.rotation)
            new_rect = rotated_surface.get_rect(center=(int(self.x + self.width / 2.0), draw_y + int(self.height / 2.0)))
            surface.blit(rotated_surface, new_rect.topleft)
        else:
            surface.blit(player_surface, (int(self.x), draw_y))


class Platform:
    def __init__(self, y, level_num, is_full_width):
        self.y = int(y)
        self.height = 18
        self.level_num = level_num
        self.is_full_width = is_full_width
        if is_full_width:
            self.x = 25
            self.width = WIDTH - 50
        else:
            min_w = 110
            max_w = max(min_w, 230 - (level_num // 10) * 10)
            self.width = random.randint(min_w, max_w)
            self.x = random.randint(30, WIDTH - self.width - 30)

    def draw(self, surface, camera_y, font, theme):
        draw_y = int(self.y - camera_y)
        color = theme["full"] if self.is_full_width else theme["platform"]
        pygame.draw.rect(surface, color, (self.x, draw_y, self.width, self.height), border_radius=8)
        pygame.draw.rect(surface, theme["edge"], (self.x, draw_y, self.width, 5))
        txt = font.render(str(self.level_num), True, (255, 255, 255))
        surface.blit(txt, (self.x + 8, draw_y + 2))


class IcyTowerGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2)
        pygame.font.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Icy Tower - Arabic Web Edition")
        self.clock = pygame.time.Clock()

        # تهيئة واستدعاء SoundManager للموسيقى والمؤثرات
        self.audio = SoundManager()
        self.bg_music = self.audio.generate_background_track(tempo_bpm=140)

        self.snd_jump = self.audio.generate_tone(300, 0.12, wave_type='square')
        self.snd_super_jump = self.audio.generate_tone(450, 0.2, wave_type='square')
        self.snd_bounce = self.audio.generate_tone(180, 0.08, wave_type='triangle')
        self.snd_win = self.audio.generate_tone(520, 0.5, wave_type='sine')
        self.snd_fail = self.audio.generate_tone(150, 0.4, wave_type='noise')

        self.font_small = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_large = pygame.font.SysFont("Impact", 28, bold=True)
        self.font_xlarge = pygame.font.SysFont("Impact", 38, bold=True)
        self.font_arabic = pygame.font.SysFont("Tahoma", 18, bold=True)
        self.font_arabic_large = pygame.font.SysFont("Tahoma", 26, bold=True)

        self.current_state = GameState.MENU
        self.current_stage_idx = 0
        self.highest_level = 0
        self.high_score = 0
        self.stage_level = 0
        self.combo_text = ""
        self.combo_timer = 0
        self.combo_bar_val = 0.0
        self.camera_y = 0.0
        self.shake_amount = 0
        self.particles = []
        self.platforms = []
        self.player = None

        self.easy_btn = pygame.Rect(150, 320, 200, 50)

        # أزرار اللمس للموبايل والمتصفح
        self.btn_left = pygame.Rect(20, HEIGHT - 90, 80, 70)
        self.btn_right = pygame.Rect(110, HEIGHT - 90, 80, 70)
        self.btn_jump = pygame.Rect(WIDTH - 110, HEIGHT - 90, 90, 70)

        self.left_pressed = False
        self.right_pressed = False

    def trigger_shake(self, amount):
        self.shake_amount = amount

    def add_particles(self, x, y, color):
        for _ in range(6):
            self.particles.append(Particle(x, y, color))

    def init_game(self, next_stage=False):
        if not next_stage:
            self.current_stage_idx = random.randint(0, len(STAGE_THEMES) - 1)
            self.highest_level = 0

        self.stage_level = 0
        self.player = Player()
        self.platforms = []
        self.particles = []
        self.base_scroll_speed = 0.4
        self.speed_factor = 0.012

        base_platform = Platform(HEIGHT - 40, 0, True)
        base_platform.x = WIDTH // 2 - 120
        base_platform.width = 240
        self.platforms.append(base_platform)

        for i in range(1, 15):
            is_full = (i % 20 == 0)
            self.platforms.append(Platform(HEIGHT - 40 - i * 70, i, is_full))

        self.camera_y = 0.0
        self.last_platform_level = 0
        self.combo_text = ""
        self.combo_timer = 0
        self.combo_bar_val = 0.0

    def start_game(self):
        self.init_game()
        self.bg_music.play(loops=-1)  # تشغيل الموسيقى عند بداية اللعب
        self.current_state = GameState.PLAYING

    def update_game(self):
        self.player.update(self.left_pressed, self.right_pressed, self.snd_bounce, self)

        target_camera_y = self.player.y - HEIGHT / 2.0
        if target_camera_y < self.camera_y:
            self.camera_y += (target_camera_y - self.camera_y) * 0.1

        self.camera_y -= (self.base_scroll_speed + (self.highest_level * self.speed_factor))
        self.player.on_ground = False

        if self.combo_bar_val > 0:
            self.combo_bar_val -= 0.8
            if self.combo_bar_val <= 0: self.combo_bar_val = 0.0

        if self.combo_timer > 0:
            self.combo_timer -= 1

        for p in self.particles[:]:
            p.update()
            if p.lifetime <= 0:
                self.particles.remove(p)

        if self.shake_amount > 0:
            self.shake_amount -= 1

        for p in self.platforms:
            if self.player.vy > 0 and (p.y <= self.player.y + self.player.height <= p.y + 15):
                if (self.player.x + self.player.width >= p.x + 5) and (self.player.x <= p.x + p.width - 5):
                    self.player.y = p.y - self.player.height
                    self.player.vy = 0
                    self.player.on_ground = True

                    level_diff = p.level_num - self.last_platform_level
                    if level_diff >= 2:
                        if level_diff == 2: self.combo_text = "GOOD!"
                        elif level_diff == 3: self.combo_text = "SWEET!"
                        elif level_diff == 4: self.combo_text = "GREAT!"
                        elif level_diff >= 5: self.combo_text = "SUPER " + "!" * (level_diff - 4)
                        self.combo_timer = 60
                        self.combo_bar_val = min(100.0, self.combo_bar_val + (level_diff * 22))

                    self.last_platform_level = p.level_num
                    if p.level_num > self.stage_level:
                        diff = p.level_num - self.stage_level
                        self.stage_level = p.level_num
                        self.highest_level += diff
                        if self.stage_level > self.high_score:
                            self.high_score = self.stage_level

                    if self.stage_level >= 100:
                        self.bg_music.stop()  # إيقاف الموسيقى عند الفوز
                        self.current_state = GameState.STAGE_CLEAR
                        self.snd_win.play()
                    break

        highest_platform_y = float(HEIGHT)
        max_lvl = 0
        for p in self.platforms:
            if p.y < highest_platform_y: highest_platform_y = p.y
            if p.level_num > max_lvl: max_lvl = p.level_num

        if highest_platform_y > self.camera_y - 100:
            next_lvl = max_lvl + 1
            is_full = (next_lvl % 20 == 0)
            self.platforms.append(Platform(highest_platform_y - 70, next_lvl, is_full))

        self.platforms = [p for p in self.platforms if p.y - self.camera_y <= HEIGHT + 50]

        if self.player.y - self.camera_y > HEIGHT:
            self.bg_music.stop()  # إيقاف الموسيقى عند الخسارة
            self.current_state = GameState.GAME_OVER
            self.snd_fail.play()

    def draw_touch_controls(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(s, (255, 255, 255, 60), self.btn_left, border_radius=10)
        pygame.draw.rect(s, (255, 255, 255, 60), self.btn_right, border_radius=10)
        pygame.draw.rect(s, (0, 255, 150, 90), self.btn_jump, border_radius=10)
        self.screen.blit(s, (0, 0))

        t_left = self.font_medium.render("<-", True, (255, 255, 255))
        t_right = self.font_medium.render("->", True, (255, 255, 255))
        t_jump = self.font_medium.render("JUMP", True, (255, 255, 255))

        self.screen.blit(t_left, t_left.get_rect(center=self.btn_left.center))
        self.screen.blit(t_right, t_right.get_rect(center=self.btn_right.center))
        self.screen.blit(t_jump, t_jump.get_rect(center=self.btn_jump.center))

    def draw(self):
        shake_x = random.randint(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        shake_y = random.randint(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0

        theme = STAGE_THEMES[self.current_stage_idx % len(STAGE_THEMES)]
        
        if self.current_state == GameState.STAGE_CLEAR:
            self.screen.fill(WIN_BG_COLOR)
        elif self.current_state == GameState.GAME_OVER:
            self.screen.fill(LOSE_BG_COLOR)
        else:
            self.screen.fill(theme["bg"])
        
        wall_w = 25
        pygame.draw.rect(self.screen, WALL_COLOR, (0 + shake_x, 0 + shake_y, wall_w, HEIGHT))
        pygame.draw.rect(self.screen, WALL_COLOR, (WIDTH - wall_w + shake_x, 0 + shake_y, wall_w, HEIGHT))

        if self.current_state == GameState.MENU:
            self.draw_menu()
            pygame.display.flip()
            return

        for p in self.platforms:
            p.draw(self.screen, self.camera_y - shake_y, self.font_small, theme)

        for particle in self.particles:
            particle.draw(self.screen, self.camera_y - shake_y)

        if self.current_state == GameState.PLAYING and self.player:
            self.player.draw(self.screen, self.camera_y - shake_y)
            self.draw_touch_controls()

        floor_txt = self.font_large.render(f"Floor: {self.stage_level} / 100", True, (255, 255, 0))
        self.screen.blit(floor_txt, (35, 20))

        if self.combo_timer > 0 and self.combo_text:
            combo_surf = self.font_large.render(self.combo_text, True, (255, 100, 0))
            self.screen.blit(combo_surf, (WIDTH - 150, 20))

        if self.combo_bar_val > 0:
            pygame.draw.rect(self.screen, (50, 50, 50), (35, 60, 150, 10), border_radius=4)
            bar_w = int((self.combo_bar_val / 100.0) * 150)
            pygame.draw.rect(self.screen, (255, 200, 0), (35, 60, bar_w, 10), border_radius=4)

        if self.current_state == GameState.STAGE_CLEAR:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 40, 20, 190))
            self.screen.blit(overlay, (0, 0))

            t1 = self.font_arabic_large.render("مبروك! لقد أنجزت البرج!", True, (255, 215, 0))
            t2 = self.font_arabic.render("اضغط هنا أو المسطرة للمستوى التالي", True, (0, 255, 150))
            self.screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
            self.screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

        if self.current_state == GameState.GAME_OVER:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((40, 0, 0, 190))
            self.screen.blit(overlay, (0, 0))

            go_txt = self.font_xlarge.render("GAME OVER", True, (255, 80, 80))
            score_txt = self.font_medium.render(f"Reached Floor: {self.stage_level}", True, (255, 255, 255))
            restart_txt = self.font_medium.render("Tap Screen / Space to Retry", True, (0, 255, 150))

            self.screen.blit(go_txt, go_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
            self.screen.blit(score_txt, score_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            self.screen.blit(restart_txt, restart_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))

        pygame.display.flip()

    def draw_menu(self):
        title_txt = self.font_large.render("ICY TOWER - EGYPT", True, (255, 255, 255))
        self.screen.blit(title_txt, title_txt.get_rect(center=(WIDTH // 2, 170)))

        if self.high_score > 0:
            hs_txt = self.font_medium.render(f"Best Score: Floor {self.high_score}", True, (255, 215, 0))
            self.screen.blit(hs_txt, hs_txt.get_rect(center=(WIDTH // 2, 230)))

        pygame.draw.rect(self.screen, (40, 180, 80), self.easy_btn, border_radius=15)
        btn1_txt = self.font_medium.render("START GAME", True, (255, 255, 255))
        self.screen.blit(btn1_txt, btn1_txt.get_rect(center=self.easy_btn.center))

    def handle_touch_event(self, pos, is_down):
        if self.current_state == GameState.PLAYING:
            if is_down:
                if self.btn_left.collidepoint(pos):
                    self.left_pressed = True
                elif self.btn_right.collidepoint(pos):
                    self.right_pressed = True
                elif self.btn_jump.collidepoint(pos):
                    self.player.jump(self.snd_jump, self.snd_super_jump, self)
            else:
                self.left_pressed = False
                self.right_pressed = False

        elif self.current_state == GameState.MENU and is_down:
            if self.easy_btn.collidepoint(pos):
                self.start_game()
        elif self.current_state == GameState.STAGE_CLEAR and is_down:
            self.current_stage_idx += 1
            self.init_game(next_stage=True)
            self.start_game()
        elif self.current_state == GameState.GAME_OVER and is_down:
            self.start_game()


# --- الحلقة الرئيسية للعبة ---
async def main():
    game = IcyTowerGame()
    running = True
    while running:
        game.clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_touch_event(event.pos, True)
            elif event.type == pygame.MOUSEBUTTONUP:
                game.handle_touch_event(event.pos, False)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT: game.left_pressed = True
                elif event.key == pygame.K_RIGHT: game.right_pressed = True
                elif event.key in (pygame.K_SPACE, pygame.K_UP):
                    if game.current_state == GameState.PLAYING:
                        game.player.jump(game.snd_jump, game.snd_super_jump, game)
                    elif game.current_state == GameState.STAGE_CLEAR:
                        game.current_stage_idx += 1
                        game.init_game(next_stage=True)
                        game.start_game()
                    elif game.current_state == GameState.GAME_OVER:
                        game.start_game()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT: game.left_pressed = False
                elif event.key == pygame.K_RIGHT: game.right_pressed = False

        if game.current_state == GameState.PLAYING:
            game.update_game()

        game.draw()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())