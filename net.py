#  net, short for networking
import socket
import threading
import pygame.constants
import math
import time


# packets:
# first letter type, information/action
# second letter data

# IN:
# name

# IB:
# x y type

# AK:
# wasd changed
# 0000 binary for wasd

# AQ:
# quit

# EN:
# name contains space


class player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.xv = 0
        self.yv = 0

        self.queue = []  # placing/breaking blocks
        self.key = [False, False, False, False]  # up, left, down, right

    def physics(self, world):
        if self.key[3]:
            self.xv += .1
        if self.key[1]:
            self.xv -= .1

        self.yv += .1
        self.y += self.yv

        floor = False
        while world.get(math.floor(self.x), math.ceil(self.y)).solid or\
                world.get(math.ceil(self.x), math.ceil(self.y)).solid:
            self.yv = 0
            self.y -= .1
            floor = True

        if floor and self.key[0]:
            self.yv = -.55

        self.x += self.xv
        self.xv /= 2


class server:
    def __init__(self, ip='localhost'):
        self.threads = []
        self.run = True

        self.players = []

        self.ip = ip
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(.5)
        self.server.bind((ip, 60000))
        self.server.listen()

        self.accept_thread = threading.Thread(target=self._accept, name='accept')
        self.accept_thread.start()
        self.threads.append(self.accept_thread)

    def _accept(self):
        while self.run:
            try:
                c, address = self.server.accept()
                print('accepted', c, address)
                p = player()
                self.players.append(p)
                self.threads.append(threading.Thread(target=server_client, args=[c, self, p]))
                self.threads[-1].start()
            except socket.timeout:
                pass

    def update(self, world):
        for p in self.players:
            p.physics(world)

    def exit(self):
        self.run = False
        for t in self.threads:
            print('joining', t)
            t.join(1)
            if t.is_alive():
                print(t, 'is still alive')

    def remove(self, s_c):
        self.players.remove(s_c.player)


class server_client:
    def __init__(self, c: socket.socket, s: server, p: player):
        self.c = c
        self.s = s
        self.r = True
        self.name = 'error0'
        self.player = p

        self.c.settimeout(.02)
        self.run()

    def packet_recv(self, packet):
        data = packet.decode('utf-8')
        print("client: '" + self.name + "' packet: '" + data + "'")
        if data[0] == 'I':
            if data[1] == 'N':
                if ' ' not in data[2:]:
                    self.name = data[2:]
                else:
                    print('incorrect name', data[2:])
                    if self.r:
                        self.c.send('EN')
                print(self.name, 'joined')
            else:
                print('unknown info packet:', data)
        elif data[0] == 'A':
            if data[1] == 'K':
                for i in range(4):
                    self.player.key[i] = data[i + 2] == '1'
            elif data[1] == 'Q':
                self.close()
            else:
                print('unknown action packet:', data)
        else:
            print('unknown packet type:', data)

    def run(self):
        while self.r:
            # print('waiting for packet:', self.name)
            try:
                self.packet_recv(self.c.recv(1024))
            except socket.timeout:
                pass

            if self.r:
                if self.player.xv != 0 or self.player.yv != 0:
                    packet = 'AM' + str(self.player.x) + ' ' + str(self.player.y)
                    print(packet)
                    packet = packet.encode('utf-8')
                    self.c.send(packet)

    def close(self):
        self.c.close()
        self.s.remove(self)
        self.r = False


class client:
    def __init__(self, ip='localhost'):
        self.ip = ip
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.name = 'test'

        self.connected = False

        self.last_move = 'AK0000'

        self.x = 0
        self.y = 0

        self.connect_thread = threading.Thread(target=self._connect)
        self.connect_thread.start()
        # print(self.name, 'started connect thread')

        self.recv_thread = threading.Thread(target=self.recv)
        self.recv_thread.start()

    def update(self, key, world):
        out = ['A', 'K']
        if key[pygame.K_w]:
            out.append('1')
        else:
            out.append('0')
        if key[pygame.K_a]:
            out.append('1')
        else:
            out.append('0')
        if key[pygame.K_s]:
            out.append('1')
        else:
            out.append('0')
        if key[pygame.K_d]:
            out.append('1')
        else:
            out.append('0')

        out = ''.join(out)
        if self.connected:
            if self.connect_thread.is_alive():
                self.connect_thread.join(1)
                if self.connect_thread.is_alive():
                    self.connected = False
                else:
                    self.server.send('IN' + 'timeout')

        if self.connected and out != self.last_move:
            self.server.send(out.encode('utf-8'))
            print('packet:', out)
            self.last_move = out

        return self.x, self.y

    def _connect(self):
        self.server.connect((self.ip, 60000))
        print('connected')
        self.connected = True
        self.server.send(('IN' + self.name).encode('utf-8'))

    def recv(self):
        while not self.connected:
            print('waiting to connect')
            time.sleep(1)
        while self.connected:
            data = self.server.recv(1024).decode('utf-8')
            if data:
                if data[0] == 'A':
                    if data[1] == 'M':
                        split = data[2:].split(' ')
                        if len(split) == 2:
                            x = self.x
                            y = self.y
                            try:
                                self.x = float(split[0])
                                self.y = float(split[1])
                            except ValueError as error:
                                print(error)
                                self.x = x  # reset position to before packet to not only update x in error
                                self.y = y
                    else:
                        print('incorrect action packet:', data)
                else:
                    print('incorrect packet type:', data)

    def exit(self):
        self.server.send('AQ'.encode('utf-8'))
        self.connected = False

        print('connecting connect_thread')
        self.connect_thread.join(1)
        if self.connect_thread.is_alive():
            print('connect_thread is still alive')
        else:
            print('connect_tread joined')

        self.recv_thread.join(1)
        if self.recv_thread.is_alive():
            print('recv_thread lives on')

        self.server.close()