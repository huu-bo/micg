#  net, short for networking
import socket
import threading
import pygame.constants
import math
import time

import block
import game
import logger
import noise


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

# AM:
# x y

# AD:
#
# player death

# IM:
# x y name
# sent from server_client to client to let client know about other clients moving
# maybe this could be used as AM

# IQ: (not implemented yet)
# name
# let other clients know about other clients disconnecting

# AQ:
# quit

# EN:
# name contains space


class player:
    def __init__(self, online, blocks, server=None, physics=True):
        self.x = 0
        self.y = -70
        self.xv = 0
        self.yv = 0

        self.key = [False, False, False, False]  # up, left, down, right

        self.name = None
        self.selection = 'grass'
        if online and server is None:
            logger.warn('player online and no connection?????')
        self.server = server
        self.online = online
        self.phy = physics

        self.inventory = {i: 0 for i in blocks if blocks[i]['solid']}
        # TODO: property for if item should be mineable and be able to put in the inventory

    def physics(self, world):
        # TODO: some way to enable flying

        if not self.phy:
            # self.server.net.send(f'AM{self.x} {self.y}')
            packet = 'AK'
            for k in self.key:
                if k:
                    packet += '1'
                else:
                    packet += '0'
            self.server.net.send(packet)
        elif world.game.gameRule.allowFly:
            if self.key[3]:
                self.xv += .1
            if self.key[1]:
                self.xv -= .1

            if self.key[2]:
                self.yv += .1
            if self.key[0]:
                self.yv -= .1

            self.x += self.xv
            self.y += self.yv

            self.xv /= 1.1
            self.yv /= 1.1
        else:
            if self.key[3]:
                self.xv += .1
            if self.key[1]:
                self.xv -= .1

            self.yv += .1
            self.y += self.yv

            if (
                    world.get(math.floor(self.x), math.ceil(self.y) - 1).solid
                    or world.get(math.ceil(self.x), math.ceil(self.y) - 1).solid
                    or world.get(math.floor(self.x), math.ceil(self.y)).solid
                    or world.get(math.ceil(self.x), math.ceil(self.y)).solid
            ):
                step = .01
                amount = 1000
                for i in range(amount):
                    y = self.y - i * step
                    if (
                            not world.get(math.floor(self.x), math.floor(y)).solid
                            and not world.get(math.ceil(self.x), math.floor(y)).solid
                            and not world.get(math.floor(self.x), math.ceil(y)).solid
                            and not world.get(math.ceil(self.x), math.ceil(y)).solid
                    ):
                        self.y = y
                        self.yv = 0
                        break

                    y = self.y + i * step
                    if not world.get(math.floor(self.x), math.ceil(y)).solid and \
                            not world.get(math.ceil(self.x), math.ceil(y)).solid:
                        self.y = y
                        self.yv = 0
                        break
                else:
                    logger.log('suffocated')  # TODO: this is a dumb message
                    self.die(world.game.gameRule.keepInventory)

            if (  # TODO: filthy hack
                    world.get(math.floor(self.x), math.ceil(self.y + .1)).solid
                    or world.get(math.ceil(self.x), math.ceil(self.y + .1)).solid
            ):
                floor = True
            else:
                floor = False

            if floor and self.key[0]:
                self.yv = -.55

            self.x += self.xv
            while world.get(math.ceil(self.x), math.ceil(self.y)).solid:
                self.x -= .01
                self.xv = 0
            while world.get(math.floor(self.x), math.ceil(self.y)).solid:
                self.x += .01
                self.xv = 0

            if abs(self.xv) < .03:
                if abs(round(self.x) - self.x) < .2:
                    self.x = round(self.x)

            if floor:
                # TODO: filthy hack
                friction = min(
                    world.get(math.floor(self.x), math.ceil(self.y + .1)).friction,
                    world.get(math.ceil(self.x), math.ceil(self.y + .1)).friction
                )
            else:
                friction = 2
            self.xv /= friction

        if self.online and self.phy:
            packet = f'IM{self.x} {self.y} {self.name}'
            if type(self.server) == Server:
                self.server.send_all(packet)
            else:
                self.server.s.send_all_except(packet, self.server.pipe)

    def die(self, keep_inventory):

        logger.log(f"Player {self.name} died at {self.x}, {self.y}")

        if self.phy and self.online:
            self.server.net.send('AD')

        self.x = 0
        self.y = -70
        self.xv = 0
        self.yv = 0

        self.key = [False, False, False, False]

        if not keep_inventory:
            for i in self.inventory:
                self.inventory[i] = 0

    def save(self):
        return {
            'x': self.x,
            'y': self.y,
            'name': self.name,
            'inventory': self.inventory
        }

    def load(self, raw: dict):
        self.x = raw['x']
        self.y = raw['y']
        self.name = raw['name']
        self.inventory = raw['inventory']


class Server:
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
        # self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.listen()

        self.accept_thread = threading.Thread(target=self._accept, name='accept')
        self.accept_thread.start()
        self.threads.append(self.accept_thread)

    def _accept(self):
        while self.run:
            try:
                c, address = self.server.accept()
                logger.log(f'Accepted {c}, {address}')
                p = player(True, self.world.blocks)
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
            logger.log(f'Joining {t}')
            t.join(1)
            if t.is_alive():
                logger.warn(f'{t}, is still alive')

    def remove(self, s_c):
        self.players.remove(s_c.player)

    def send_all(self, data):
        for p in self.pipes:
            p.send(data)

    def send_all_except(self, data, exception):  # TODO: broken
        for p in self.pipes:
            if p is not exception:
                p.send(data)

    def chat(self, text: str):
        self.send_all('AC' + text)


class server_client:
    def __init__(self, c: socket.socket, s: Server, p: player, pi):
        self.c = c
        self.s = s
        self.r = True  # TODO: what is 'r'
        self.name = 'NAME_NOT_SENT'
        self.player = p
        self.player.server = self
        self.pipe = pi
        self.net = net(c)

        self.world: noise.world = self.s.world

        self.c.settimeout(.02)
        self.run()

    def packet_recv(self, packet: str):
        # data = packet.decode('utf-8')
        data = packet
        # info("client: '" + self.name + "' packet: '" + data + "'")
        if data[0] == 'I':
            if data[1] == 'N':
                had_name = self.name != 'NAME_NOT_SENT'
                duplicate = False

                # print(self.s.players)
                for p in self.s.players:
                    if data[2:] == p.name:
                        duplicate = True
                if data[2:] == self.world.game.player.name:
                    duplicate = True

                if ' ' not in data[2:] and not duplicate:
                    self.name = data[2:]
                    self.net.send('IN' + self.name)
                else:
                    logger.error(f"incorrect name '{data[2:]}'")
                    if self.r:
                        self.net.send('EN')
                if not had_name:
                    # let all the other clients that are not this client know that this client exists
                    self.s.send_all_except('IN' + self.name, self.pipe)
                logger.log(f'{self.name} joined')
                self.net.send(f'IN{self.world.game.player.name}')
            elif data[1] == 'B':
                split = data[2:].split(' ')
                logger.warn('block info deprecated')
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
                logger.error(f"Unknown info packet: '{data}'")
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

            elif data[1] == 'D':
                self.player.die(self.world.game.gameRule.keepInventory)

            elif data[1] == 'Q':
                self.close()

            elif data[1] == 'C':
                self.world.game.chat_history.append(game.Chat(data[2:], 'c', '#TODO'))  # TODO: username

            else:
                logger.error(f"Unknown action packet: '{data}'")
        else:
            logger.error(f"Unknown packet type: '{data}'")

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

            if self.player.xv != 0 or self.player.yv != 0:
                packet = 'AM' + str(self.player.x) + ' ' + str(self.player.y)
                self.net.send(packet)

                packet = 'IM' + str(self.player.x) + ' ' + str(self.player.y) + ' ' + self.name
                self.s.send_all(packet)

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
        self.players = {}
        self.world.game.players = self.players
        self.world.game.player = player(False, self.world.blocks)  # placeholder

        self.connected = False

        self.last_move = 'AK0000'

        self.connect_thread = threading.Thread(target=self._connect)
        self.connect_thread.start()
        # print(self.name, 'started connect thread')

        self.recv_thread = threading.Thread(target=self.recv)
        self.recv_thread.start()

    def _connect(self):
        self.server.connect((self.ip, 60000))
        logger.log(f'Connected with {self.ip}')
        self.connected = True
        self.net.send('IN' + self.name)

    def recv(self):
        i = 0
        while not self.connected:
            if i < 2:
                logger.log('Waiting to connect...')
            elif i < 10:
                logger.warn('Waiting to connect...')
            else:
                logger.error('connect timeout')
                return
            time.sleep(1)
            i += 1
        while self.connected:
            for p in self.net.recv(self.server.recv(1024)):
                self.recv_packet(p)

    def recv_packet(self, data):
        # print(f"client received packet '{data}'")
        if data:
            if data[0] == 'A':
                if data[1] == 'M':
                    split = data[2:].split(' ')
                    if len(split) == 2:
                        x = self.players[self.name].x
                        y = self.players[self.name].y
                        try:
                            self.players[self.name].x = float(split[0])
                            self.players[self.name].y = float(split[1])
                        except ValueError as error:
                            logger.exception('while updating player position', error)
                            self.players[self.name].x = x  # reset position to before packet to not only update x in error
                            self.players[self.name].y = y
                elif data[1] == 'P':
                    split = data[2:].split(' ')
                    if len(split) == 3:
                        self.world.set(int(split[0]), int(split[1]), block.block(split[2], self.world.blocks),
                                       update=False)
                    else:
                        logger.error(f"Incorrect packet '{data}'")  # TODO: keep track of amount of incorrect packets
                elif data[1] == 'C':
                    self.world.game.chat_history.append(game.Chat(data[2:], 'c', '#TODO'))  # TODO: username
                else:
                    logger.error(f"Incorrect action packet: '{data}'")

            elif data[0] == 'I':
                if data[1] == 'C':
                    split = data[2:].split(' ')
                    self.world.deserialise_chunk(data[2:-1])
                    self.chunk_requests[(int(split[0]), int(split[1]))] = True
                elif data[1] == 'N':
                    if data[2:] not in self.players:
                        p = player(True, self.world.blocks, server=self, physics=False)
                        p.name = data[2:]
                        self.players[data[2:]] = p
                        if p.name == self.name:
                            self.world.game.player = p
                        logger.log(f'Player {data[2:]} joined')
                    else:
                        logger.log(f'Player {data[2:]} joined multiple times')  # TODO: let clients know about other clients disconnecting
                elif data[1] == 'M':
                    split = data[2:].split(' ')
                    name = split[2]
                    if name in self.players:
                        self.players[name].x = float(split[0])
                        self.players[name].y = float(split[1])
                    elif name == self.world.game.player.name:
                        self.world.game.player.x = float(split[0])
                        self.world.game.player.y = float(split[1])
                    else:
                        logger.warn(f"Player '{name}' moved but does not exist")
                else:
                    logger.warn(f'Incorrect information packet type: {data}')

            elif data[0] == 'E':
                if data[1] == 'N':
                    name = self.name
                    self.name = self.name.replace(' ', '') + '+'
                    self.net.send('IN' + self.name)
                    self.players[self.name] = self.players[name]
                    self.players.pop(name)
                    self.players[self.name].name = self.name
                else:
                    logger.error(f"Unknown error packet: '{data}'")

            else:
                logger.warn(f'Incorrect packet type: {data}')

    def get_chunk(self, x, y):
        if (x, y) not in self.chunk_requests:
            packet = 'IC' + str(x) + ' ' + str(y)
            self.net.send(packet)  # TODO: will send packets even if connection is not established and crash
            self.chunk_requests[(x, y)] = False

            t = 0
            while not self.chunk_requests[(x, y)]:
                time.sleep(.1)
                t += 1
                if t > 10 and not self.chunk_requests[(x, y)]:
                    logger.warn('Chunk request timeout')

                    packet = 'IC' + str(x) + ' ' + str(y)
                    self.net.send(packet)
                    self.chunk_requests[(x, y)] = True
                    t = 0

    def set_block(self, x, y, value):
        self.net.send('AP' + str(x) + ' ' + str(y) + ' ' + value.name)

    def chat(self, text: str):
        self.net.send('AC' + text)

    def exit(self):
        self.net.send('AQ')
        self.connected = False

        logger.log('connecting connect_thread')
        self.connect_thread.join(1)
        if self.connect_thread.is_alive():
            logger.warn('connect_thread is still alive')
        else:
            logger.log('connect_tread joined')

        self.recv_thread.join(1)
        if self.recv_thread.is_alive():
            logger.log('recv_thread lives on')

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