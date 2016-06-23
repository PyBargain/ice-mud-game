#!/usr/bin/python3
# encoding=utf-8


import time

from socket import socket
from select import select

import pygame
from pygame.locals import *


from game import Player, Game


class Server:
    def __init__(self, saddr):
        self.s_socket = socket()
        self.s_socket.bind(('127.0.0.1', 10667))
    def start(self):
        self.s_socket.listen(2)
        self.cs_socket = [self.s_socket.accept()[0]]
        self.startTime = time.time() + 10
        stopAcceptTime = self.startTime - 5
        print('收到第一个连接，等待5秒其他玩家')
        while time.time() < stopAcceptTime:
            self.s_socket.settimeout(stopAcceptTime - time.time())
            try: self.cs_socket.append(self.s_socket.accept()[0])
            except: pass
        self.s_socket.settimeout(None)
        print('5秒后开始游戏')
        self.players = []
        for _ in self.cs_socket:
            self.players.append(Player())
        self.game = Game(self.players, self.startTime)
        state = repr(self.game.getState()).encode() + b'\n'
        for c_socket in self.cs_socket:
            c_socket.send(state)
        time.sleep(self.startTime - time.time())
        while True:
            self.game.tick()
            for c_socket in select(self.cs_socket, [], [], 0)[0]:
                s = b''
                while True:
                    s += c_socket.recv(1)
                    if s[-1] == ord('\n'):
                        break
                s = s.decode()
                if s[0] == 'K':
                    print(repr(s))
                    self.players[self.cs_socket.index(c_socket)].keyEvent(s[1])
                elif s[0] == 'N':
                    self.players[self.cs_socket.index(c_socket)].setName(s[1:-1])
            state = repr(self.game.getState()).encode() + b'\n'
            for c_socket in self.cs_socket:
                c_socket.send(state)
            time.sleep(1/10)
    def close(self):
        self.s_socket.close()


try:
    server = Server(('127.0.0.1', 10667))
    server.start()
finally:
    server.close()
