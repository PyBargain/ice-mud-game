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
        self.x = 668
        self.y = 963
        self.vx = 0
        self.vy = 0
        self.d = 0
        self.isPayed = False
        self.stage = 0

    def tick(self, t):
        dt = t - self.t
        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        self.side = self.vx * math.cos(math.radians(self.d)) - self.vy * math.sin(math.radians(self.d))
        self.vx -= self.side * math.cos(math.radians(self.d)) / 1
        self.vy += self.side * math.sin(math.radians(self.d)) / 1
        if self.kUp:
            self.vx -= dt * math.sin(math.radians(self.d))
            self.vy -= dt * math.cos(math.radians(self.d))
        if self.kDown:
            self.vx += dt * math.sin(math.radians(self.d))
            self.vy += dt * math.cos(math.radians(self.d))
        if self.kLeft:
            self.d += dt * 60
        if self.kRight:
            self.d -= dt * 60
        self.t = t
        if self.stage == 0 and self.x > 1500:
            self.stage = 1
        if self.stage == 1 and self.x < 1000 and self.y <= 991 and self.y >= 935:
            self.stage = 2

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
            pixel_top_right = get_gray_scale(pos_x, pos_y - 50)
            pixel_top_left = get_gray_scale(pos_x - 50, pos_y - 50)
            pixel_bottom_left = get_gray_scale(pos_x - 50, pos_y)
            pixel_bottom_right = get_gray_scale(pos_x, pos_y)
            diff_x = (pixel_top_left + pixel_bottom_left - pixel_top_right - pixel_bottom_right)
            diff_y = (pixel_top_left + pixel_top_right - pixel_bottom_left - pixel_bottom_right)
            return diff_x, diff_y

        return MapData(width, height, map_func)


TABLE = { # ul   dl     ur      dr      x   y
        (False, False, False, False): ( 0,  0),
        (False, False, False, True ): ( 1,  1),
        (False, False, True , False): ( 1, -1),
        (False, False, True , True ): ( 1,  0),
        (False, True , False, False): (-1,  1),
        (False, True , False, True ): ( 0,  1),
        (False, True , True , False): ( 0,  0),
        (False, True , True , True ): ( 1,  1),
        (True , False, False, False): (-1, -1),
        (True , False, False, True ): ( 0,  0),
        (True , False, True , False): ( 0, -1),
        (True , False, True , True ): ( 1, -1),
        (True , True , False, False): (-1,  0),
        (True , True , False, True ): (-1,  1),
        (True , True , True , False): (-1, -1),
        (True , True , True , True ): ( 0,  0)
}


class Game:
    def __init__(self, players, startTime):
        self.players = players
        self.startTime = startTime
        self.map_data_image = pygame.image.load('map_data.png')
        self.map_data = MapData.get_map_data(self.map_data_image)

    def tick(self):
        for p in self.players:
            p.tick(time.time() - self.startTime)
            self.checkCollision(p)

    def checkCollision(self, player):
        def get_v(pos):
            return self.map_data_image.get_at((int(pos[0]), int(pos[1]))).hsva[2] > 50
        if get_v((player.x, player.y)):
            return
        neighbor = tuple(map(get_v, [
            (player.x-30, player.y-30),
            (player.x-30, player.y+30),
            (player.x+30, player.y-30),
            (player.x+30, player.y+30)]))
        player.x += TABLE[neighbor][0] * 2
        player.y += TABLE[neighbor][1] * 2
        if TABLE[neighbor][0]: player.vx = 0
        if TABLE[neighbor][1]: player.vy = 0
        return


    def getState(self):
        retval = []
        for p in self.players:
            retval.append([p.name, p.t, p.x, p.vx, p.y, p.vy, p.d])
        return retval
