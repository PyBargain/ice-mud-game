#! /usr/bin/python3
# coding=utf-8

import math


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
            if y < 0:
                self.rotation = math.asin(x / self.speed) % (2 * math.pi)
            elif y > 0:
                self.rotation = math.pi - math.asin(x / self.speed)
        elif self.speed < 0:
            self.speed = -math.sqrt(x ** 2 + y ** 2)
            if y > 0:
                self.rotation = -math.asin(-x / self.speed) % (2 * math.pi)
            elif y < 0:
                self.rotation = math.asin(-x / self.speed) + math.pi

    @motion_y.setter
    def motion_y(self, y):
        x = self.motion_x
        if self.speed > 0:
            self.speed = math.sqrt(x ** 2 + y ** 2)
            if x < 0:
                self.rotation = 2 * math.pi - math.acos(-y / self.speed)
            elif x > 0:
                self.rotation = math.acos(-y / self.speed)
        elif self.speed < 0:
            self.speed = -math.sqrt(x ** 2 + y ** 2)
            if x > 0:
                self.rotation = math.acos(y / self.speed) + math.pi
            elif x < 0:
                self.rotation = math.pi - math.acos(y / self.speed)

    def update_tick(self, time, map_data):

        self.check_collision(time, map_data)
        dt = time - self.time
        self.time = time
        self.pos_x += dt * self.motion_x
        self.pos_y += dt * self.motion_y
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
        width, height = map_data.size()
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
        self.pos_x -= dt * self.motion_x * (wall_height_x / 256) ** 2 / 4  # 碰撞导致漂移
        self.pos_y -= dt * self.motion_y * (wall_height_y / 256) ** 2 / 4
        self.motion_x -= wall_height_x * dt * 32
        self.motion_y -= wall_height_y * dt * 32


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
            pixel_top_left = gray_scale(
                map_image.get_at((check_range(pos_x - 1, width), check_range(pos_y - 1, height))))
            pixel_bottom_left = gray_scale(
                map_image.get_at((check_range(pos_x - 1, width), check_range(pos_y, height))))
            pixel_bottom_right = gray_scale(map_image.get_at((check_range(pos_x, width), check_range(pos_y, height))))
            diff_x = (pixel_top_left + pixel_bottom_left - pixel_top_right - pixel_bottom_right)
            diff_y = (pixel_top_left + pixel_top_right - pixel_bottom_left - pixel_bottom_right)
            return diff_x, diff_y

        return MapData(width, height, map_func)


class Constants:
    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 480
    WIN_MIDDLE_X = WINDOW_WIDTH / 2
    WIN_MIDDLE_Y = WINDOW_HEIGHT / 2

    NAME_COLOR = (255, 255, 255)
    NAME_BG = (64, 64, 64)

    FPS = 60
