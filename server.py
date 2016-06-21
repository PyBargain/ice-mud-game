#! /usr/bin/python3
# coding=utf-8

import socketserver
import threading
import base64
import struct
import time
import game


class GameServer:
    """
    Three Steps:

            Client: send_packet
    Client ------------------------> Server

            Server: handle_message
    Server ------------------------> Server

            Client: receive_message
    Server ------------------------> Client
    """

    class ServerPacketLogout:
        @staticmethod
        def handle_message(request_message, client_address, game_server):
            if client_address in game_server.map.player_data.keys():
                game_server.map.players.remove(game_server.map.player_data[client_address].name)
                game_server.map.player_data.pop(client_address)
            return None

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
                return game_server.map.write_player_data(game_server.map.player_data)
            else:
                return None

    class ServerPacketLogin:
        @staticmethod
        def handle_message(request_message, client_address, game_server):
            name = request_message[:16:]
            if name in game_server.map.players:
                return ''
            else:
                game_server.map.player_data[client_address] = PlayerDataServer(name, client_address)
                game_server.map.players.append(name)
                return str(game_server.map.start_time)

    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 23344
        self.map = RaceMap(self)
        self.packet_types = {'L': self.ServerPacketLogin,
                             'C': self.ServerPacketControl,
                             'E': self.ServerPacketLogout}
        self.socket = None

    def create_handler(self, request, client_address, server):
        return GameServer.Handler(request, client_address, server, self)

    def run(self):
        self.socket = socketserver.ThreadingTCPServer((self.host, self.port), self.create_handler)
        print("Starting server... ")
        threading.Thread(target=self.socket.serve_forever).start()
        self.map.run()
        print("Stopping server... ")
        self.socket.shutdown()

    def stop(self):
        self.socket.shutdown()

    class Handler(socketserver.StreamRequestHandler):

        def __init__(self, request, client_address, server, game_server):
            self.game_server = game_server
            super().__init__(request, client_address, server)

        def handle(self):
            while self.game_server.map.running:
                message = str(self.rfile.readline().strip(), "utf-8")

                print("(Client)", repr(self.client_address), message)

                try:
                    packet_handler = self.game_server.packet_types[message[0]]
                    new_message = packet_handler.handle_message(message[2::], self.client_address, self.game_server)
                except:
                    pass

                if new_message is None:
                    break
                else:
                    print("(Server)", repr(self.server.server_address), message[0] + message[1] + new_message)
                    self.wfile.write(bytes(message[0] + message[1] + new_message + '\n', "utf-8"))
            print("(Closed)", self.client_address)


class PlayerDataServer(game.PlayerData):
    def __init__(self, name, client_address):
        self.client_address = client_address
        super().__init__(name)


class RaceMap:
    def __init__(self, game_server):
        self.player_data = {}
        self.players = []
        self.game_server = game_server
        self.start_time = time.time() - 4
        self.running = True
        self.game_started = False
        self.map_data = []

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
            player_data.update_tick(t)
            # player_data.check_collision(t) #碰撞判断

    def get_map_data(self, map_data):  # 这个函数在game.py 里调用
        # TODO：->_->讲道理我现在不知道怎么拿到map，我希望的map格式在game.py里有写
        pass

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
            time.sleep((1.0 / game.FPS) - time.time() % (1.0 / game.FPS))

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
    GameServer().run()
