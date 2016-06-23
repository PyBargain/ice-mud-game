#!/usr/bin/python3
# encoding=utf8


import math, time, pygame


class Player:
    def __init__(self):
        self.kUp = False
        self.kDown = False
        self.kLeft = False
        self.kRight = False
        self.name = 'Player'
        self.t = 0
        self.x = 200
        self.y = 200
        self.vx = 0
        self.vy = 0
        self.d = 0

    def tick(self, t):
        dt = t - self.t
        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        self.side = self.vx * math.cos(math.radians(self.d)) - self.vy * math.sin(math.radians(self.d))
        self.vx -= self.side * math.cos(math.radians(self.d)) / 4
        self.vy += self.side * math.sin(math.radians(self.d)) / 4
        if self.kUp:
            self.vx -= dt * math.sin(math.radians(self.d))
            self.vy -= dt * math.cos(math.radians(self.d))
            print(repr((self.vx, self.vy)))
        if self.kDown:
            self.vx += dt * math.sin(math.radians(self.d))
            self.vy += dt * math.cos(math.radians(self.d))
        if self.kLeft:
            self.d += dt * 30
        if self.kRight:
            self.d -= dt * 30
        self.t = t

    def keyEvent(self, k):
        if k == 'U': self.kUp = True
        elif k == 'u': self.kUp = False
        elif k == 'D': self.kDown = True
        elif k == 'd': self.kDown = False
        elif k == 'L': self.kLeft = True
        elif k == 'l': self.kLeft = False
        elif k == 'R': self.kRight = True
        elif k == 'r': self.kRight = False

    def setName(self, name):
        self.name = name

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
                h, s, v, a = color.hsva
                return v * 2.56

            def check_range(number, bound):
                return min(max(number, 0), bound - 1)

            def get_gray_scale(pos_x, pos_y):
                return gray_scale(map_image.get_at((check_range(pos_x, width), check_range(pos_y, height))))

            pos_x, pos_y = round(x), round(y)
            pixel_top_right = get_gray_scale(pos_x, pos_y - 1)
            pixel_top_left = get_gray_scale(pos_x - 1, pos_y - 1)
            pixel_bottom_left = get_gray_scale(pos_x - 1, pos_y)
            pixel_bottom_right = get_gray_scale(pos_x, pos_y)
            diff_x = (pixel_top_left + pixel_bottom_left - pixel_top_right - pixel_bottom_right)
            diff_y = (pixel_top_left + pixel_top_right - pixel_bottom_left - pixel_bottom_right)
            return diff_x, diff_y

        return MapData(width, height, map_func)


class Game:
    def __init__(self, players, startTime):
        self.players = players
        self.startTime = startTime
        self.map_data = MapData.get_map_data(pygame.image.load('map_data.png'))

    def tick(self):
        for p in self.players:
            p.tick(time.time() - self.startTime)
            self.checkCollision(p)

    def checkCollision(self, player):
        dt = time.time() - self.startTime
        wall_height = self.map_data.wall((player.x, player.y))
        wall_height_x, wall_height_y = wall_height
        # 这里是外边界处的碰撞判断
        width, height = self.map_data.size()
        motion_x, motion_y = player.vx, player.vy
        # 这些应该能懂，不懂参见下面...
        '''
        if player.x <= 0 and motion_x < 0:
            player.vx = 0
            player.x = -1
        elif player.x >= width - 1 and motion_x > 0:
            player.vx = 0
            player.x = width
        if player.y <= 0 and motion_y < 0:
            player.vy = 0
            player.y = -1
        elif player.y >= height - 1 and motion_y > 0:
            player.vy = 0
            player.y = height
        '''
        # 这里是其它位置的碰撞判断
        # 碰撞导致减速，1/2的目的是使碰撞削减速度（防止碰撞的惩罚措施）
        # player.x -= dt * player.vx * (wall_height_x / 256) ** 2  # 碰撞导致漂移
        # player.y -= dt * player.vy * (wall_height_y / 256) ** 2
        player.vx *= math.exp(-0.25 * wall_height_x * wall_height_x)
        player.vy *= math.exp(-0.25 * wall_height_y * wall_height_y)
        player.x -= 0.25 * wall_height_x
        player.y -= 0.25 * wall_height_y


    def getState(self):
        retval = []
        for p in self.players:
            retval.append([p.name, p.t, p.x, p.vx, p.y, p.vy, p.d])
        return retval
