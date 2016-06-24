#!/usr/bin/python3
# encoding=utf-8


import math, time

from socket import socket
from select import select

import pygame
from pygame.locals import *


WINDOWWIDTH = 1280
WINDOWHEIGHT = 720
WINMIDX = WINDOWWIDTH / 2
WINMIDY = WINDOWHEIGHT / 2
NAMECOLOR = (255, 255, 255)
NAMEBG = (64, 64, 64)
FPS = 60


INPUT_KEYS = {K_BACKSPACE, K_RETURN}
CHAR_KEYS = list(range(ord('0'), ord('9')+1)) + list(range(ord('a'), ord('z')+1)) + [K_SPACE]


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
        self.excited = False

    def show(self):
        '''
        循环显示游戏界面

        此函数直到stop被调用后才会返回
        '''
        global c_socket, Name, winner
        pygame.init()
        clock = pygame.time.Clock()
        surf = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), FULLSCREEN)
        # 路径'C:\\WINDOWS\\Fonts\\STSONG.TTF'已弃用
        font = pygame.font.Font('font/wqy-microhei.ttc', 18)
        bigfont = pygame.font.Font('font/wqy-microhei.ttc', 72)
        mapImageNormal = pygame.image.load('map.png').convert(32, SRCALPHA)
        mapImageExcited = pygame.image.load('map_excited.png').convert(32, SRCALPHA)
        mapImage = mapImageNormal
        mapRect = mapImage.get_rect()
        carImageNormal = pygame.image.load('car.png').convert(32, SRCALPHA)
        carImageExcited = pygame.image.load('car_excited.png').convert(32, SRCALPHA)
        carImage = carImageNormal
        corner = carImage.get_at((0, 0))
        for x in range(carImage.get_width()):
            for y in range(carImage.get_height()):
                if carImage.get_at((x, y)) == corner:
                    carImage.set_at((x, y), (0, 0, 0, 0))
        pygame.display.set_caption('Ice Mud Game')
        winner = ''
        # title1
        img = pygame.image.load('title1.png')
        imgrect = img.get_rect()
        name = ''
        inputing = True
        while self.running and inputing:
            for event in pygame.event.get():
                if event.type == KEYUP:
                    if event.key in CHAR_KEYS:
                        name += chr(event.key)
                    elif event.key == K_BACKSPACE:
                        if name:
                            name = name[:-1]
                    elif event.key == K_RETURN:
                        inputing = False
                    elif event.key == K_ESCAPE:
                        self.stop()
            surf.blit(img, imgrect)
            text = font.render(name, True, (0, 0, 0))
            rect = text.get_rect()
            rect.bottomleft = (597, 535)
            surf.blit(text, rect)
            pygame.display.update()
            clock.tick(FPS)
        Name = name
        # title2
        img = pygame.image.load('title2.png')
        imgrect = img.get_rect()
        key = ''
        inputing = True
        while self.running and inputing:
            for event in pygame.event.get():
                if event.type == KEYUP:
                    if event.key in CHAR_KEYS:
                        key += chr(event.key)
                    elif event.key == K_BACKSPACE:
                        if key:
                            key = key[:-1]
                    elif event.key == K_RETURN:
                        inputing = False
                    elif event.key == K_ESCAPE:
                        self.stop()
            surf.blit(img, imgrect)
            text = font.render('*'*len(key), True, (0, 0, 0))
            rect = text.get_rect()
            rect.bottomleft = (597, 569)
            surf.blit(text, rect)
            pygame.display.update()
            clock.tick(FPS)
        # title3
        if self.running:
            c_socket = socket()
            self.c_socket = c_socket
            c_socket.connect(CADDR)
            c_socket.send(b'N'+name.encode()+b'\n')
            c_socket.send(b'S'+key.encode()+b'\n')
        img = pygame.image.load('title3.png')
        imgrect = img.get_rect()
        name = ''
        inputing = True
        player_count = 0
        while self.running and inputing:
            for event in pygame.event.get():
                if event.type == KEYUP:
                    if event.key == K_ESCAPE:
                        self.stop()
            if select([c_socket], [], [], 0)[0]:
                s = b''
                while True:
                    s += c_socket.recv(1)
                    if s[-1] == ord('\n'):
                        break
                s = s.decode()
                if s[0] == 'T':
                    self.startTime = eval(s[1:])
                elif s[0] == 'C':
                    player_count = eval(s[1:])
                elif s[0] == '[':
                    inputing = False
            surf.blit(img, imgrect)
            text = font.render(str(int(self.startTime - 4 - time.time())), True, (0, 0, 0))
            rect = text.get_rect()
            rect.center = (817, 404)
            surf.blit(text, rect)
            text = font.render(str(player_count), True, (0, 0, 0))
            rect = text.get_rect()
            rect.midleft = (705, 463)
            surf.blit(text, rect)
            pygame.display.update()
            clock.tick(FPS)
        # 正式运行
        lastt = 0
        while self.running and winner == '':
            t = time.time() - self.startTime
            for event in pygame.event.get():
                if event.type == KEYUP:
                    if event.key in self.onKeyUp:
                        self.onKeyUp[event.key]()
                    if event.key == K_ESCAPE:
                        self.stop()
                if event.type == KEYDOWN:
                    if event.key == K_e:
                        if self.excited:
                            carImage = carImageNormal
                            mapImage = mapImageNormal
                            self.excited = False
                        else:
                            carImage = carImageExcited
                            mapImage = mapImageExcited
                            self.excited = True
                    if event.key in self.onKeyDown:
                        self.onKeyDown[event.key]()
            data = self.getData()
            name, t0, x, dx, y, dy, drct = data[0]
            dt = t - t0
            cx = x + dt * dx
            cy = y + dt * dy
            surf.fill((0, 0, 0))
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
                # FIXME: 这里还有点问题
                surf.fill(NAMEBG, nameRect)
                surf.blit(nameSurf, nameRect)
            # draw text
            tt = time.time()
            if tt - 1 < self.startTime:
                if tt + 3 < self.startTime: s = 'READY?'
                elif tt + 2 < self.startTime: s = '3'
                elif tt + 1 < self.startTime: s = '2'
                elif tt < self.startTime: s = '1'
                else: s = 'GO!'
                text = bigfont.render(s, True, (64, 64, 64))
                rect = text.get_rect()
                rect.center = (645, 185)
                surf.blit(text, rect)
                text = bigfont.render(s, True, (255, 255, 255))
                rect = text.get_rect()
                rect.center = (640, 180)
                surf.blit(text, rect)
            text = font.render(str(clock.get_fps()), True, (255, 255, 255))
            rect = text.get_rect()
            rect.topleft = (0, 0)
            surf.blit(text, rect)
            text = font.render('%02d:%02d'%(abs(t)//60, abs(t)%60), True, (255, 255, 255))
            rect = text.get_rect()
            rect.topright = (1280, 0)
            surf.blit(text, rect)
            text = font.render(str(int(10*math.sqrt(dx*dx+dy*dy)))+' MPH', True, (255, 255, 255))
            rect = text.get_rect()
            rect.bottomright = (1280, 720)
            surf.blit(text, rect)
            pygame.display.update()
            clock.tick(FPS)
        # end
        while self.running:
            for event in pygame.event.get():
                if event.type == KEYUP:
                    if event.key in (K_RETURN, K_ESCAPE):
                        self.stop()
            text = bigfont.render(winner + '是胜利者！', True, (64, 64, 64))
            rect = text.get_rect()
            rect.center = (645, 185)
            surf.blit(text, rect)
            text = bigfont.render(winner + '是胜利者！', True, (255, 255, 255))
            rect = text.get_rect()
            rect.center = (640, 180)
            surf.blit(text, rect)
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
    global l, winner
    if select([c_socket], [], [], 0)[0]:
        s = b''
        while True:
            s += c_socket.recv(1)
            if s[-1] == ord('\n'):
                break
        if s[0] == ord('W'):
            winner = s[1:-1].decode()
            return l
        l = eval(s.decode())
    self = l[0]
    for i in l:
        if i[0] == Name:
            self = i
            break
    l.remove(self)
    l.insert(0, self)
    return l


def upd():
    c_socket.send(b'KU\n')

def upu():
    c_socket.send(b'Ku\n')

def downd():
    c_socket.send(b'KD\n')

def downu():
    c_socket.send(b'Kd\n')

def leftd():
    c_socket.send(b'KL\n')

def leftu():
    c_socket.send(b'Kl\n')

def rightd():
    c_socket.send(b'KR\n')

def rightu():
    c_socket.send(b'Kr\n')


with open('config.txt') as f:
    CADDR = eval(f.read())


display = Display(time.time() + 4, gd, upd, upu, downd, downu, leftd, leftu, rightd, rightu)
display.show()
