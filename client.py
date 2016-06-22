#! /usr/bin/python3
# coding=utf-8

import socket
import threading
import game


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
            game_client.display.startTime = float(request_message)

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
            self.display = game.dummy_display(self)
            self.display.show()
        finally:
            sock.close()


if __name__ == "__main__":
    GameClient("127.0.0.1", 23345).run()
