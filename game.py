#!/usr/bin/python3
# encoding=utf8


import math, time


class Player:
    def __init__(self):
        self.kUp = False
        self.kDown = False
        self.kLeft = False
        self.kRight = False
        self.name = 'Player'
        self.t = 0
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.d = 0

    def tick(self, t):
        dt = t - self.t
        self.x += self.vx * dt
        self.y += self.vy * dt
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


class Game:
    def __init__(self, players, startTime):
        self.players = players
        self.startTime = startTime

    def tick(self):
        for p in self.players:
            p.tick(time.time() - self.startTime)

    def getState(self):
        retval = []
        for p in self.players:
            retval.append([p.name, p.t, p.x, p.vx, p.y, p.vy, p.d])
        return retval
