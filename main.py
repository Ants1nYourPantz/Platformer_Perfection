import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
import requests
import time




pygame.init()
pygame.display.set_caption("Platformer")
pygame.font.init()


WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))
menu_run = True
 
main_background = pygame.Surface((WIDTH, HEIGHT))
main_background.fill((0, 0, 0))

FONT = pygame.font.SysFont('comicsans', 30)




def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 128, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "VirtualGuy", 32, 32, True)
    ANIMATION_DELAY = 3
    
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x, elapsed_time):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    time_text = FONT.render(f"Time: {round(elapsed_time)}s", 1, "white")
    window.blit(time_text, (10, 10))
    
    pygame.display.update()


def handle_vertical_collistion(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0

    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collistion(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()



# HOME SCREEN AND GAME RUN SCREENS
def start_screen():
    global menu_run
    create_button = pygame.Rect(WIDTH // 3, HEIGHT // 3, 200, 50)
    login_button = pygame.Rect(WIDTH // 3, HEIGHT // 2, 200, 50)
    start_button = pygame.Rect(WIDTH // 3, HEIGHT // 1.5, 200, 50)

    while menu_run:
        Font = pygame.font.SysFont('comicsans', 40)
        window.blit(main_background, dest=(0, 0))
        game_title = Font.render("StarSide Jumpers", True, (180, 0, 255))
        window.blit(game_title, dest=(WIDTH / 3.2, HEIGHT / 6))

        # Create button
        Font = pygame.font.SysFont('comicsans', 20)
        pygame.draw.rect(window, (180, 0, 255), create_button)
        create_text = Font.render("Create Account", True, (0, 0, 0))
        window.blit(create_text, (create_button.x + 30, create_button.y + 10))

        # Login button
        Font = pygame.font.SysFont('comicsans', 20)
        pygame.draw.rect(window, (180, 0, 255), login_button)
        login_text = Font.render("Log In", True, (0, 0, 0))
        window.blit(login_text, (login_button.x + 70, login_button.y + 10))

        # Start button
        Font = pygame.font.SysFont('comicsans', 20)
        pygame.draw.rect(window, (180, 0, 255), start_button)
        start_text = Font.render("Start Game", True, (0, 0, 0))
        window.blit(start_text, (start_button.x + 50, start_button.y + 10))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            # Create button clicked
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if create_button.collidepoint(event.pos):
                    create_user()

            # Login button clicked
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if login_button.collidepoint(event.pos):
                    print("Log in button clicked")

            # Start button clicked
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.collidepoint(event.pos):
                    menu_run = False
                    



def create_user():
    menu_run = True
    input_rects = [pygame.Rect(WIDTH // 3, HEIGHT // 3, 400, 50), pygame.Rect(WIDTH // 3, HEIGHT // 2, 400, 50)]

    input_active = [False, False]
    input_texts = ['', '']
    input_font = pygame.font.SysFont('comicsans', 40)
    # create_account = ()

    submit_button = pygame.Rect(WIDTH // 2 - 50, HEIGHT - 100, 150, 50)
    submit_font = pygame.font.SysFont('comicsans', 30)

 
    while menu_run:
        window.blit(main_background, dest=(0, 0))

        # Input field label text size
        label_font = pygame.font.SysFont(None, 30)

        #Input Boxes for Username and Password
        for i, rect in enumerate(input_rects):
            if input_active[i]:
                color = (255, 255, 0)
            else:
                color = (255, 255, 255)
            pygame.draw.rect(window, color, rect, 2)
            text_surface = input_font.render(input_texts[i], True, (255, 255, 255))
            window.blit(text_surface, (rect.x + 5, rect.y + 5))

            if i == 0:
                label_surface = label_font.render("Username:", True, (255, 255, 255))
            elif i == 1:
                label_surface = label_font.render("Password:", True, (255, 255, 255))
            window.blit(label_surface, (rect.x - 100, rect.y))

        # Submit
        pygame.draw.rect(window, (180, 0, 255), submit_button)
        submit_text = submit_font.render("Create", True, (0, 0, 0))
        window.blit(submit_text, (submit_button.x + 20, submit_button.y + 10))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            # Input fields clicked
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(input_rects):
                    if rect.collidepoint(event.pos):
                        input_active[i] = True
                    else:
                        input_active[i] = False

            # Submit button clicked
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if submit_button.collidepoint(event.pos):
                    username = input_texts[0]
                    password = input_texts[1]
                    print(username, password)

                    # Exit create user loop
                    menu_run = False

            # Key inputs
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active[0] = False
                    input_active[1] = False
                if input_active[0]:
                    if event.key == pygame.K_BACKSPACE:
                        input_texts[0] = input_texts[0][:-1]
                    else:
                        input_texts[0] += event.unicode
                if input_active[1]:
                    if event.key == pygame.K_BACKSPACE:
                        input_texts[1] = input_texts[1][:-1]
                    else:
                        input_texts[1] += event.unicode

    


def username_screen():
    pass


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background('bg.jpeg')

    start_time = time.time()
    elapsed_time = 0

    block_size = 96

    player = Player(100, 100, 50, 50)
    fire = Fire(200, 352, 16, 32)
    fire.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
              for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size),
            # Starting Platform Right Wall
               Block(94, HEIGHT - block_size * 6, block_size),  
               Block(188, HEIGHT - block_size * 6, block_size),  
               Block(282, HEIGHT - block_size * 6, block_size),  
               Block(376, HEIGHT - block_size * 6, block_size),  
               Block(470, HEIGHT - block_size * 7, block_size),  
               Block(470, HEIGHT - block_size * 8, block_size),  
               Block(470, HEIGHT - block_size * 9, block_size),    
               Block(470, HEIGHT - block_size * 10, block_size),    
               Block(470, HEIGHT - block_size * 11, block_size),    
               Block(282, HEIGHT - block_size * 8, block_size),  
               Block(188, HEIGHT - block_size * 8, block_size),  
               Block(94, HEIGHT - block_size * 8, block_size),  
               Block(0, HEIGHT - block_size * 8, block_size),  
               Block(0, HEIGHT - block_size * 9, block_size),  
               Block(0, HEIGHT - block_size * 10, block_size),  
               Block(0, HEIGHT - block_size * 11, block_size),  
            # First Run
               Block(-94, HEIGHT - block_size * 6, block_size),  
               Block(-188, HEIGHT - block_size * 6, block_size),  
               Block(-282, HEIGHT - block_size * 6, block_size),  
               Block(-376, HEIGHT - block_size * 6, block_size),  
               Block(-376, HEIGHT - block_size * 7, block_size),  
               Block(-470, HEIGHT - block_size * 6, block_size),  
               Block(-564, HEIGHT - block_size * 6, block_size),  
               Block(-658, HEIGHT - block_size * 6, block_size),  
               Block(-752, HEIGHT - block_size * 6, block_size),  
               Block(-846, HEIGHT - block_size * 6, block_size),
            # End Wall Left 
               Block(-1034, HEIGHT - block_size * 2, block_size),  
               Block(-1034, HEIGHT - block_size * 3, block_size),  
               Block(-1034, HEIGHT - block_size * 4, block_size),  
               Block(-1034, HEIGHT - block_size * 5, block_size),  
               Block(-1034, HEIGHT - block_size * 6, block_size),  
               Block(-1034, HEIGHT - block_size * 7, block_size),  
               Block(-1034, HEIGHT - block_size * 8, block_size),  
               Block(-1034, HEIGHT - block_size * 9, block_size),  
               Block(-1034, HEIGHT - block_size * 10, block_size),
            # Right Run
               Block(-940, HEIGHT - block_size * 4, block_size),  
               Block(-846, HEIGHT - block_size * 4, block_size),
               Block(-752, HEIGHT - block_size * 4, block_size),
            # 3 Stack  
               Block(-470, HEIGHT - block_size * 2, block_size),  
               Block(-376, HEIGHT - block_size * 2, block_size),  
               Block(-423, HEIGHT - block_size * 3, block_size),  
               Block(-517, HEIGHT - block_size * 5, block_size),  
               Block(-517, HEIGHT - block_size * 6, block_size),  
            # Starting Wall  
               Block(0, HEIGHT - block_size * 4, block_size),  
               Block(0, HEIGHT - block_size * 5, block_size),  
               Block(0, HEIGHT - block_size * 6, block_size),     
            # Near Fire L
               Block(380, 416, block_size),
               Block(194, 416, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size), 
               fire, 
            # Wall 1
               Block(570, HEIGHT - block_size * 2, block_size),
               Block(664, HEIGHT - block_size * 2, block_size),
               Block(664, HEIGHT - block_size * 3, block_size),
               Block(664, HEIGHT - block_size * 4, block_size),
               Block(664, HEIGHT - block_size * 5, block_size),
            # Pyrimad Level 1
               Block(1122, HEIGHT - block_size * 2, block_size),
               Block(1592, HEIGHT - block_size * 2, block_size),
               Block(1592, HEIGHT - block_size * 3, block_size),
            # P Stack 
               Block(1686, HEIGHT - block_size * 2, block_size),
               Block(1686, HEIGHT - block_size * 3, block_size),
               Block(1686, HEIGHT - block_size * 4, block_size),
               Block(1686, HEIGHT - block_size * 5, block_size),
               Block(1686, HEIGHT - block_size * 6, block_size),
               Block(1686, HEIGHT - block_size * 7, block_size),
               Block(1874, HEIGHT - block_size * 2, block_size),
               Block(1874, HEIGHT - block_size * 3, block_size),
               Block(1874, HEIGHT - block_size * 4, block_size),
               Block(1874, HEIGHT - block_size * 5, block_size),
               Block(1874, HEIGHT - block_size * 6, block_size),
               Block(1874, HEIGHT - block_size * 7, block_size),
               Block(1874, HEIGHT - block_size * 8, block_size),
               Block(1874, HEIGHT - block_size * 9, block_size),
               Block(1874, HEIGHT - block_size * 10, block_size),
               Block(1874, HEIGHT - block_size * 11, block_size),
               Block(1874, HEIGHT - block_size * 12, block_size),
            # Pyrimad Level 2
               Block(1169, HEIGHT - block_size * 3, block_size),
               Block(1357, HEIGHT - block_size * 3, block_size),
            # Pyramid Level 3
               Block(1357, HEIGHT - block_size * 4, block_size),
            # Pyramid Level 4
               Block(981, HEIGHT - block_size * 5, block_size),
               Block(981, HEIGHT - block_size * 6, block_size),
               Block(981, HEIGHT - block_size * 7, block_size),
               Block(981, HEIGHT - block_size * 8, block_size),
               Block(981, HEIGHT - block_size * 9, block_size),
               Block(1075, HEIGHT - block_size * 5, block_size),
               Block(1169, HEIGHT - block_size * 5, block_size),
               Block(1263, HEIGHT - block_size * 5, block_size),
               Block(1357, HEIGHT - block_size * 5, block_size),
               Block(1451, HEIGHT - block_size * 5, block_size),
            # Horizontal 2
               Block(1169, HEIGHT - block_size * 7, block_size),
               Block(1263, HEIGHT - block_size * 7, block_size),
               Block(1357, HEIGHT - block_size * 7, block_size),
               Block(1451, HEIGHT - block_size * 7, block_size),
            #    Block(1263, HEIGHT - block_size * 7, block_size),
               ]
 
    
    offset_x = 0
    scroll_area_width = 500

    start_screen()
    
    while True:
        clock.tick(FPS)
        current_time = time.time()
        elapsed_time = current_time - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
                
        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x, elapsed_time)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel


if __name__ == "__main__":
    main(window)