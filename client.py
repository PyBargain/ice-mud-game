#! /usr/bin/python3
# coding=utf-8

import base64
import struct
import random
import socket
import threading
import time
import pygame
import select

from game import *


class GameClient:
    """
    Three Steps:

            Client: send_packet
    Client ------------------------> Server

            Server: handle_message
    Server ------------------------> Server

            Client: receive_message
    Server ------------------------> Client
    """

    class ClientPacketLogout:
        @staticmethod
        def receive_message(request_message, client_address, game_client):
            pass

    class ClientPacketControl:
        @staticmethod
        def receive_message(request_message, client_address, game_client):
            game_client.display.read_player_data(game_client.display.player_data, request_message)

    class ClientPacketLogin:
        @staticmethod
        def receive_message(request_message, server_address, game_client):
            game_client.display.start_time = float(request_message)

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def send_packet(self, message):
        print("(Client)", self.socket.getsockname(), message)
        self.socket.sendall(bytes(message + '\n', "utf-8"))

    def run(self):
        self.socket = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        packet_types = {'L': self.ClientPacketLogin,
                        'C': self.ClientPacketControl,
                        'E': self.ClientPacketLogout}

        def run_socket(game_client):
            message_pool = ""
            while 1:
                message = str(game_client.socket.recv(128), "utf-8")

                if not message: break
                message_pool += message

                if '\n' not in message_pool: continue
                index = message_pool.index('\n')
                message = message_pool[:index:]
                message_pool = message_pool[index + 1::]

                address = (game_client.host, game_client.port)
                print("(Server)", repr(address), message)
                packet_types[message[0]].receive_message(message[2::], address, game_client)

        try:
            sock.connect((self.host, self.port))
            threading.Thread(target=run_socket, args=(self,)).start()
            self.display = Display(time.time() - 4, KeyBinding(), self)
            self.display.show()
        finally:
            sock.close()


class Display:
    """
    负责客户端逻辑
    """
    def __init__(self, start_time, key_binding, game_server):
        """
        产生一个display对象

        参数：
            start_time      游戏时间为0时的UNIX时间戳
        """
        self.start_time = start_time
        self.key_binding = key_binding

        pygame.init()
        self.surf = pygame.display.set_mode((Constants.WINDOW_WIDTH, Constants.WINDOW_HEIGHT))
        pygame.display.set_caption('Ice Mud Game')
        self.game_server = game_server
        self.last_tick = time.time() - self.start_time
        self.running = True
        self.state_changed = True
        self.theme_index = 0
        self.theme = "normal"

        self.map_data_image = pygame.image.load('map_data.png')
        self.map_width = self.map_data_image.get_width()
        self.map_height = self.map_data_image.get_height()
        self.map_data = MapData.get_map_data(self.map_data_image)

        self.player_data = [PlayerData("Player" + str(random.randrange(1000, 10000))), PlayerData('玩家2')]
        self.current_player = self.player_data[0]

    def handle_key(self, time):
        """
        响应键盘事件
        """
        for event in pygame.event.get():
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE: self.stop()
        self.state_changed = self.key_binding.update(lambda key: pygame.key.get_pressed()[key], time, self)

    def send_changes(self):
        if self.state_changed:
            packed = struct.pack('3f', self.current_player.time, self.current_player.speed,
                                 self.current_player.rotation)
            self.game_server.send_packet("C:" + str(base64.b64encode(packed), "utf-8"))

    def calculate_offset(self, pos_x, pos_y):
        x = min(max(Constants.WIN_MIDDLE_X - self.current_player.pos_x, Constants.WINDOW_WIDTH - self.map_width),
                0) + pos_x
        y = min(max(Constants.WIN_MIDDLE_Y - self.current_player.pos_y, Constants.WINDOW_HEIGHT - self.map_height),
                0) + pos_y
        return (x, y)

    def draw_map(self, player_data):
        """
        背景图
        """
        mapImage = pygame.image.load(self.theme + '/map.png').convert(32, pygame.SRCALPHA)
        mapRect = mapImage.get_rect()
        mapRect.topleft = self.calculate_offset(0, 0)
        self.surf.blit(mapImage, mapRect)

    def draw_car(self, player_data):
        """
        快上车
        """
        carImagePath = self.theme + ('/mycar.png' if player_data.name is self.current_player.name else "/car.png")
        carImage = pygame.image.load(carImagePath).convert(32, pygame.SRCALPHA)
        rotatedCar = pygame.transform.rotate(carImage, -player_data.rotation * 180 / math.pi)
        carRect = rotatedCar.get_rect()
        carRect.center = self.calculate_offset(player_data.pos_x, player_data.pos_y)
        self.surf.blit(rotatedCar, carRect)
        font = pygame.font.Font('font/wqy-microhei.ttc', 18)
        nameSurf = font.render(player_data.name, True, Constants.NAME_COLOR)
        nameRect = nameSurf.get_rect()
        nameRect.center = self.calculate_offset(player_data.pos_x, player_data.pos_y - 48)
        # FIXME: 这里还有点问题，先去掉  还是先开着吧
        surf.fill(NAMEBG, nameRect)
        self.surf.blit(nameSurf, nameRect)

    def draw_building(self, player_data):
        """
        建筑物
        """
        # TODO: Your work, FasdSnake
        # 因为某些原因弃坑
        pass

    def draw_cars(self):
        """
        所有的车
        """
        for player_data in self.player_data:
            if (player_data.name != self.current_player.name):
                self.draw_car(player_data)
        self.draw_car(self.current_player)

    def tick_player(self, t):
        """
        玩家逻辑
        """
        for player_data in self.player_data:
            player_data.update_tick(t, self.map_data)

    def tick(self, t):
        """
        Game loop
        """
        # check server
        if select.select([], [], [], 0)[0]:
            pass
        # key events
        self.handle_key(t)
        # tick player
        self.tick_player(t)
        self.send_changes()
        # draw
        self.draw_map(self.current_player)
        self.draw_building(self.current_player)
        self.draw_cars()
        # update
        pygame.display.update()
        self.last_tick = t

    def show(self):
        """
        循环显示游戏界面

        此函数直到stop被调用后才会返回
        """
        clock = pygame.time.Clock()
        self.game_server.send_packet('L:' + self.current_player.name)
        self.send_changes()
        while self.running:
            self.tick(time.time() - self.start_time)
            clock.tick(Constants.FPS)
        pygame.quit()

    def stop(self):
        """
        结束游戏，使show调用返回
        """
        self.game_server.send_packet('E:')
        self.running = False
        self.game_server.socket.close()

    def read_player_data(self, data, message):
        try:
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
                    player.update_tick(self.last_tick, self.map_data)
                    data_dict.pop(player.name)
                else:
                    data.remove(player)
            for name, packed in data_dict.items():
                player = PlayerData(name)
                pos_x, pos_y, player.speed, player.rotation, player.time = struct.unpack('5f', base64.b64decode(packed))
                player.pos_x = pos_x
                player.pos_y = pos_y
                player.update_tick(self.last_tick, self.map_data)
                data.append(player)
        except:
            pass


class KeyBinding:
    def __init__(self):
        self.counter = 3
        self.themes = ["normal", "simple", "excited"]
        self.theme_changed = True

    def update(self, is_key_pressed, time, display):
        """
        用于每次更新时触发，返回此次触发是否引起客户端和服务端同步
        is_key_pressed      一个函数指针，传入键对应的ascii码，返回这个键是否被按下
        time                当前时间
        display             一个负责客户端的Display对象
        """
        if (is_key_pressed(pygame.K_e)):
            if self.theme_changed:
                display.theme_index = (display.theme_index + 1) % len(self.themes)
                display.theme = self.themes[display.theme_index]
                self.theme_changed = False
        elif not self.theme_changed:
            self.theme_changed = True

        flag = False
        if (is_key_pressed(pygame.K_UP)):
            self._up(display, time)
            flag = True
        if (is_key_pressed(pygame.K_DOWN)):
            self._down(display, time)
            flag = True
        if (is_key_pressed(pygame.K_LEFT)):
            self._left(display, time)
            flag = True
        if (is_key_pressed(pygame.K_RIGHT)):
            self._right(display, time)
            flag = True
        if self.counter >= 3:
            self.counter = 0
            return flag
        else:
            self.counter += 1
            return False

    def _up(self, display, time):
        dv = (time - display.last_tick) * ((2048 - display.current_player.speed) / 16 + 64 * random.random())
        display.current_player.speed += dv

    def _down(self, display, time):
        dv = (time - display.last_tick) * ((2048 + display.current_player.speed) / 16 + 64 * random.random())
        display.current_player.speed -= dv

    def _left(self, display, time):
        display.current_player.rotation -= (time - display.last_tick) * 0.5

    def _right(self, display, time):
        display.current_player.rotation += (time - display.last_tick) * 0.5


if __name__ == "__main__":
    GameClient("127.0.0.1", 23345).run()
