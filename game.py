#! /usr/bin/python3
# coding=utf-8

import base64
import struct
import math
import time
import random

import pygame
from pygame.locals import *

# import server

WINDOWWIDTH = 640
WINDOWHEIGHT = 480
WINMIDX = WINDOWWIDTH / 2
WINMIDY = WINDOWHEIGHT / 2

NAMECOLOR = (255, 255, 255)
NAMEBG = (64, 64, 64)

FPS = 60

CAMERAH = 10
CARRADIUM = 64


class PlayerData:
    """
    玩家数据
    """

    def __init__(self, name):
        # name
        self.name = name

        # second, provides last update time
        self.time = 0

        # position
        self.pos_x = 200
        self.pos_y = 200

        # sqrt(self.motion_x ** 2 + self.motion_y ** 2)
        self.speed = 1

        # rotation in rad
        self.rotation = 0

    @property
    def motion_x(self):
        return self.speed * math.sin(self.rotation)

    @property
    def motion_y(self):
        return -self.speed * math.cos(self.rotation)

    @motion_x.setter
    def motion_x(self, x):
        y = self.motion_y
        if self.speed > 0:
            self.speed = math.sqrt(x ** 2 + y ** 2)
            if y < 0: self.rotation = math.asin(x / self.speed) % (2 * math.pi)
            elif y > 0: self.rotation = math.pi - math.asin(x / self.speed)
        elif self.speed < 0:
            self.speed = -math.sqrt(x ** 2 + y ** 2)
            if y > 0: self.rotation = -math.asin(-x / self.speed) % (2 * math.pi)
            elif y < 0: self.rotation = math.asin(-x / self.speed) + math.pi

    @motion_y.setter
    def motion_y(self, y):
        x = self.motion_x
        if self.speed > 0:
            self.speed = math.sqrt(x ** 2 + y ** 2)
            if x < 0: self.rotation = 2 * math.pi - math.acos(-y / self.speed)
            elif x > 0: self.rotation = math.acos(-y / self.speed)
        elif self.speed < 0:
            self.speed = -math.sqrt(x ** 2 + y ** 2)
            if x > 0: self.rotation = math.acos(y / self.speed) + math.pi
            elif x < 0: self.rotation = math.pi - math.acos(y / self.speed)

    def update_tick(self, time, map_data):

        self.check_collision(time, map_data)
        dt = time - self.time
        self.time = time
        self.pos_x += dt * self.motion_x
        self.pos_y += dt * self.motion_y
        self.speed *= 1 - dt
        # self.speed = (1 if self.speed > 0 else -1) * math.sqrt(self.motion_x ** 2 + self.motion_y ** 2)
        if self.speed != 0:
            self.rotation = self.rotation % (2 * math.pi)

    def check_collision(self, time, map_data):
        """
        撞！
        map_data为函数指针，传入一个表示横坐标和一个纵坐标的tuple，返回一个表示墙面高度和角度的tuple
        """
        dt = time - self.time
        # FIXME：->_->为便于修改，这里定义了两个变量作控制变量，wzb你给不出我希望的地图格式的话，可以修改这里
        # by ustc-zzzz: 你放个函数指针进去会shi啊->_->
        wall_height = map_data.wall((self.pos_x, self.pos_y))
        wall_height_x, wall_height_y = wall_height
        # 这里是外边界处的碰撞判断
        width, height =  map_data.size()
        motion_x, motion_y = self.motion_x, self.motion_y
        if self.pos_x <= 0 and motion_x < 0:  # 这些应该能懂，不懂参见下面...
            self.motion_x *= 0
        elif self.pos_x >= width - 1 and motion_x > 0:
            self.motion_x *= 0
        if self.pos_y <= 0 and motion_y < 0:
            self.motion_y *= 0
        elif self.pos_y >= height - 1 and motion_y > 0:
            self.motion_y *= 0
        # 这里是其它位置的碰撞判断
        # 碰撞导致减速，1/2的目的是使碰撞削减速度（防止碰撞的惩罚措施）
        self.motion_x -= wall_height_x * dt * 32
        self.motion_y -= wall_height_y * dt * 32
        # 没必要，下一tick会自动处理
        # self.speed = (1 if self.speed > 0 else -1) * math.sqrt(self.motion_x ** 2 + self.motion_y ** 2)
        # self.pos_x = dt * self.motion_x  # 碰撞导致漂移
        # self.pos_y = dt * self.motion_y

class MapData:

    def __init__(self, width, height, map_func):
        self._width = width
        self._height = height
        self._func = map_func

    def size(self):
        return (self._width, self._height)

    def wall(self, pos):
        x, y = pos
        return self._func(x, y)

    @staticmethod
    def get_map_data(map_image):
        width, height = map_image.get_size()

        def map_func(x, y):
            def gray_scale(color):
                return 0.2989 * color.r + 0.5870 * color.g + 0.1140 * color.b

            def check_range(number, bound):
                return min(max(number, 0), bound - 1)

            pos_x, pos_y = round(x), round(y)
            pixel_top_right = gray_scale(map_image.get_at((check_range(pos_x, width), check_range(pos_y - 1, height))))
            pixel_top_left = gray_scale(map_image.get_at((check_range(pos_x - 1, width), check_range(pos_y - 1, height))))
            pixel_bottom_left = gray_scale(map_image.get_at((check_range(pos_x - 1, width), check_range(pos_y, height))))
            pixel_bottom_right = gray_scale(map_image.get_at((check_range(pos_x, width), check_range(pos_y, height))))
            diff_x = (pixel_top_left + pixel_bottom_left - pixel_top_right - pixel_bottom_right)
            diff_y = (pixel_top_left + pixel_top_right - pixel_bottom_left - pixel_bottom_right)
            return diff_x, diff_y

        return MapData(width, height, map_func)


class Display:
    def __init__(self, start_time, key_binding, game_server):
        """
        产生一个display对象

        参数：
            start_time      游戏时间为0时的UNIX时间戳
            on_key_down     方向键被按下时的处理函数
            ...       ...
        """
        self.startTime = start_time
        self.key_binding = key_binding
        self.surf = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        self.game_server = game_server
        self.last_tick = time.time() - self.startTime
        self.running = True
        self.state_changed = True
        self.theme_index = 0
        self.theme = "normal"

        self.map_data_image = pygame.image.load('map_data.png')
        self.map_width = self.map_data_image.get_width()
        self.map_height = self.map_data_image.get_height()
        self.map_data = MapData.get_map_data(self.map_data_image)

        self.player_data = [PlayerData("Player" + str(random.randrange(1000, 10000))), PlayerData('玩家2')]
        self.current_player = self.player_data[0]

    def handle_key(self, time):
        """
        响应键盘事件
        """
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE: self.stop()
        self.state_changed = self.key_binding.update(lambda key: pygame.key.get_pressed()[key], time, self)

    def send_changes(self):
        if self.state_changed:
            packed = struct.pack('3f', self.current_player.time, self.current_player.speed, self.current_player.rotation)
            self.game_server.send_packet("C:" + str(base64.b64encode(packed), "utf-8"))

    def calculate_offset(self, pos_x, pos_y):
        x = min(max(WINMIDX - self.current_player.pos_x, WINDOWWIDTH - self.map_width), 0) + pos_x
        y = min(max(WINMIDY - self.current_player.pos_y, WINDOWHEIGHT - self.map_height), 0) + pos_y
        return (x, y)

    def draw_map(self, player_data):
        """
        背景图
        """
        mapImage = pygame.image.load(self.theme + '/map.png').convert(32, SRCALPHA)
        mapRect = mapImage.get_rect()
        mapRect.topleft = self.calculate_offset(0, 0)
        self.surf.blit(mapImage, mapRect)

    def draw_car(self, player_data):
        """
        快上车
        """
        carImagePath = self.theme + ('/mycar.png' if player_data.name is self.current_player.name else "/car.png")
        carImage = pygame.image.load(carImagePath).convert(32, SRCALPHA)
        rotatedCar = pygame.transform.rotate(carImage, -player_data.rotation * 180 / math.pi)
        carRect = rotatedCar.get_rect()
        carRect.center = self.calculate_offset(player_data.pos_x, player_data.pos_y)
        self.surf.blit(rotatedCar, carRect)
        font = pygame.font.Font('font/wqy-microhei.ttc', 18)
        nameSurf = font.render(player_data.name, True, NAMECOLOR)
        nameRect = nameSurf.get_rect()
        nameRect.center = self.calculate_offset(player_data.pos_x, player_data.pos_y - 48)
        # FIXME: 这里还有点问题，先去掉
        # surf.fill(NAMEBG, nameRect)
        self.surf.blit(nameSurf, nameRect)

    def draw_building(self, player_data):
        """
        建筑物
        """
        # TODO: Your work, FasdSnake
        pass

    def draw_cars(self):
        """
        所有的车
        """
        for player_data in self.player_data:
            if (player_data.name != self.current_player.name):
                self.draw_car(player_data)
        self.draw_car(self.current_player)

    def tick_player(self, t):
        """
        玩家逻辑
        """
        for player_data in self.player_data:
            player_data.update_tick(t, self.map_data)

    def tick(self, t):
        """
        Game loop
        """
        # key events
        self.handle_key(t)
        # tick player
        self.tick_player(t)
        self.send_changes()
        # draw
        self.draw_map(self.current_player)
        self.draw_building(self.current_player)
        self.draw_cars()
        # update
        pygame.display.update()
        self.last_tick = t

    def show(self):
        """
        循环显示游戏界面

        此函数直到stop被调用后才会返回
        """
        pygame.init()
        clock = pygame.time.Clock()
        pygame.display.set_caption('Ice Mud Game')
        self.game_server.send_packet('L:' + self.current_player.name)
        self.send_changes()
        while self.running:
            self.tick(time.time() - self.startTime)
            clock.tick(FPS)
        pygame.quit()

    def stop(self):
        """
        结束游戏，使show调用返回
        """
        self.game_server.send_packet('E:')
        self.running = False

    def read_player_data(self, data, message):
        try:
            packed_data = message.split('\x00')[:-1:]
            data_dict = {}
            for packed in packed_data:
                name = packed[28::]
                data_dict[name] = packed[:28:]
            for player in data:
                if player.name in data_dict:
                    packed = base64.b64decode(data_dict[player.name])
                    pos_x, pos_y, player.speed, player.rotation, player.time = struct.unpack('5f', packed)
                    player.pos_x = pos_x
                    player.pos_y = pos_y
                    player.update_tick(self.last_tick, self.map_data)
                    data_dict.pop(player.name)
                else:
                    data.remove(player)
            for name, packed in data_dict.items():
                player = PlayerData(name)
                pos_x, pos_y, player.speed, player.rotation, player.time = struct.unpack('5f', base64.b64decode(packed))
                player.pos_x = pos_x
                player.pos_y = pos_y
                player.update_tick(self.last_tick, self.map_data)
                data_dict.pop(player.name)
        except:
            pass

class KeyBinding:

    def __init__(self):
        self.counter = 3
        self.themes = ["normal", "simple", "excited"]
        self.theme_changed = True

    def update(self, is_key_pressed, time, display):
        if (is_key_pressed(K_e)):
            if self.theme_changed:
                display.theme_index = (display.theme_index + 1) % len(self.themes)
                display.theme = self.themes[display.theme_index]
                self.theme_changed = False
        elif not self.theme_changed:
            self.theme_changed = True
        flag = False
        if (is_key_pressed(K_UP)):
            self.up(display, time)
            flag = True
        if (is_key_pressed(K_DOWN)):
            self.down(display, time)
            flag = True
        if (is_key_pressed(K_LEFT)):
            self.left(display, time)
            flag = True
        if (is_key_pressed(K_RIGHT)):
            self.right(display, time)
            flag = True
        if self.counter >= 3:
            self.counter = 0
            return flag
        else:
            self.counter += 1
            return False


    def up(self, display, time):
        display.current_player.speed += (time - display.last_tick) * ((2048 - display.current_player.speed) / 16 + 64 * random.random())


    def down(self, display, time):
        display.current_player.speed -= (time - display.last_tick) * ((2048 + display.current_player.speed) / 16 + 64 * random.random())


    def left(self, display, time):
        display.current_player.rotation -= (time - display.last_tick) * 0.5


    def right(self, display, time):
        display.current_player.rotation += (time - display.last_tick) * 0.5


def dummy_display(game_server):
    return Display(time.time() - 4, KeyBinding(), game_server)
