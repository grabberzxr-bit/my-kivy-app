import pygame
import random
import sys
import os
import math

# Initialize Pygame
pygame.init()

# Screen Dimensions - 16:9 Widescreen Ratio
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dan the Block Adventure")

# Colors
WHITE = (255, 255, 255)
BLACK = (15, 15, 20)
BLUE = (50, 100, 255)
RED = (220, 50, 50)
GREEN = (50, 180, 50)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
GRAY = (60, 60, 65)
DARK_GRAY = (30, 30, 35)
LIGHT_GRAY = (100, 100, 105)
SKY_BLUE = (135, 206, 235)

clock = pygame.time.Clock()

# --- LOAD TEXTURES WITH FALLBACK ---
def load_image(filename, width, height, fallback_color):
    if os.path.exists(filename):
        try:
            img = pygame.image.load(filename).convert_alpha()
            return pygame.transform.scale(img, (width, height))
        except Exception:
            pass
    surf = pygame.Surface((width, height))
    surf.fill(fallback_color)
    pygame.draw.rect(surf, (0, 0, 0), (0, 0, width, height), 2)
    return surf

# Perfectly synced with your custom 48, 64, and 24 grid choices
player_img = load_image("player.png", 48, 64, BLUE)
enemy_img = load_image("enemy.png", 40, 56, RED)
brick_img = load_image("brick.png", 64, 64, GRAY)
medkit_img = load_image("medkit.png", 24, 24, GREEN)
ammo_img = load_image("ammo.png", 24, 24, ORANGE)

# --- GAME OBJECT CLASSES ---

class Player:
    def __init__(self):
        # Hitbox matches the 48x64 image size exactly
        self.rect = pygame.Rect(100, 200, 48, 64)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.vel_y = 0.0
        self.speed = 350.0  
        self.gravity = 1200.0  
        self.jump_force = -550.0
        self.is_jumping = False
        self.health = 100.0
        self.max_health = 100.0
        self.weapon = "MELEE"
        self.ammo = 0
        self.direction = 1
        self.is_attacking = False
        self.attack_cooldown = 0.0

    def update(self, move_left, move_right, jump, platforms, dt):
        if move_left:
            self.x -= self.speed * dt
            self.direction = -1
        if move_right:
            self.x += self.speed * dt
            self.direction = 1

        self.rect.x = int(self.x)

        if jump and not self.is_jumping:
            self.vel_y = self.jump_force
            self.is_jumping = True

        self.vel_y += self.gravity * dt
        self.y += self.vel_y * dt
        self.rect.y = int(self.y)

        self.is_jumping = True
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel_y > 0 and (self.rect.bottom - (self.vel_y * dt)) <= plat.rect.top + 10:
                    self.rect.bottom = plat.rect.top
                    self.y = float(self.rect.y)
                    self.vel_y = 0.0
                    self.is_jumping = False

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        else:
            self.is_attacking = False

        if self.rect.y > SCREEN_HEIGHT:
            self.health = 0

class Bullet:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 18, 6)
        self.x = float(self.rect.x)
        self.speed = 700.0 * direction  

    def update(self, dt):
        self.x += self.speed * dt
        self.rect.x = int(self.x)

class Enemy:
    def __init__(self, x, y, difficulty_multiplier):
        # Hitbox matches the 40x56 image size exactly
        self.rect = pygame.Rect(x, y, 40, 56)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.max_health = int(30 * difficulty_multiplier)
        self.health = self.max_health
        self.speed = random.choice([100.0, 140.0]) * difficulty_multiplier
        self.direction = random.choice([-1, 1])
        self.vel_y = 0.0
        self.gravity = 1200.0

    def update(self, platforms, dt):
        self.x += self.speed * self.direction * dt
        self.rect.x = int(self.x)
        
        self.vel_y += self.gravity * dt
        self.y += self.vel_y * dt
        self.rect.y = int(self.y)
        
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel_y > 0 and (self.rect.bottom - (self.vel_y * dt)) <= plat.rect.top + 12:
                    self.rect.bottom = plat.rect.top
                    self.y = float(self.rect.y)
                    self.vel_y = 0.0
                    
                    # Safe platform patrol logic: prevents walking off edge drops
                    if self.direction == 1 and self.rect.right >= plat.rect.right:
                        self.rect.right = plat.rect.right
                        self.x = float(self.rect.x)
                        self.direction = -1
                    elif self.direction == -1 and self.rect.left <= plat.rect.left:
                        self.rect.left = plat.rect.left
                        self.x = float(self.rect.x)
                        self.direction = 1

        if self.rect.y > SCREEN_HEIGHT:
            self.health = 0

class Platform:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.fan_rects = []
        num_fans = max(1, width // 128)
        for i in range(num_fans):
            fan_x = x + (i * (width // num_fans)) + (width // (num_fans * 2)) - 20
            self.fan_rects.append(pygame.Rect(fan_x, y + height, 40, 15))

class Pickup:
    def __init__(self, x, y, type):
        # Hitbox matches the 24x24 item size exactly
        self.rect = pygame.Rect(x, y, 24, 24)
        self.type = type

# --- GENERATION ENGINE ---

class WorldGenerator:
    def __init__(self):
        self.last_generated_x = 0
        
    def generate_next_segment(self, platforms, enemies, pickups, current_multiplier):
        plat_width = random.randint(250, 500)
        plat_y = random.randint(340, 440)
        plat_x = self.last_generated_x + random.randint(80, 160)

        plat_width = (plat_width // 64) * 64
        if plat_width < 128: plat_width = 128

        new_plat = Platform(plat_x, plat_y, plat_width, 45)
        platforms.append(new_plat)

        if random.random() < 0.6:
            enemy_x = plat_x + (plat_width // 2)
            enemies.append(Enemy(enemy_x, plat_y - 60, current_multiplier))

        if random.random() < 0.3:
            pickup_type = random.choice(["MEDKIT", "GUN_AMMO"])
            pickup_x = plat_x + random.randint(30, plat_width - 50)
            pickups.append(Pickup(pickup_x, plat_y - 35, pickup_type))

        self.last_generated_x = plat_x + plat_width

def reset_game(checkpoint_override=None):
    global player, platforms, enemies, pickups, bullets, world_gen, camera_offset_x, score, active_fingers, checkpoint_milestone, difficulty_level, checkpoint_x
    
    player = Player()
    
    if checkpoint_override:
        player.x = float(checkpoint_override)
        player.rect.x = int(player.x)
        platforms = [Platform(checkpoint_override - 100, 440, 512, 100)]
        world_gen = WorldGenerator()
        world_gen.last_generated_x = checkpoint_override + 412
    else:
        platforms = [Platform(0, 440, 768, 100)]
        world_gen = WorldGenerator()
        world_gen.last_generated_x = 768
        checkpoint_x = 0
        checkpoint_milestone = 2000
        difficulty_level = 1
        score = 0
        
    enemies = []
    pickups = []
    bullets = []
    camera_offset_x = player.x - 250
    active_fingers = {}

checkpoint_x = 0
checkpoint_milestone = 2000
difficulty_level = 1
reset_game()

# --- MOBILE INTERFACE LAYOUT (BIGGER CONTROLS) ---
btn_y = 465
btn_size = 95  

left_btn = pygame.Rect(30, btn_y, btn_size, btn_size)
right_btn = pygame.Rect(145, btn_y, btn_size, btn_size)
jump_btn = pygame.Rect(760, btn_y, btn_size, btn_size)
attack_btn = pygame.Rect(885, btn_y, btn_size, btn_size)
pause_btn = pygame.Rect(SCREEN_WIDTH - 120, 20, 100, 45)

# Expanded crash-safe collision touch detector bounding zone
pause_touch_zone = pygame.Rect(SCREEN_WIDTH - 140, 10, 130, 65)

# Menu Navigation Rectangles
start_menu_btn = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 - 20, 240, 60)
restart_game_btn = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 30, 240, 60)
resume_btn = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 - 40, 240, 60)
quit_btn = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 40, 240, 60)

game_state = "MENU"
running = True
fan_anim_timer = 0.0

# --- MAIN LOOP ---
while running:
    dt = min(clock.tick(60) / 1000.0, 0.1)
    
    font = pygame.font.SysFont(None, 28)
    title_font = pygame.font.SysFont(None, 64)
    ui_font = pygame.font.SysFont(None, 36)

    # 1. MENU STATE
    if game_state == "MENU":
        screen.fill(BLACK)
        title_lbl = title_font.render("DAN THE BLOCK ADVENTURE", True, YELLOW)
        screen.blit(title_lbl, (SCREEN_WIDTH // 2 - title_lbl.get_width() // 2, 120))
        
        pygame.draw.rect(screen, BLUE, start_menu_btn, 0, 8)
        start_lbl = ui_font.render("START GAME", True, WHITE)
        screen.blit(start_lbl, (start_menu_btn.x + (start_menu_btn.width - start_lbl.get_width())//2, start_menu_btn.y + 15))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_menu_btn.collidepoint(pygame.mouse.get_pos()):
                    reset_game()
                    game_state = "PLAYING"

    # 2. ACTIVE GAMEPLAY STATE
    elif game_state == "PLAYING":
        fan_anim_timer += dt * 25  
        screen.fill(SKY_BLUE)
        
        move_left = False
        move_right = False
        jump = False
        shoot_or_punch = False

        # --- DUAL TOUCH & MOUSE INPUT SYSTEM ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            
            elif event.type == pygame.FINGERDOWN:
                fx, fy = int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT)
                if pause_touch_zone.collidepoint(fx, fy):
                    game_state = "PAUSED"
                else:
                    active_fingers[event.finger_id] = (fx, fy)
            elif event.type == pygame.FINGERMOTION:
                active_fingers[event.finger_id] = (int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT))
            elif event.type == pygame.FINGERUP:
                active_fingers.pop(event.finger_id, None)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if pause_touch_zone.collidepoint(pygame.mouse.get_pos()):
                    game_state = "PAUSED"

        for fid, pos in active_fingers.items():
            if left_btn.collidepoint(pos): move_left = True
            if right_btn.collidepoint(pos): move_right = True
            if jump_btn.collidepoint(pos): jump = True
            if attack_btn.collidepoint(pos): shoot_or_punch = True

        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if left_btn.collidepoint(m_pos): move_left = True
            if right_btn.collidepoint(m_pos): move_right = True
            if jump_btn.collidepoint(m_pos): jump = True
            if attack_btn.collidepoint(m_pos): shoot_or_punch = True

        # Checkpoint Systems Tracker
        if player.rect.x > checkpoint_milestone:
            checkpoint_x = checkpoint_milestone
            checkpoint_milestone += 2000
            difficulty_level += 1  

        if player.rect.x + SCREEN_WIDTH > world_gen.last_generated_x:
            difficulty_multiplier = 1.0 + (difficulty_level - 1) * 0.25
            world_gen.generate_next_segment(platforms, enemies, pickups, difficulty_multiplier)

        player.update(move_left, move_right, jump, platforms, dt)
        
        target_camera_x = player.rect.x - 250
        camera_offset_x += (target_camera_x - camera_offset_x) * 0.1
        int_cam_x = int(camera_offset_x)

        if shoot_or_punch and not player.is_attacking and player.attack_cooldown <= 0:
            player.is_attacking = True
            if player.weapon == "PISTOL" and player.ammo > 0:
                player.ammo -= 1
                b_x = player.rect.right if player.direction == 1 else player.rect.left
                bullets.append(Bullet(b_x, player.rect.centery - 3, player.direction))
                player.attack_cooldown = 0.25 
                if player.ammo <= 0: player.weapon = "MELEE"
            else:
                player.attack_cooldown = 0.35

        for bullet in bullets[:]:
            bullet.update(dt)
            if abs(bullet.rect.x - player.rect.x) > SCREEN_WIDTH:
                bullets.remove(bullet)

        for enemy in enemies[:]:
            enemy.update(platforms, dt)
            
            if player.is_attacking and player.weapon == "MELEE":
                # Scaled melee range boundary check
                melee_range = pygame.Rect(player.rect.x - 40, player.rect.y, player.rect.width + 80, player.rect.height)
                if melee_range.colliderect(enemy.rect):
                    enemy.health -= 10
                    player.is_attacking = False
            
            if player.rect.colliderect(enemy.rect):
                player.health -= 35 * dt 
            
            for bullet in bullets[:]:
                if bullet.rect.colliderect(enemy.rect):
                    enemy.health -= 15
                    if bullet in bullets: bullets.remove(bullet)

            if enemy.health <= 0:
                enemies.remove(enemy)
                score += 100

        for pickup in pickups[:]:
            if player.rect.colliderect(pickup.rect):
                if pickup.type == "MEDKIT":
                    player.health = min(player.max_health, player.health + 25)
                elif pickup.type == "GUN_AMMO":
                    player.weapon = "PISTOL"
                    player.ammo += 10
                pickups.remove(pickup)

        if player.health <= 0:
            game_state = "GAMEOVER"

        # --- RENDERING ENGINE WORLD ELEMENTS ---
        for plat in platforms:
            tiles_needed = plat.rect.width // 64 + 1
            for i in range(tiles_needed):
                screen.blit(brick_img, (plat.rect.x + (i * 64) - int_cam_x, plat.rect.y))
            
            for fan in plat.fan_rects:
                pygame.draw.rect(screen, DARK_GRAY, (fan.x - int_cam_x, fan.y, fan.width, fan.height))
                blade_oscillation = int(math.sin(fan_anim_timer) * 16) + 20
                pygame.draw.line(screen, ORANGE, (fan.centerx - int_cam_x - blade_oscillation // 2, fan.centery), 
                                                 (fan.centerx - int_cam_x + blade_oscillation // 2, fan.centery), 3)

        for pickup in pickups:
            img = medkit_img if pickup.type == "MEDKIT" else ammo_img
            screen.blit(img, (pickup.rect.x - int_cam_x, pickup.rect.y))

        for enemy in enemies:
            e_render = pygame.transform.flip(enemy_img, True, False) if enemy.direction == -1 else enemy_img
            screen.blit(e_render, (enemy.rect.x - int_cam_x, enemy.rect.y))
            pygame.draw.rect(screen, RED, (enemy.rect.x - int_cam_x, enemy.rect.y - 12, int((enemy.health / enemy.max_health) * 40), 5))

        for bullet in bullets:
            pygame.draw.rect(screen, YELLOW, (bullet.rect.x - int_cam_x, bullet.rect.y, bullet.rect.width, bullet.rect.height))

        p_render = pygame.transform.flip(player_img, True, False) if player.direction == -1 else player_img
        if player.is_attacking and player.weapon == "MELEE":
            p_render.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(p_render, (player.rect.x - int_cam_x, player.rect.y))

        # --- HUD DATA RENDER ---
        pygame.draw.rect(screen, RED, (20, 20, 200, 18))
        if player.health > 0:
            pygame.draw.rect(screen, GREEN, (20, 20, int(player.health * 2), 18))

        weapon_label = font.render(f"WEAPON: {player.weapon} | AMMO: {player.ammo if player.weapon == 'PISTOL' else 'INF'}", True, BLACK)
        score_label = font.render(f"SCORE: {score} | STAGE: {difficulty_level}", True, BLACK)
        screen.blit(weapon_label, (20, 48))
        screen.blit(score_label, (240, 20))

        # Pause Control
        pygame.draw.rect(screen, GRAY, pause_btn, 0, 4)
        screen.blit(font.render("PAUSE", True, WHITE), (pause_btn.x + 18, pause_btn.y + 12))

        # Action Control Overlays (Enhanced Large Format Layout)
        pygame.draw.rect(screen, DARK_GRAY, left_btn, 0, 12)
        pygame.draw.rect(screen, DARK_GRAY, right_btn, 0, 12)
        pygame.draw.rect(screen, DARK_GRAY, jump_btn, 0, 12)
        pygame.draw.rect(screen, ORANGE if player.weapon == "PISTOL" else BLUE, attack_btn, 0, 12)

        screen.blit(ui_font.render("<", True, WHITE), (left_btn.x + 38, left_btn.y + 32))
        screen.blit(ui_font.render(">", True, WHITE), (right_btn.x + 38, right_btn.y + 32))
        screen.blit(ui_font.render("JMP", True, WHITE), (jump_btn.x + 24, jump_btn.y + 32))
        screen.blit(ui_font.render("ATK", True, WHITE), (attack_btn.x + 24, attack_btn.y + 32))

    # 3. INTERACTIVE PAUSE MENU STATE
    elif game_state == "PAUSED":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(10)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, DARK_GRAY, (SCREEN_WIDTH//2 - 160, SCREEN_HEIGHT//2 - 120, 320, 260), 0, 12)
        
        paused_lbl = title_font.render("GAME PAUSED", True, YELLOW)
        screen.blit(paused_lbl, (SCREEN_WIDTH // 2 - paused_lbl.get_width() // 2, SCREEN_HEIGHT // 2 - 95))

        pygame.draw.rect(screen, GREEN, resume_btn, 0, 8)
        screen.blit(ui_font.render("RESUME", True, WHITE), (resume_btn.x + 68, resume_btn.y + 15))

        pygame.draw.rect(screen, RED, quit_btn, 0, 8)
        screen.blit(ui_font.render("QUIT GAME", True, WHITE), (quit_btn.x + 55, quit_btn.y + 15))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                m_pos = pygame.mouse.get_pos()
                if resume_btn.collidepoint(m_pos):
                    active_fingers.clear() 
                    game_state = "PLAYING"
                elif quit_btn.collidepoint(m_pos):
                    game_state = "MENU"
            
            elif event.type == pygame.FINGERDOWN:
                fx, fy = int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT)
                if resume_btn.collidepoint(fx, fy):
                    active_fingers.clear()
                    game_state = "PLAYING"
                elif quit_btn.collidepoint(fx, fy):
                    game_state = "MENU"

    # 4. GAME OVER STATE
    elif game_state == "GAMEOVER":
        screen.fill(BLACK)
        go_lbl = title_font.render("GAME OVER", True, RED)
        screen.blit(go_lbl, (SCREEN_WIDTH // 2 - go_lbl.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        
        info_lbl = ui_font.render(f"Respawning at Checkpoint Stage: {difficulty_level}", True, WHITE)
        screen.blit(info_lbl, (SCREEN_WIDTH // 2 - info_lbl.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        pygame.draw.rect(screen, GREEN, restart_game_btn, 0, 8)
        restart_lbl = ui_font.render("RESPAWN", True, WHITE)
        screen.blit(restart_lbl, (restart_game_btn.x + (restart_game_btn.width - restart_lbl.get_width())//2, restart_game_btn.y + 15))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_game_btn.collidepoint(pygame.mouse.get_pos()):
                    reset_game(checkpoint_override=checkpoint_x)
                    game_state = "PLAYING"

    pygame.display.flip()

pygame.quit()
s
