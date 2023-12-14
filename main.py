import json
import pygame
import sys

# Инициализация Pygame
pygame.mixer.pre_init()
pygame.init()

# Настройки окна
TITLE = "Platformer"
WIDTH = 960
HEIGHT = 640
FPS = 60
GRID_SIZE = 64


# Управление
LEFT = pygame.K_LEFT
RIGHT = pygame.K_RIGHT
JUMP = pygame.K_SPACE

# Уровни
levels = ["levels/world-1.json",
          "levels/world-2.json",
          "levels/world-3.json"]

# Цвета
TRANSPARENT = (0, 0, 0, 0)
DARK_BLUE = (16, 86, 103)
WHITE = (255, 255, 255)

# Шрифты
FONT_SM = pygame.font.Font("assets/fonts/minya_nouvelle_bd.ttf", 32)
FONT_MD = pygame.font.Font("assets/fonts/minya_nouvelle_bd.ttf", 64)
FONT_LG = pygame.font.Font("assets/fonts/thats_super.ttf", 72)

# Вспомогательные функции
def load_image(file_path, width=GRID_SIZE, height=GRID_SIZE):
    # Загрузка изображения и масштабирование
    img = pygame.image.load(file_path)
    img = pygame.transform.scale(img, (width, height))
    return img


# Изображения
hero_walk1 = load_image("assets/character/adventurer_walk1.png")
hero_walk2 = load_image("assets/character/adventurer_walk2.png")
hero_jump = load_image("assets/character/adventurer_jump.png")
hero_idle = load_image("assets/character/adventurer_idle.png")
hero_images = {"run": [hero_walk1, hero_walk2],
               "jump": hero_jump,
               "idle": hero_idle}

block_images = {"TL": load_image("assets/tiles/top_left.png"),
                "TM": load_image("assets/tiles/top_middle.png"),
                "TR": load_image("assets/tiles/top_right.png"),
                "ER": load_image("assets/tiles/end_right.png"),
                "EL": load_image("assets/tiles/end_left.png"),
                "TP": load_image("assets/tiles/top.png"),
                "CN": load_image("assets/tiles/center.png"),
                "LF": load_image("assets/tiles/lone_float.png"),
                "SP": load_image("assets/tiles/special.png")}

coin_img = load_image("assets/items/coin.png")
heart_img = load_image("assets/items/bandaid.png")
oneup_img = load_image("assets/items/first_aid.png")
flag_img = load_image("assets/items/flag.png")
flagpole_img = load_image("assets/items/flagpole.png")

monster_img1 = load_image("assets/enemies/monster-1.png")
monster_img2 = load_image("assets/enemies/monster-2.png")
monster_images = [monster_img1, monster_img2]

bear_img = load_image("assets/enemies/bear-1.png")
bear_images = [bear_img]


class Entity(pygame.sprite.Sprite):
    
    # Базовый класс для всех объектов в игре.

    def __init__(self, x, y, image):
        # Инициализация базового класса Sprite
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vy = 0
        self.vx = 0

    def apply_gravity(self, level):
        # Применение гравитации к объекту.
        self.vy += level.gravity
        self.vy = min(self.vy, level.terminal_velocity)

class Block(Entity):
    # Класс блока в игре, наследуется от Entity.

    def __init__(self, x, y, image):
        # Инициализация блока
        super().__init__(x, y, image)


class Character(Entity):
    # Класс персонажа игры, наследуется от Entity.

    def __init__(self, images):
        # Инициализация персонажа
        super().__init__(0, 0, images['idle'])

        self.image_idle_right = images['idle']
        self.image_idle_left = pygame.transform.flip(self.image_idle_right, 1, 0)
        self.images_run_right = images['run']
        self.images_run_left = [pygame.transform.flip(img, 1, 0) for img in self.images_run_right]
        self.image_jump_right = images['jump']
        self.image_jump_left = pygame.transform.flip(self.image_jump_right, 1, 0)

        self.running_images = self.images_run_right
        self.image_index = 0
        self.steps = 0

        self.speed = 5
        self.jump_power = 20

        self.vx = 0
        self.vy = 0
        self.facing_right = True
        self.on_ground = True

        self.score = 0
        self.lives = 3
        self.hearts = 3
        self.max_hearts = 3
        self.invincibility = 0

    def move_left(self):
        # Движение персонажа влево.
        self.vx = -self.speed
        self.facing_right = False

    def move_right(self):
        # Движение персонажа вправо.
        self.vx = self.speed
        self.facing_right = True

    def stop(self):
        # Остановка движения персонажа.
        self.vx = 0

    def jump(self, blocks):
        # Персонаж выполняет прыжок, проверяя столкновение с блоками.
        self.rect.y += 1

        hit_list = pygame.sprite.spritecollide(self, blocks, False)

        if len(hit_list) > 0:
            # Если есть столкновение с блоком, выполнить прыжок и воспроизвести звук
            self.vy = -1 * self.jump_power

        self.rect.y -= 1

    def check_world_boundaries(self, level):
        # Проверка границ мира для персонажа.
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > level.width:
            self.rect.right = level.width

    def move_and_process_blocks(self, blocks):
        # Движение и обработка столкновений с блоками.
        self.rect.x += self.vx
        hit_list = pygame.sprite.spritecollide(self, blocks, False)

        for block in hit_list:
            if self.vx > 0:
                self.rect.right = block.rect.left
                self.vx = 0
            elif self.vx < 0:
                self.rect.left = block.rect.right
                self.vx = 0

        self.on_ground = False
        self.rect.y += self.vy + 1
        hit_list = pygame.sprite.spritecollide(self, blocks, False)

        for block in hit_list:
            if self.vy > 0:
                self.rect.bottom = block.rect.top
                self.vy = 0
                self.on_ground = True
            elif self.vy < 0:
                self.rect.top = block.rect.bottom
                self.vy = 0

    def process_coins(self, coins):
        # Обработка сбора монет.
        hit_list = pygame.sprite.spritecollide(self, coins, True)

        for coin in hit_list:
            self.score += coin.value

    def process_enemies(self, enemies):
        # Обработка столкновения с врагами.
        hit_list = pygame.sprite.spritecollide(self, enemies, False)

        if len(hit_list) > 0 and self.invincibility == 0:
            self.hearts -= 1
            self.invincibility = int(0.75 * FPS)

    def process_powerups(self, powerups):
        # Обработка подбора усилений.
        hit_list = pygame.sprite.spritecollide(self, powerups, True)

        for p in hit_list:
            p.apply(self)

    def check_flag(self, level):
        # Проверка столкновения с флагом.
        hit_list = pygame.sprite.spritecollide(self, level.flag, False)

        if len(hit_list) > 0:
            level.completed = True

    def set_image(self):
        # Установка изображения в зависимости от состояния персонажа.
        if self.on_ground:
            if self.vx != 0:
                if self.facing_right:
                    self.running_images = self.images_run_right
                else:
                    self.running_images = self.images_run_left

                self.steps = (self.steps + 1) % self.speed  

                if self.steps == 0:
                    self.image_index = (self.image_index + 1) % len(self.running_images)
                    self.image = self.running_images[self.image_index]
            else:
                if self.facing_right:
                    self.image = self.image_idle_right
                else:
                    self.image = self.image_idle_left
        else:
            if self.facing_right:
                self.image = self.image_jump_right
            else:
                self.image = self.image_jump_left

    def die(self):
        # Обработка смерти персонажа.
        self.lives -= 1


    def respawn(self, level):
        # Возрождение персонажа на стартовой позиции.
        self.rect.x = level.start_x
        self.rect.y = level.start_y
        self.hearts = self.max_hearts
        self.invincibility = 0
        self.facing_right = True

    def update(self, level):
        # Обновление состояния персонажа на каждом кадре.
        self.process_enemies(level.enemies)
        self.apply_gravity(level)
        self.move_and_process_blocks(level.blocks)
        self.check_world_boundaries(level)
        self.set_image()

        if self.hearts > 0:
            self.process_coins(level.coins)
            self.process_powerups(level.powerups)
            self.check_flag(level)

            if self.invincibility > 0:
                self.invincibility -= 1
        else:
            self.die()


class Coin(Entity):
    # Класс для представления монеты, наследуется от Entity.

    def __init__(self, x, y, image):
        # Инициализация монеты
        super().__init__(x, y, image)

        self.value = 1


class Enemy(Entity):
    # Класс для представления врага, наследуется от Entity.

    def __init__(self, x, y, images):
        # Инициализация врага
        super().__init__(x, y, images[0])

        self.images_left = images
        self.images_right = [pygame.transform.flip(img, 1, 0) for img in images]
        self.current_images = self.images_left
        self.image_index = 0
        self.steps = 0

    def reverse(self):
        # Изменение направления движения врага
        self.vx *= -1

        if self.vx < 0:
            self.current_images = self.images_left
        else:
            self.current_images = self.images_right

        self.image = self.current_images[self.image_index]

    def check_world_boundaries(self, level):
        # Проверка границ мира для врага
        if self.rect.left < 0:
            self.rect.left = 0
            self.reverse()
        elif self.rect.right > level.width:
            self.rect.right = level.width
            self.reverse()

    def move_and_process_blocks(self, blocks):
        # Движение и обработка столкновений с блоками
        self.rect.x += self.vx
        hit_list = pygame.sprite.spritecollide(self, blocks, False)

        for block in hit_list:
            if self.vx > 0:
                self.rect.right = block.rect.left
                self.reverse()
            elif self.vx < 0:
                self.rect.left = block.rect.right
                self.reverse()

        self.rect.y += self.vy  # the +1 is hacky. not sure why it helps.
        hit_list = pygame.sprite.spritecollide(self, blocks, False)

        for block in hit_list:
            if self.vy > 0:
                self.rect.bottom = block.rect.top
                self.vy = 0
            elif self.vy < 0:
                self.rect.top = block.rect.bottom
                self.vy = 0

    def set_images(self):
        # Установка изображения врага в зависимости от состояния
        if self.steps == 0:
            self.image = self.current_images[self.image_index]
            self.image_index = (self.image_index + 1) % len(self.current_images)

        self.steps = (self.steps + 1) % 20  # Nothing significant about 20. It just seems to work okay.

    def is_near(self, hero):
        # Проверка, находится ли герой в пределах видимости врага
        return abs(self.rect.x - hero.rect.x) < 2 * WIDTH

    def update(self, level, hero):
        # Обновление состояния врага на каждом кадре, если герой в пределах видимости
        if self.is_near(hero):
            self.apply_gravity(level)
            self.move_and_process_blocks(level.blocks)
            self.check_world_boundaries(level)
            self.set_images()

    def reset(self):
        # Сброс в начальное состояние
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.vx = self.start_vx
        self.vy = self.start_vy
        self.current_images = self.images_left
        self.image = self.current_images[0]
        self.steps = 0


class Bear(Enemy):
    # Класс для представления медведя, наследуется от Enemy

    def __init__(self, x, y, images):
        super().__init__(x, y, images)

        self.start_x = x
        self.start_y = y
        self.start_vx = -2
        self.start_vy = 0

        self.vx = self.start_vx
        self.vy = self.start_vy


class Monster(Enemy):
    # Класс для представления монстра, наследуется от Enemy

    def __init__(self, x, y, images):
        super().__init__(x, y, images)

        self.start_x = x
        self.start_y = y
        self.start_vx = -2
        self.start_vy = 0

        self.vx = self.start_vx
        self.vy = self.start_vy

    def move_and_process_blocks(self, blocks):
        # Дополнительная обработка столкновений для монстра
        reverse = False

        self.rect.x += self.vx
        hit_list = pygame.sprite.spritecollide(self, blocks, False)

        for block in hit_list:
            if self.vx > 0:
                self.rect.right = block.rect.left
                self.reverse()
            elif self.vx < 0:
                self.rect.left = block.rect.right
                self.reverse()

        self.rect.y += self.vy + 1  # the +1 is hacky. not sure why it helps.
        hit_list = pygame.sprite.spritecollide(self, blocks, False)

        reverse = True

        for block in hit_list:
            if self.vy >= 0:
                self.rect.bottom = block.rect.top
                self.vy = 0

                if self.vx > 0 and self.rect.right <= block.rect.right:
                    reverse = False

                elif self.vx < 0 and self.rect.left >= block.rect.left:
                    reverse = False

            elif self.vy < 0:
                self.rect.top = block.rect.bottom
                self.vy = 0

        if reverse:
            self.reverse()


class OneUp(Entity):
    # Класс для представления бонуса "одна жизнь", наследуется от Entity

    def __init__(self, x, y, image):
        # Инициализация бонуса "одна жизнь"
        super().__init__(x, y, image)

    def apply(self, character):
        # Применение бонуса к персонажу
        character.lives += 1


class Heart(Entity):
    # Класс для представления бонуса "сердце", наследуется от Entity

    def __init__(self, x, y, image):
        # Инициализация бонуса "сердце"
        super().__init__(x, y, image)

    def apply(self, character):
        # Применение бонуса к персонажу
        character.hearts += 1
        character.hearts = max(character.hearts, character.max_hearts)


class Flag(Entity):
    # Класс для представления флага, наследуется от Entity

    def __init__(self, x, y, image):
        # Инициализация флага
        super().__init__(x, y, image)

# Определение класса Level
class Level():

    # Конструктор класса, инициализация атрибутов объекта
    def __init__(self, file_path):
        # Списки для хранения начальных объектов различных типов
        self.starting_blocks = []
        self.starting_enemies = []
        self.starting_coins = []
        self.starting_powerups = []
        self.starting_flag = []

        # Группы спрайтов для разных типов объектов
        self.blocks = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.flag = pygame.sprite.Group()

        # Группы для активных и неактивных спрайтов
        self.active_sprites = pygame.sprite.Group()
        self.inactive_sprites = pygame.sprite.Group()

        # Загрузка данных из файла
        with open(file_path, 'r') as f:
            data = f.read()

        map_data = json.loads(data)

        # Инициализация размеров уровня и начальной позиции игрока
        self.width = map_data['width'] * GRID_SIZE
        self.height = map_data['height'] * GRID_SIZE
        self.start_x = map_data['start'][0] * GRID_SIZE
        self.start_y = map_data['start'][1] * GRID_SIZE

        # Создание начальных объектов для разных типов
        for item in map_data['blocks']:
            x, y = item[0] * GRID_SIZE, item[1] * GRID_SIZE
            img = block_images[item[2]]
            self.starting_blocks.append(Block(x, y, img))

        for item in map_data['bears']:
            x, y = item[0] * GRID_SIZE, item[1] * GRID_SIZE
            self.starting_enemies.append(Bear(x, y, bear_images))

        for item in map_data['monsters']:
            x, y = item[0] * GRID_SIZE, item[1] * GRID_SIZE
            self.starting_enemies.append(Monster(x, y, monster_images))

        for item in map_data['coins']:
            x, y = item[0] * GRID_SIZE, item[1] * GRID_SIZE
            self.starting_coins.append(Coin(x, y, coin_img))

        for item in map_data['oneups']:
            x, y = item[0] * GRID_SIZE, item[1] * GRID_SIZE
            self.starting_powerups.append(OneUp(x, y, oneup_img))

        for item in map_data['hearts']:
            x, y = item[0] * GRID_SIZE, item[1] * GRID_SIZE
            self.starting_powerups.append(Heart(x, y, heart_img))

        for i, item in enumerate(map_data['flag']):
            x, y = item[0] * GRID_SIZE, item[1] * GRID_SIZE

            if i == 0:
                img = flag_img
            else:
                img = flagpole_img

            self.starting_flag.append(Flag(x, y, img))


        # Инициализация слоев для отображения уровня
        self.background_layer = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)
        self.scenery_layer = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)
        self.inactive_layer = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)
        self.active_layer = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)

        # Установка цвета фона и изображения заднего плана
        if map_data['background-color'] != "":
            self.background_layer.fill(map_data['background-color'])

        if map_data['background-img'] != "":
            background_img = pygame.image.load(map_data['background-img']).convert_alpha()
            # Обработка и позиционирование изображения заднего фона
            if map_data['background-fill-y']:
                h = background_img.get_height()
                w = int(background_img.get_width() * HEIGHT / h)
                background_img = pygame.transform.scale(background_img, (w, HEIGHT))

            if "top" in map_data['background-position']:
                start_y = 0
            elif "bottom" in map_data['background-position']:
                start_y = self.height - background_img.get_height()

            if map_data['background-repeat-x']:
                for x in range(0, self.width, background_img.get_width()):
                    self.background_layer.blit(background_img, [x, start_y])
            else:
                self.background_layer.blit(background_img, [0, start_y])

        # Загрузка изображения для слоя сцены (scenery)
        if map_data['scenery-img'] != "":
            scenery_img = pygame.image.load(map_data['scenery-img']).convert_alpha()
            # Обработка и позиционирование изображения сцены
            if map_data['scenery-fill-y']:
                h = scenery_img.get_height()
                w = int(scenery_img.get_width() * HEIGHT / h)
                scenery_img = pygame.transform.scale(scenery_img, (w, HEIGHT))

            if "top" in map_data['scenery-position']:
                start_y = 0
            elif "bottom" in map_data['scenery-position']:
                start_y = self.height - scenery_img.get_height()

            if map_data['scenery-repeat-x']:
                for x in range(0, self.width, scenery_img.get_width()):
                    self.scenery_layer.blit(scenery_img, [x, start_y])
            else:
                self.scenery_layer.blit(scenery_img, [0, start_y])


        # Инициализация физических параметров уровня
        self.gravity = map_data['gravity']
        self.terminal_velocity = map_data['terminal-velocity']

        # Флаг для отслеживания завершения уровня
        self.completed = False

        # Добавление начальных объектов в соответствующие группы
        self.blocks.add(self.starting_blocks)
        self.enemies.add(self.starting_enemies)
        self.coins.add(self.starting_coins)
        self.powerups.add(self.starting_powerups)
        self.flag.add(self.starting_flag)

        # Добавление групп в группы активных и неактивных спрайтов
        self.active_sprites.add(self.coins, self.enemies, self.powerups)
        self.inactive_sprites.add(self.blocks, self.flag)

        # Оптимизация конвертации изображений для ускорения отрисовки
        for s in self.active_sprites:
            s.image.convert()

        for s in self.inactive_sprites:
            s.image.convert()

        # Отрисовка неактивных спрайтов на неактивном слое
        self.inactive_sprites.draw(self.inactive_layer)

        # Конвертация изображений для всех слоев (возможно, для оптимизации)
        self.background_layer.convert()
        self.scenery_layer.convert()
        self.inactive_layer.convert()
        self.active_layer.convert()

    # Метод для сброса уровня
    def reset(self):
        # Добавление начальных врагов, монет и бонусов
        self.enemies.add(self.starting_enemies)
        self.coins.add(self.starting_coins)
        self.powerups.add(self.starting_powerups)

        # Добавление объектов в активные спрайты
        self.active_sprites.add(self.coins, self.enemies, self.powerups)

        # Сброс состояния каждого врага
        for e in self.enemies:
            e.reset()


# Определение класса Game
class Game():

    # Константы для состояний игры
    SPLASH = 0
    START = 1
    PLAYING = 2
    PAUSED = 3
    LEVEL_COMPLETED = 4
    GAME_OVER = 5
    VICTORY = 6

    # Инициализация объекта игры
    def __init__(self):
        # Создание окна pygame
        self.window = pygame.display.set_mode([WIDTH, HEIGHT])
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.done = False

        # Инициализация игровых параметров
        self.reset()

    # Метод для начала уровня
    def start(self):
        self.level = Level(levels[self.current_level])
        self.level.reset()
        self.hero.respawn(self.level)

    # Метод для перехода к следующему уровню
    def advance(self):
        self.current_level += 1
        self.start()
        self.stage = Game.START

    # Метод для сброса игры
    def reset(self):
        # Инициализация персонажа и текущего уровня
        self.hero = Character(hero_images)
        self.current_level = 0
        self.start()
        self.stage = Game.SPLASH

    # Метод для отображения заставки
    def display_splash(self, surface):
        line1 = FONT_LG.render(TITLE, 1, DARK_BLUE)
        line2 = FONT_SM.render("Press any key to start.", 1, WHITE)

        x1 = WIDTH / 2 - line1.get_width() / 2
        y1 = HEIGHT / 3 - line1.get_height() / 2

        x2 = WIDTH / 2 - line2.get_width() / 2
        y2 = y1 + line1.get_height() + 16

        surface.blit(line1, (x1, y1))
        surface.blit(line2, (x2, y2))

    # Метод для отображения сообщения
    def display_message(self, surface, primary_text, secondary_text):
        line1 = FONT_MD.render(primary_text, 1, WHITE)
        line2 = FONT_SM.render(secondary_text, 1, WHITE)

        x1 = WIDTH / 2 - line1.get_width() / 2
        y1 = HEIGHT / 3 - line1.get_height() / 2

        x2 = WIDTH / 2 - line2.get_width() / 2
        y2 = y1 + line1.get_height() + 16

        surface.blit(line1, (x1, y1))
        surface.blit(line2, (x2, y2))

    # Метод для отображения статистики
    def display_stats(self, surface):
        hearts_text = FONT_SM.render("Hearts: " + str(self.hero.hearts), 1, WHITE)
        lives_text = FONT_SM.render("Lives: " + str(self.hero.lives), 1, WHITE)
        score_text = FONT_SM.render("Score: " + str(self.hero.score), 1, WHITE)

        surface.blit(score_text, (WIDTH - score_text.get_width() - 32, 32))
        surface.blit(hearts_text, (32, 32))
        surface.blit(lives_text, (32, 64))

    # Метод для обработки событий
    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True

            elif event.type == pygame.KEYDOWN:
                if self.stage == Game.SPLASH or self.stage == Game.START:
                    self.stage = Game.PLAYING

                elif self.stage == Game.PLAYING:
                    if event.key == JUMP:
                        self.hero.jump(self.level.blocks)

                elif self.stage == Game.PAUSED:
                    pass

                elif self.stage == Game.LEVEL_COMPLETED:
                    self.advance()

                elif self.stage == Game.VICTORY or self.stage == Game.GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset()

        pressed = pygame.key.get_pressed()

        if self.stage == Game.PLAYING:
            if pressed[LEFT]:
                self.hero.move_left()
            elif pressed[RIGHT]:
                self.hero.move_right()
            else:
                self.hero.stop()

    # Метод для обновления состояния игры
    def update(self):
        if self.stage == Game.PLAYING:
            self.hero.update(self.level)
            self.level.enemies.update(self.level, self.hero)

        if self.level.completed:
            if self.current_level < len(levels) - 1:
                self.stage = Game.LEVEL_COMPLETED
            else:
                self.stage = Game.VICTORY
            pygame.mixer.music.stop()

        elif self.hero.lives == 0:
            self.stage = Game.GAME_OVER
            pygame.mixer.music.stop()

        elif self.hero.hearts == 0:
            self.level.reset()
            self.hero.respawn(self.level)

    # Метод для вычисления смещения отображения
    def calculate_offset(self):
        x = -1 * self.hero.rect.centerx + WIDTH / 2

        if self.hero.rect.centerx < WIDTH / 2:
            x = 0
        elif self.hero.rect.centerx > self.level.width - WIDTH / 2:
            x = -1 * self.level.width + WIDTH

        return x, 0

    # Метод для отрисовки состояния игры
    def draw(self):
        offset_x, offset_y = self.calculate_offset()

        # Заполнение активного слоя
        self.level.active_layer.fill(TRANSPARENT)
        self.level.active_sprites.draw(self.level.active_layer)

        # Отображение персонажа (с учетом неуязвимости)
        if self.hero.invincibility % 3 < 2:
            self.level.active_layer.blit(self.hero.image, [self.hero.rect.x, self.hero.rect.y])

        # Отображение слоев уровня на экране
        self.window.blit(self.level.background_layer, [offset_x / 3, offset_y])
        self.window.blit(self.level.scenery_layer, [offset_x / 2, offset_y])
        self.window.blit(self.level.inactive_layer, [offset_x, offset_y])
        self.window.blit(self.level.active_layer, [offset_x, offset_y])

        # Отображение статистики
        self.display_stats(self.window)

        # Отображение соответствующего экрана в зависимости от состояния игры
        if self.stage == Game.SPLASH:
            self.display_splash(self.window)
        elif self.stage == Game.START:
            self.display_message(self.window, "Ready?!!!", "Press any key to start.")
        elif self.stage == Game.PAUSED:
            pass
        elif self.stage == Game.LEVEL_COMPLETED:
            self.display_message(self.window, "Level Complete", "Press any key to continue.")
        elif self.stage == Game.VICTORY:
            self.display_message(self.window, "You Win!", "Press 'R' to restart.")
        elif self.stage == Game.GAME_OVER:
            self.display_message(self.window, "Game Over", "Press 'R' to restart.")

        # Обновление экрана
        pygame.display.flip()

    # Основной цикл игры
    def loop(self):
        while not self.done:
            self.process_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

# Запуск игры при запуске файла
if __name__ == "__main__":
    game = Game()
    game.start()
    game.loop()
    pygame.quit()
    sys.exit()