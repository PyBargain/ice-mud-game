#! /usr/bin/python3
# coding=utf-8


import math, time

import pygame
from pygame.locals import *


WINDOWWIDTH = 640
WINDOWHEIGHT = 480
WINMIDX = WINDOWWIDTH / 2
WINMIDY = WINDOWHEIGHT / 2
NAMECOLOR = (255, 255, 255)
NAMEBG = (64, 64, 64)
FPS = 30


class Display:

    def __init__(self, startTime, getData, upDown, upUp, downDown, downUp,
            leftDown, leftUp, rightDown, rightUp):
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
        self.onKeyDown = {K_UP: upDown, K_DOWN: downDown, K_LEFT: leftDown, K_RIGHT: rightDown}
        self.onKeyUp = {K_UP: upUp, K_DOWN: downUp, K_LEFT: leftUp, K_RIGHT: rightUp}
        self.running = True

    def show(self):
        '''
        循环显示游戏界面

        此函数直到stop被调用后才会返回
        '''
        pygame.init()
        clock = pygame.time.Clock()
        surf = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        # 路径'C:\\WINDOWS\\Fonts\\STSONG.TTF'已弃用
        font = pygame.font.Font('font/wqy-microhei.ttc', 18)
        mapImage = pygame.image.load('map.png').convert(32, SRCALPHA)
        mapRect = mapImage.get_rect()
        carImage = pygame.image.load('car.png').convert(32, SRCALPHA)
        pygame.display.set_caption('Ice Mud Game')
        while self.running:
            t = time.time() - self.startTime
            for event in pygame.event.get():
                if event.type == KEYUP:
                    if event.key in self.onKeyUp:
                        self.onKeyUp[event.key]()
                    if event.key == K_ESCAPE:
                        self.stop()
                if event.type == KEYDOWN:
                    if event.key in self.onKeyDown:
                        self.onKeyDown[event.key]()
            data = self.getData()
            name, t0, x, dx, y, dy, drct = data[0]
            dt = t - t0
            cx = x + dt * dx
            cy = y + dt * dy
            # draw map
            mapRect.topleft = (WINMIDX - cx, WINMIDY - cy)
            surf.blit(mapImage, mapRect)
            # draw buildings
            pass
            # draw cars
            for name, t0, x, dx, y, dy, drct in reversed(data):
                x += dt * dx - cx
                y += dt * dy - cy
                rotatedCar = pygame.transform.rotate(carImage, drct)
                carRect = rotatedCar.get_rect()
                carRect.center = (WINMIDX + x, WINMIDY + y)
                surf.blit(rotatedCar, carRect)
                nameSurf = font.render(name, True, NAMECOLOR)
                nameRect = nameSurf.get_rect()
                nameRect.center = (WINMIDX + x, WINMIDY + y - 40)
                # FIXME: 这里还有点问题，先去掉
                # surf.fill(NAMEBG, nameRect)
                surf.blit(nameSurf, nameRect)
            pygame.display.update()
            clock.tick(FPS)
        pygame.quit()

    def stop(self):
        '''
        结束游戏，使show调用返回
        '''
        self.running = False


def nop():
    pass

l = [['P1', 0, 500, 10, 250, 20, 100], ['玩家2', 0, 500, 5, 250, 7, 0]]

def gd():
    return l

def update():
    t = time.time() - display.startTime
    for i in l:
        dt = t - i[1]
        i[2] += i[3] * dt
        i[4] += i[5] * dt
        i[1] = t

def up():
    update()
    l[0][3] -= 2 * math.sin(math.radians(l[0][6]))
    l[0][5] -= 2 * math.cos(math.radians(l[0][6]))

def down():
    update()
    l[0][3] += 2 * math.sin(math.radians(l[0][6]))
    l[0][5] += 2 * math.cos(math.radians(l[0][6]))

def left():
    update()
    l[0][6] += 20

def right():
    update()
    l[0][6] -= 20

display = Display(time.time() + 4, gd, up, nop, down, nop, left, nop, right, nop)
display.show()
