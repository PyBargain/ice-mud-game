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
        self.side, self.top = BUILDINGIMG[image]
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
            return (x/y if y > x else 2 - y/x, x*x + y*y)
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
                top = (i-left)*(rtop-ltop)//width+ltop
                bottom = (i-left)*(rbottom-lbottom)//width+lbottom
                display.blit(pygame.transform.rotate(self.side, 90),
                        Rect(i, top, 1, bottom - top),
                        Rect((i-left)*self.side.height//width, 0, (self.side.height+width-1)//width, self.side.width))
        elif x < rect.left:
            # 画右侧面
        if y > rect.bottom:
            # 画上侧面
        elif y < rect.top:
            # 画下侧面
        # 画顶面
        display.blit(self.top, toprect)


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
            pass  # TODO
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
