import socket
import socketserver
import game
import math
import time
import threading
import struct
import base64


class ServerPacketLogout():
    def handle_message(self, request_message, client_address, game_server):
        if client_address in game_server.map.player_data.keys():
            game_server.map.players.remove(game_server.map.player_data[client_address].name)
            game_server.map.player_data.pop(client_address)
            return "Bye. "
        return None


class ServerPacketControl():
    def handle_message(self, request_message, client_address, game_server):
        message = base64.b64decode(request_message[:16:])
        if client_address in game_server.map.player_data.keys():
            timestamp, speed, rotation = struct.unpack("3f", message)
            player_data = game_server.map.player_data[client_address]
            player_data.time = timestamp
            player_data.speed = speed
            player_data.rotation = rotation
            player_data.update_tick(game_server.map.last_tick)
            return game_server.map.write_player_data(game_server.map.player_data)
        else:
            return None


class ServerPacketLogin():
    def handle_message(self, request_message, client_address, game_server):
        name = request_message[:16:]
        if name in game_server.map.players:
            return ''
        else:
            game_server.map.player_data[client_address] = PlayerDataServer(name, client_address)
            game_server.map.players.append(name)
            return game_server.map.write_player_data(game_server.map.player_data)


class GameServer():
    '''
    Three Steps:

            Client: send_message
    Client ------------------------> Server

            Server: handle_message
    Server ------------------------> Server

            Client: receive_message
    Server ------------------------> Client
    '''

    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 23345
        self.map = RaceMap(self)

    def create_handler(self, request, client_address, server):
        handler = GameServer.Handler(request, client_address, server, self)

    def run(self):
        self.socket = socketserver.ThreadingTCPServer((self.host, self.port), self.create_handler)
        threading.Thread(target=self.socket.serve_forever).start()
        time.sleep(10)
        self.stop()

    def stop(self):
        self.socket.shutdown()

    class Handler(socketserver.BaseRequestHandler):
        packet_types = {'L': ServerPacketLogin, 'C': ServerPacketControl, 'E': ServerPacketLogout}

        def __init__(self, request, client_address, server, game_server):
            self.game_server = game_server
            super().__init__(request, client_address, server)

        def handle(self):
            message_pool = ""
            while 1:
                message = str(self.request.recv(128), "utf-8")

                if not message: break
                message_pool += message

                if '\n' not in message_pool: continue
                index = message_pool.index('\n')
                message = message_pool[:index:]
                message_pool = message_pool[index + 1::]

                print("(Client)", repr(self.client_address), message)
                packet_handler = self.packet_types[message[0]]()
                new_message = packet_handler.handle_message(message[2::], self.client_address, self.game_server)
                if (new_message is None): break
                else:
                    print("(Server)", repr(self.server.server_address), message[0] + message[1] + new_message)
                    self.request.sendall(bytes(message[0] + message[1] + new_message, "utf-8"))


class PlayerDataServer(game.PlayerData):
    def __init__(self, name, client_address):
        self.client_address = client_address
        super().__init__(name)


class RaceMap():
    def __init__(self, game_server):
        self.player_data = {}
        self.players = []
        self.game_server = game_server
        self.start_time = time.time() - 4
        self.running = True
        self.game_started = False

    def write_player_data(self, data):
        message = ''
        for player_data in data.values():
            packed_data = struct.pack('3f', player_data.speed, player_data.rotation, player_data.time)
            message += str(base64.b64encode(packed_data), "utf-8")
            message += player_data.name
            message += '\x00'
        return message

    def tick_player(self, t):
        '''
        玩家逻辑
        '''
        for player_data in self.player_data.values():
            player_data.update_tick(t)

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
        '''
        循环显示游戏界面

        此函数直到stop被调用后才会返回
        '''
        while self.running:
            self.tick(time.time() - self.startTime)
            time.sleep(game.FPS - time.time() % game.FPS)
        self.game_server.stop()

    def tick(self, t):
        '''
        Game loop
        '''
        if len(self.player_data) > 0:
            self.game_started = True
            # tick player
            self.tick_player(t)
        elif self.game_started:
            self.running = False
        self.last_tick = t


GameServer().run()
