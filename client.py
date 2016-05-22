import socket, threading


class GameClient():
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 23345

    def run(self, string):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))

        for i in range(5):
            sock.sendall(bytes('L:' + string + '\n', "utf-8"))
            print(string, i, repr(sock.recv(1024)))

        sock.sendall(bytes('E:\n', "utf-8"))
        print(repr(sock.recv(1024)))
        sock.close()


gc = GameClient()
threading.Thread(target=gc.run, args=("test1",)).start()
threading.Thread(target=gc.run, args=("测试2",)).start()
threading.Thread(target=gc.run, args=("test3",)).start()
threading.Thread(target=gc.run, args=("测试4",)).start()
threading.Thread(target=gc.run, args=("test5",)).start()
