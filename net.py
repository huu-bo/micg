#  net, short for networking
import socket
import threading
import pygame.constants
import math
import time

import block


class net:
    def __init__(self, s: socket.socket):
        self.messages = []
        self.last = ''
        self.s = s

    def recv(self, data: bytes):
        data = data.decode('utf-8')
        if ';' not in data:
            self.last += data
        else:
            split = data.split(';')
            for i in range(len(split)):
                if i == 0:
                    self.messages.append(self.last + split[i])
                    self.last = ''
                elif i != len(split) - 1:
                    self.messages.append(split[i])
                else:
                    self.last = split[i]

        m = self.messages
        self.messages = []
        return m

    def send(self, packet: str):
        if ';' in packet[:-1]:
            for p in packet.split(';'):
                self.send(p + ';')
        else:
            if packet[-1] != ';':
                packet += ';'
            self.s.send(packet.encode('utf-8'))


# packets:
# first letter type, information/action
# second letter data

# IN:
# name

# IB:
# x y type

# IC: get chunk

# AK:
# wasd changed
# 0000 binary for wasd

# AP:
# x y type
# place block, also for deleting block since you're basically placing air

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
    def __init__(self, world, ip='localhost'):
        self.threads = []
        self.run = True
        self.world = world

        self.players = []
        self.pipes = []

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
                pi = pipe()
                self.pipes.append(pi)
                self.threads.append(threading.Thread(target=server_client, args=[c, self, p, pi]))
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

    def send_all(self, data):
        for p in self.pipes:
            p.send(data)


class server_client:
    def __init__(self, c: socket.socket, s: server, p: player, pi):
        self.c = c
        self.s = s
        self.r = True
        self.name = 'NAME_NOT_SENT'
        self.player = p
        self.pipe = pi
        self.net = net(c)

        self.world = self.s.world

        self.c.settimeout(.02)
        self.run()

    def packet_recv(self, packet: str):
        # data = packet.decode('utf-8')
        data = packet
        print("client: '" + self.name + "' packet: '" + data + "'")
        if data[0] == 'I':
            if data[1] == 'N':
                if ' ' not in data[2:]:
                    self.name = data[2:]
                else:
                    print('incorrect name', data[2:])
                    if self.r:
                        self.net.send('EN')
                print(self.name, 'joined')
            elif data[1] == 'B':
                split = data[2:].split(' ')
                print('block info', split, 'deprecated')
                if self.world is not None:
                    if len(split) == 2:
                        x = int(split[0])
                        y = int(split[1])
                        packet = 'IB' + str(x) + ' ' + str(y) + ' ' + self.world.get(x, y).name
                        self.net.send(packet)
                        print(packet)
                    else:
                        raise ValueError(data)
                else:
                    raise ValueError('server_client.world is None')
            elif data[1] == 'C':
                split = data[2:].split(' ')
                if len(split) == 2:
                    c = self.world.serialize_chunk(int(split[0]), int(split[1]))
                    # print('IC' + split[0] + ' ' + split[1] + ' ' + c[:50])
                    self.net.send('IC' + split[0] + ' ' + split[1] + ' ' + c)
            else:
                print('unknown info packet:', data)
        elif data[0] == 'A':
            if data[1] == 'K':
                for i in range(4):
                    self.player.key[i] = data[i + 2] == '1'

            elif data[1] == 'P':
                split = data[2:].split(' ')
                if len(split) != 3:
                    return

                self.world.set(int(split[0]), int(split[1]), block.block(split[2], self.world.blocks))
                self.s.send_all(data)  # let all the other clients know,
                # will cause the packet to be sent back to the client that sent it

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
                for p in self.net.recv(self.c.recv(1024)):
                    self.packet_recv(p)
            except socket.timeout:
                pass

            data = self.pipe.recv()
            if data is not None:
                for packet in data:
                    # if data[:2] == 'AP':
                    self.net.send(packet)
                    data = self.pipe.recv()

            if self.r:
                if self.player.xv != 0 or self.player.yv != 0:
                    packet = 'AM' + str(self.player.x) + ' ' + str(self.player.y)
                    self.net.send(packet)

    def close(self):
        self.c.close()
        self.s.remove(self)
        self.r = False


class client:
    def __init__(self, world, ip='localhost'):
        self.ip = ip
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.net = net(self.server)

        self.world = world
        self.chunk_requests = {}  # chunks for which requests have been sent to the server

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
        if key[pygame.K_w] or key[pygame.K_UP]:
            out.append('1')
        else:
            out.append('0')
        if key[pygame.K_a] or key[pygame.K_LEFT]:
            out.append('1')
        else:
            out.append('0')
        if key[pygame.K_s] or key[pygame.K_DOWN]:
            out.append('1')
        else:
            out.append('0')
        if key[pygame.K_d] or key[pygame.K_RIGHT]:
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
                    self.net.send('IN' + 'timeout')  # ?

        if self.connected and out != self.last_move:
            self.net.send(out)
            self.last_move = out

        return self.x, self.y

    def _connect(self):
        self.server.connect((self.ip, 60000))
        print('connected')
        self.connected = True
        self.net.send('IN' + self.name)

    def recv(self):
        while not self.connected:
            print('waiting to connect')
            time.sleep(1)
        while self.connected:
            for p in self.net.recv(self.server.recv(1024)):
                self.recv_packet(p)

    def recv_packet(self, data):
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
                elif data[1] == 'P':
                    split = data[2:].split(' ')
                    if len(split) == 3:
                        self.world.set(int(split[0]), int(split[1]), block.block(split[2], self.world.blocks),
                                       update=False)
                    else:
                        print('incorrect packet')  # TODO: keep track of amount of incorrect packets
                else:
                    print('incorrect action packet:', data)

            elif data[0] == 'I':
                if data[1] == 'C':
                    split = data[2:].split(' ')
                    self.world.deserialise_chunk(data[2:-1])
                    self.chunk_requests[(int(split[0]), int(split[1]))] = True
                else:
                    print('incorrect information packet type:', data)

            else:
                print('incorrect packet type:', data)

    def get_chunk(self, x, y):
        if (x, y) not in self.chunk_requests:
            packet = 'IC' + str(x) + ' ' + str(y)
            self.net.send(packet)
            self.chunk_requests[(x, y)] = False

            t = 0
            while not self.chunk_requests[(x, y)]:
                time.sleep(.1)
                t += 1
                if t > 1000 and not self.chunk_requests[(x, y)]:
                    print('chunk request timeout')

                    packet = 'IC' + str(x) + ' ' + str(y)
                    self.net.send(packet)
                    self.chunk_requests[(x, y)] = True
                    t = 0

    def set_block(self, x, y, value):
        self.net.send('AP' + str(x) + ' ' + str(y) + ' ' + value.name)

    def exit(self):
        self.net.send('AQ')
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


class pipe:
    def __init__(self):
        self.data = []

    def recv(self):
        if not self.data:
            ret = None
        else:
            ret = self.data
            self.data = []
        return ret

    def send(self, data):
        self.data.append(data)
