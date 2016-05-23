#! /usr/bin/python3
# coding=utf-8

import base64, struct
import math, time
import random

import pygame
from pygame.locals import *

WINDOWWIDTH = 640
WINDOWHEIGHT = 480
WINMIDX = WINDOWWIDTH / 2
WINMIDY = WINDOWHEIGHT / 2
NAMECOLOR = (255, 255, 255)
NAMEBG = (64, 64, 64)
FPS = 30
CAMERAH = 10


class Building:
    def __init__(self, rect, height, image):
        '''
        产生一个建筑物对象

        参数：
            rect    pygame的Rect对象，描述建筑物的底部矩形
            height  建筑物高度
            image   建筑物的表面贴图方案

        我们假定摄像机位于高度10处
        '''
        self.rect = rect
        self.height = height
        # TODO: SMG->_->, by ustc-zzzz
        # self.side, self.top = BUILDINGIMG[image]
        self.scale = CAMERAH / (CAMERAH - height)
        self._screenr = pygame.rect.Rect(rect)
        self._screenr.w *= self.scale
        self._screenr.h *= self.scale

    def toprect(self, x, y):
        '''
        返回镜头位于特定坐标时，建筑物顶部在屏幕上的矩形

        返回的对象可能会在未来被改变
        '''
        self._screenr.centerx = (WINMIDX + self.rect.centerx - x) * self.scale
        self._screenr.centery = (WINMIDY + self.rect.centery - y) * self.scale
        return self._screenr

    def side(self, x, y):
        '''
        返回用于遮挡解算的信息(ld, rd, lw, rw)
            (ld, rd)    正上方为最小值，顺时针方向递增的两个类角度量，刻画了镜头位于特定坐标时该建筑物所占据的视角
            (lw, rw)    该建筑物所占据的视角最两侧的点到镜头的类距离
        '''
        left = self.rect.left
        right = self.rect.right
        top = self.rect.top
        bottom = self.rect.bottom

        def calcdw(x, y):
            return (x / y if y > x else 2 - y / x, x * x + y * y)

        if x > left:
            if y > bottom:
                # l为左下角
                ld, lw = 6 + calcdw(y - bottom, x - left)
            if y < top:
                # r为左上角
                rd, rw = 4 + calcdw(x - left, top - y)
        else:
            if y > top:
                # l为左上角
                ld, lw = 0 + calcdw(left - x, y - top)
            if y < bottom:
                # r为左下角
                rd, rw = 2 + calcdw(bottom - y, left - x)
        if x > right:
            if y < bottom:
                # l为右下角
                ld, lw = 4 + calcdw(x - right, bottom - y)
            if y > top:
                # r为右上角
                rd, rw = 6 + calcdw(y - top, x - right)
        else:
            if y < top:
                # l为右上角
                ld, lw = 2 + calcdw(top - y, right - x)
            if y > bottom:
                # r为右下角
                rd, rw = 0 + calcdw(y - bottom, right - x)
        return (ld, rd, lw, rw)

    def draw(self, x, y, display):
        '''
        将建筑物绘制在display上
        '''
        rect = self.rect
        toprect = self.toprect(x, y)
        if x > rect.right:
            # 画左侧面
            left = rect.left
            ltop = rect.top
            lbottom = rect.bottom
            right = toprect.left
            rtop = toprect.top
            rbottom = toprect.bottom
            width = right - left
            for i in range(left, right):
                top = (i - left) * (rtop - ltop) // width + ltop
                bottom = (i - left) * (rbottom - lbottom) // width + lbottom
                display.blit(pygame.transform.rotate(self.side, 90),
                             Rect(i, top, 1, bottom - top),
                             Rect((i - left) * self.side.height // width, 0, (self.side.height + width - 1) // width,
                                  self.side.width))
        elif x < rect.left:
            # 画右侧面
            pass
        if y > rect.bottom:
            # 画上侧面
            pass
        elif y < rect.top:
            # 画下侧面
            pass
        # 画顶面
        display.blit(self.top, toprect)


class PlayerData:
    '''
    玩家数据
    '''

    def __init__(self, name):
        # name
        self.name = name

        # second
        self.time = 0

        # position
        self.pos_x = 200
        self.pos_y = 200

        # speed
        self.motion_x = 0
        self.motion_y = 0

        # sqrt(self.motion_x ** 2 + self.motion_y ** 2)
        self.speed = 1

        # rotation in rad
        self.rotation = 0

    def update_tick(self, time):
        dt = self.time - time
        self.time = time
        self.motion_x = self.speed * math.sin(self.rotation)
        self.motion_y = self.speed * math.cos(self.rotation)
        self.pos_x += dt * self.motion_x
        self.pos_y += dt * self.motion_y
        self.speed = math.sqrt(self.motion_x ** 2 + self.motion_y ** 2)
        if self.speed != 0:
            self.rotation = math.acos(self.motion_y / self.speed) \
                if self.motion_x > 0 \
                else - math.acos(self.motion_y / self.speed)


class Display:
    def __init__(self, startTime, getData, thePlayerData, upDown, upUp, downDown, downUp,
                 leftDown, leftUp, rightDown, rightUp, game_server):
        '''
        产生一个display对象

        参数：
            startTime 游戏时间为0时的UNIX时间戳
            getData   返回值为[(昵称, 游戏时间, 赛车X, 赛车X速度, 赛车Y, 赛车Y速度, 赛车方向), ...]的函数
            upDown    方向键“上”被按下时的处理函数
            ...       ...
        '''
        self.startTime = startTime
        self.getData = getData
        self.thePlayerData = thePlayerData
        self.onKeyDown = {K_UP: upDown, K_DOWN: downDown, K_LEFT: leftDown, K_RIGHT: rightDown}
        self.onKeyUp = {K_UP: upUp, K_DOWN: downUp, K_LEFT: leftUp, K_RIGHT: rightUp}
        self.surf = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        self.game_server = game_server
        self.last_tick = time.time() - self.startTime
        self.running = True
        self.state_changed = True

        self.map_width = 0
        self.map_height = 0

    def handle_key(self):
        '''
        响应键盘事件
        '''
        self.state_changed = False
        for event in pygame.event.get():
            if event.type == KEYUP:
                if event.key in self.onKeyUp:
                    self.onKeyUp[event.key]()
                if event.key == K_ESCAPE:
                    self.stop()
            if event.type == KEYDOWN:
                if event.key in self.onKeyDown:
                    self.onKeyDown[event.key]()
            self.state_changed = True

    def send_changes(self):
        if self.state_changed:
            packed = struct.pack('3f', self.thePlayerData.time, self.thePlayerData.speed, self.thePlayerData.rotation)
            self.game_server.send_packet("C:" + str(base64.b64encode(packed), "utf-8"))

    def calculate_offset(self, pos_x, pos_y):
        x = min(max(WINMIDX - self.thePlayerData.pos_x, WINDOWWIDTH - self.map_width), 0) + pos_x
        y = min(max(WINMIDY - self.thePlayerData.pos_y, WINDOWHEIGHT - self.map_height), 0) + pos_y
        return (x, y)

    def draw_map(self, player_data):
        '''
        背景图
        '''
        mapImage = pygame.image.load('map.png').convert(32, SRCALPHA)
        mapRect = mapImage.get_rect()
        self.map_width, self.map_height = mapRect[2], mapRect[3]
        mapRect.topleft = self.calculate_offset(0, 0)
        self.surf.blit(mapImage, mapRect)

    def draw_car(self, player_data):
        '''
        快上车
        '''
        carImage = pygame.image.load('car.png').convert(32, SRCALPHA)
        rotatedCar = pygame.transform.rotate(carImage, player_data.rotation * 180 / math.pi)
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
        '''
        建筑物
        '''
        # TODO: Your work, FasdSnake
        pass

    def draw_cars(self):
        '''
        所有的车
        '''
        for player_data in self.getData():
            self.draw_car(player_data)

    def tick_player(self, t):
        '''
        玩家逻辑
        '''
        for player_data in self.getData():
            player_data.update_tick(t)

    def tick(self, t):
        '''
        Game loop
        '''
        # key events
        self.handle_key()
        # tick player
        self.tick_player(t)
        self.send_changes()
        # draw
        self.draw_map(self.thePlayerData)
        self.draw_building(self.thePlayerData)
        self.draw_cars()
        # update
        pygame.display.update()
        self.last_tick = t

    def show(self):
        '''
        循环显示游戏界面

        此函数直到stop被调用后才会返回
        '''
        pygame.init()
        clock = pygame.time.Clock()
        pygame.display.set_caption('Ice Mud Game')
        self.game_server.send_packet('L:' + self.thePlayerData.name)
        self.send_changes()
        while self.running:
            self.tick(time.time() - self.startTime)
            clock.tick(FPS)
        pygame.quit()

    def stop(self):
        '''
        结束游戏，使show调用返回
        '''
        self.game_server.send_packet('E:')
        self.running = False

    def read_player_data(self, data, message):
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
                player.update_tick(self.last_tick)
                data_dict.pop(player.name)
            else:
                data.remove(player)
        for name, packed in data_dict.items():
            player = PlayerData(name)
            pos_x, pos_y, player.speed, player.rotation, player.time = struct.unpack('5f', base64.b64decode(packed))
            player.pos_x = pos_x
            player.pos_y = pos_y
            player.update_tick(self.last_tick)
            data.append(player)


def nop():
    pass


player_data = [PlayerData("Player" + str(random.randrange(1000, 10000))), PlayerData('玩家2')]

current_player = player_data[0]


def get_data():
    return player_data


def up():
    current_player.speed += 50 + 5 * random.random()


def down():
    current_player.speed -= 50 + 5 * random.random()


def left():
    current_player.rotation += 0.1


def right():
    current_player.rotation -= 0.1


def dummy_display(game_server):
    return Display(time.time() - 4, get_data, current_player, up, nop, down, nop, left, nop, right, nop, game_server)
