#! /usr/bin/python3
# coding=utf-8

import socket
import asyncore
import threading
import base64
import struct
import time
import pygame

from game import *


class GameServer(asyncore.dispatcher):
    """
    Three Steps:

            Client: send_packet
    Client ------------------------> Server

            Server: handle_message
    Server ------------------------> Server

            Client: receive_message
    Server ------------------------> Client
    """
    class PlayerDataServer(PlayerData):
        def __init__(self, name, client_address):
            self.client_address = client_address
            super().__init__(name)

    class ServerPacketLogout:
        @staticmethod
        def handle_message(request_message, client_address, game_server):
            if client_address in game_server.map.player_data.keys():
                game_server.map.players.remove(game_server.map.player_data[client_address].name)
                game_server.map.player_data.pop(client_address)
                game_server.remove_client(client_address)
            return []

    class ServerPacketControl:
        @staticmethod
        def handle_message(request_message, client_address, game_server):
            message = base64.b64decode(request_message[:16:])
            if client_address in game_server.map.player_data.keys():
                timestamp, speed, rotation = struct.unpack("3f", message)
                player_data = game_server.map.player_data[client_address]
                player_data.time = timestamp
                player_data.speed = speed
                player_data.rotation = rotation
                return [game_server.map.write_player_data(game_server.map.player_data)]
            else:
                return []

    class ServerPacketLogin:
        @staticmethod
        def handle_message(request_message, client_address, game_server):
            name = request_message[:16:]
            if name in game_server.map.players:
                return ['']
            else:
                game_server.map.player_data[client_address] = GameServer.PlayerDataServer(name, client_address)
                game_server.map.players.append(name)
                return [str(game_server.map.start_time)]

    class RemoteClient(asyncore.dispatcher):

        def __init__(self, host, socket, address):
            asyncore.dispatcher.__init__(self, socket)
            self.host = host
            self.address = address
            self.outbox = []

        def say(self, message):
            self.outbox.append(message)

        def handle_read(self):
            client_message = self.recv(1024).strip()
            self.host.broadcast(client_message, self.address)

        def handle_write(self):
            for message in self.outbox: self.send(message)
            self.outbox.clear()

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = (host, port)
        self.bind(self.address)
        self.listen(1)
        self.remote_clients = {}
        self.map = RaceMap(self)
        self.network_loop = threading.Thread(target = (lambda: asyncore.loop(timeout = 3)))
        self.packet_types = {'L': self.ServerPacketLogin,
                             'C': self.ServerPacketControl,
                             'E': self.ServerPacketLogout}

    def run(self):
        print("Starting server... ")
        self.network_loop.start()
        self.map.run()
        print("Stopping server... ")
        self.close()
        self.network_loop.join()

    def remove_client(self, address):
        if address in self.remote_clients.keys():
            print("(Closed)", address)
            self.remote_clients.pop(address).close()

    def handle_accept(self):
        socket, address = self.accept()
        self.remote_clients[address] = self.RemoteClient(self, socket, address)

    def broadcast(self, message, address):
        client_message = str(message, "utf-8")
        print("(Client)", repr(address), client_message)
        packet_handler = self.packet_types[client_message[0]]
        new_messages = packet_handler.handle_message(client_message[2::], address, self)
        for new_message in new_messages:
            server_message = client_message[0] + client_message[1] + new_message
            print("(Server)", repr(self.address), server_message)
            for remote_client in self.remote_clients.values():
                remote_client.say(bytes(server_message + '\n', "utf-8"))


class RaceMap:
    """
    负责服务端逻辑
    """

    def __init__(self, game_server):
        self.player_data = {}
        self.players = []
        self.game_server = game_server
        self.start_time = time.time() - 4
        self.running = True
        self.game_started = False
        self.map_data = MapData.get_map_data(pygame.image.load('map_data.png'))

    def write_player_data(self, data):
        message = ''
        for player_data in data.values():
            packed_data = struct.pack('5f',
                                      player_data.pos_x, player_data.pos_y, player_data.speed,
                                      player_data.rotation, player_data.time)
            message += str(base64.b64encode(packed_data), "utf-8")
            message += player_data.name
            message += '\x00'
        return message

    def tick_player(self, t):
        """
        玩家逻辑
        """
        for player_data in self.player_data.values():
            player_data.update_tick(t, self.map_data)

    def handle_key(self):
        pass

    def receive_packets(self):
        packets = self.game_server.packets
        for type, bytes in packets:
            if type == 'L':
                pass

    def send_packets(self):
        pass

    def run(self):
        """
        循环显示游戏界面
        """
        while self.running:
            self.tick(time.time() - self.start_time)
            time.sleep((1.0 / Constants.FPS) - time.time() % (1.0 / Constants.FPS))

    def tick(self, t):
        """
        Game loop
        """
        if len(self.player_data) > 0:
            self.game_started = True
            # tick player
            self.tick_player(t)
        elif self.game_started:
            self.running = False
        self.last_tick = t


if __name__ == "__main__":
    GameServer("127.0.0.1", 23345).run()
