#!/usr/bin/python3
# encoding=utf-8


import time

from socket import socket
from select import select

from hashlib import sha1

import pygame
from pygame.locals import *


from game import Player, Game


TICKET_SHA1SUM = '9dfc9983c4dc37d280f3628815a832a47d3f70c4'


'''
客户端发往服务器端的消息前缀：
    N 设置昵称
    S 验证身份特权
    K 按键事件
服务器端发往客户端的消息前缀：
    T startTime
    C 当前在线人数
    [ 数据
'''


class Server:
    def __init__(self, saddr):
        self.s_socket = socket()
        self.s_socket.bind(('127.0.0.1', 10667))
    def start(self):
        self.s_socket.listen(2)
        self.cs_socket = [self.s_socket.accept()[0]]
        self.players = [Player()]
        self.startTime = time.time() + 10
        stopAcceptTime = self.startTime - 5
        print('收到第一个连接，等待5秒其他玩家')
        self.cs_socket[-1].send(('T%r\n'%self.startTime).encode())
        self.s_socket.settimeout(0.01)
        while time.time() < stopAcceptTime:
            try:
                self.cs_socket.append(self.s_socket.accept()[0])
                self.players.append(Player())
                self.cs_socket[-1].send(('T%r\n'%self.startTime).encode())
                for c_socket in self.cs_socket:
                    c_socket.send(('C%r\n'%len(self.cs_socket)).encode())
            except: pass
            self.checkNet()
        self.s_socket.settimeout(None)
        print('5秒后开始游戏')
        self.game = Game(self.players, self.startTime)
        state = repr(self.game.getState()).encode() + b'\n'
        for c_socket in self.cs_socket:
            c_socket.send(state)
            c_socket.send(state) # XXX: 因为客户端会丢掉收到的第一条消息
        time.sleep(self.startTime - time.time())
        while True:
            self.game.tick()
            self.checkNet()
            state = repr(self.game.getState()).encode() + b'\n'
            for c_socket in self.cs_socket:
                c_socket.send(state)
            time.sleep(1/10)
    def close(self):
        self.s_socket.close()
    def checkNet(self):
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
            elif s[0] == 'S':
                if sha1(s[1:-1].encode()).hexdigest() == TICKET_SHA1SUM:
                    self.players[self.cs_socket.index(c_socket)].isPayed = True

try:
    server = Server(('127.0.0.1', 10667))
    server.start()
finally:
    server.close()
