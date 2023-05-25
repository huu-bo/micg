import json
import math
import os
import pygame
import net
import noise

import block
import logger


# VERSION syntax:
#     M N
#     M N-pre
#     N
#     N-M
#     N-pre

#  where N is:
#    a number
#    N.N.N  # three numbers separated by dots
# where M is the full name of a greek letter starting with a capital letter
#    e.g. 'Alpha' 'Beta'

VERSION = 'Beta 1-pre'
size = 20


class Game:
    def __init__(self, screen: pygame.Surface):
        """MICG
        requires pygame to be initialised

        :argument screen: the pygame display window"""

        self.gameRule = GameRule()
        self.screen = screen

        self.online = False
        self.server = False
        self.connection = None

        self.prompt = ''
        self.prompt_shown = False
        self.chat_history = []
        self.previous_chats = []

        self.settings_gui_shown = False

        gen = noise.generator(0, floor=100)
        self.world = noise.world(gen, self)
        self.blocks = self.world.blocks

        self.players = {'self': net.player(False, self.blocks)}
        self.player = self.players['self']
        self.player.name = 'player'

        self.configfile = 'config.json'

        self.pre_mouse = [False * 3]
        self.font = pygame.font.SysFont('ubuntu', int(size / 1.1))
        self.crafting = False

        self.debug = {
            'chunk_border': False,
            'block_update': False,
            'block_stress': False,
            'player_info': False,
            'to_update': False,
        }

        # TODO: players
        # TODO: multiplayer
        # TODO: make net.player send packets to server if online (net.serverclient something does that?)
        # TODO: draw multiplayer players
        # TODO: logging
        # TODO: put a lock on player because net.client updates player position while rendering
        # TODO: world saving and loading

    def save_config(self):
        logger.log('Saving config')
        filename = self.configfile

        with open(filename, 'w') as file:
            data = {
                "username": self.player.name
            }

            json.dump(data, file)

    def load_config(self):
        filename = self.configfile
        logger.log(f"Loading log, filename: '{filename}'")

        if filename not in os.listdir('.'):
            logger.warn('    No config, creating new...')
            with open(filename, 'w') as file:
                json.dump({
                    "username": "test"
                }, file)
                return

        with open(filename, "r") as file:
            logger.log('    loading config')
            try:
                data: dict = json.load(file)
            except json.decoder.JSONDecodeError as e:
                logger.error('config.json syntax error')
                logger.error(str(e))
                logger.error('config.json:')
                file.seek(0)
                logger.error("'" + str(file.read()) + "'")

            self.player.name = str(data.setdefault('username', 'NO USERNAME'))

    def update(self) -> bool:
        """:returns a bool which is False when the game should quit"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if not self.prompt_shown:
                    if event.key == pygame.K_t:
                        self.prompt_shown = True
                        self.prompt = ''
                    elif event.key == pygame.K_SLASH:
                        self.prompt_shown = True
                        self.prompt = '/'
                else:
                    if event.key == pygame.K_ESCAPE:
                        self.prompt_shown = False
                    elif event.key == pygame.K_RETURN:
                        self.prompt_shown = False
                        self.chat()
                    elif event.key == pygame.K_BACKSPACE:
                        self.prompt = self.prompt[:-1]
                        if not self.prompt:
                            self.prompt_shown = False
                    elif event.key == pygame.K_UP:
                        if len(self.previous_chats) > 0:
                            self.prompt = self.previous_chats[-1]
                    else:
                        self.prompt += event.unicode

        mouse_pos = pygame.mouse.get_pos()
        mouse_press = pygame.mouse.get_pressed(5)
        keys = pygame.key.get_pressed()

        if not self.prompt_shown:
            self.player.key = [keys[pygame.K_w] or keys[pygame.K_UP],
                               keys[pygame.K_a] or keys[pygame.K_LEFT],
                               keys[pygame.K_s] or keys[pygame.K_DOWN],
                               keys[pygame.K_d] or keys[pygame.K_RIGHT]]
        else:
            self.player.key = [False, False, False, False]
        self.player.physics(self.world)
        if self.online and self.server:
            for player in self.connection.players:
                player.physics(self.world)

        if not self.online or self.server:
            if self.player.y > 40:
                self.player.die(self.gameRule.keepInventory)

        if mouse_pos[1] < size * 40:
            x = math.floor(mouse_pos[0] / size + self.player.x) - 20
            y = math.floor(mouse_pos[1] / size + self.player.y) - 20
            if mouse_press[2]:
                if self.world.get(x, y).solid:
                    self.player.inventory[self.world.get(x, y).name] += 1

                b = block.block('air', self.blocks)
                self.world.set(x, y, b)
                self.world.to_update.append(b)
            if not self.world.get(x, y).solid:
                if mouse_press[0]:
                    if self.player.inventory[self.player.selection] > 0 and y < 40:
                        b = block.block(self.player.selection, self.blocks)
                        self.world.set(x, y, b)
                        self.world.to_update.append(b)

                        if mouse_pos[1] < size * 40:
                            self.player.inventory[self.player.selection] -= 1

        if self.server or not self.online:
            self.world.update(pygame.time.get_ticks())
        else:
            self.world.to_update = []
            self.world.to_append = []

        return True

    def draw(self):
        screen = self.screen
        screen.fill((0, 0, 0))

        kmod = pygame.key.get_mods()
        mouse_pos = pygame.mouse.get_pos()
        mouse_press = pygame.mouse.get_pressed(3)
        mouse_click = [mouse_press[i] and not self.pre_mouse[i] for i in range(3)]

        # world rendering
        for y in range(41):
            for x in range(41):
                b = self.world.get(x + math.floor(self.player.x - 20), y + math.floor(self.player.y) - 20)
                if b is not None:
                    if b.render:
                        pygame.draw.rect(screen, b.color,
                                         (round((x - self.player.x % 1) * size), round((y - self.player.y % 1) * size),
                                          size, size))
                        if self.debug['block_stress']:
                            screen.blit(self.font.render(str(b.support), True, (100, 0, 0)),
                                        (round((x - self.player.x % 1) * size), round((y - self.player.y % 1) * size)))

                    if self.debug['block_update']:
                        if b in self.world.to_update or b in self.world.to_append:
                            pygame.draw.rect(screen, (255, 0, 0),
                                             (round((x - self.player.x % 1) * size),
                                              round((y - self.player.y % 1) * size), size, size), 2)

        # draw player
        pygame.draw.rect(screen, (255, 255, 0),
                         (size * 20, size * 20, size, size))

        # draw online players
        if self.online and self.server:
            for p in self.connection.players:
                # pygame.draw.rect(screen, (255, 0, 0), ((p.x - px) * size, (p.y - py) * size, size, size))
                # pygame.draw.rect(screen, (255, 0, 0), (round(p.x * size), p.y * size, size, size))
                print(p.x, p.y)
                pygame.draw.rect(screen, (255, 0, 0),
                                 (round((p.x - self.player.x) * size), round((p.y - self.player.y + 20) * size), size, size))
        elif self.online and not self.server:
            for i in self.connection.players:
                p = self.connection.players[i]
                pygame.draw.rect(screen, (255, 0, 0),
                                 (round((p.x - self.player.x) * size), round((p.y - self.player.x + 20) * size), size, size))

        # inventory ui
        self.draw_inventory(mouse_pos, mouse_press, mouse_click)

        # debug ui
        self.draw_debug_settings(mouse_pos, mouse_click, kmod)

        # prompt
        self.draw_chat()

        # draw chunk borders
        if self.debug['chunk_border']:
            pygame.draw.line(screen, (255, 0, 0),
                             ((40 - self.player.x % 40) * size, 0),
                             ((40 - self.player.x % 40) * size, 800))
            pygame.draw.line(screen, (255, 0, 0),
                             (0, (40 - self.player.y % 40) * size),
                             (800, (40 - self.player.y % 40) * size))

        if self.debug['player_info']:
            screen.blit(self.font.render(f'Position: {round(self.player.x, 3)} {round(self.player.y, 3)}', True,
                                         (255, 255, 255)), (10, 5))
            screen.blit(self.font.render(f'Motion: {round(self.player.xv, 3)} {round(self.player.yv, 3)}', True,
                                         (255, 255, 255)), (10, 25))
            # screen.blit(self.font.render(f'onGround: {self.player}', True, (255, 255, 255)), (10, 55))

        if len(self.world.to_update) > 100 or self.debug['to_update']:
            screen.blit(self.font.render('processing ' + str(len(self.world.to_update)), True, (255, 255, 255)),
                        (10, 10 + 75 * self.debug['player_info']))

        self.pre_mouse = mouse_press

    def draw_inventory(self, mouse_pos, mouse_press, mouse_click):
        kmod = pygame.key.get_mods()
        if kmod & pygame.KMOD_CTRL:
            return
        if self.prompt_shown:
            return

        if not self.crafting:
            pygame.draw.rect(self.screen, (0, 0, 0), (0, size * 40, size * 40, size * 2))  # black background

            i = 0
            for b in self.player.inventory:
                c = block.color(b, self.blocks)

                pygame.draw.rect(self.screen, c, (i * size, size * 40, size, size))
                self.screen.blit(self.font.render(
                    str(self.player.inventory[b]),
                    True, (255, 255, 255)), (i * size, size * 41))

                if self.player.selection == b:
                    pygame.draw.rect(self.screen, ((255 - c[0]) % 255, (255 - c[1]) % 255, (255 - c[2]) % 255),
                                     (i * size, size * 40, size, size), 1)

                if size * 40 < mouse_pos[1] < size * 41:
                    if i * size < mouse_pos[0] < (i + 1) * size:
                        pygame.draw.rect(self.screen, ((255 - c[0]) % 255, (255 - c[1]) % 255, (255 - c[2]) % 255),
                                         (i * size, size * 40, size, size), 2)

                        if mouse_press[0]:
                            self.player.selection = b

                            pygame.draw.rect(self.screen, (255, 255, 255), (i * size, size * 40, size, size), 3)

                i += 1
            pygame.draw.rect(self.screen, (255, 255, 255), (i * size, size * 40, size, size))
            if size * 40 < mouse_pos[1] < size * 41:
                if i * size < mouse_pos[0] < (i + 1) * size:
                    pygame.draw.rect(self.screen, (0, 0, 0), (i * size, size * 40, size, size), 2)

                    if mouse_press[0]:
                        self.crafting = True

                        pygame.draw.rect(self.screen, (0, 0, 0), (i * size, size * 40, size, size), 3)
        else:
            i = 0
            for b in self.player.inventory:
                if b in self.blocks:
                    bc = block.color(b, self.blocks)
                    r = block.recipies(b, self.blocks)
                    if r:
                        for f in r:
                            c = block.color(f, self.blocks)

                            pygame.draw.rect(self.screen, c, (i * size, size * 40, size, size))  # craft this block
                            pygame.draw.rect(self.screen, bc, (i * size, size * 41, size, size))  # from this block

                            if size * 40 < mouse_pos[1] < size * 42:  # TODO: multi-material recipy (rendering)
                                if i * size < mouse_pos[0] < (i + 1) * size:
                                    pygame.draw.rect(self.screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 2)

                                    if kmod & pygame.KMOD_SHIFT and mouse_press[0]:
                                        block.craft(self.player.inventory, b, f, self.blocks, self)
                                        pygame.draw.rect(self.screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 3)
                                    elif mouse_click[0]:
                                        block.craft(self.player.inventory, b, f, self.blocks, self)
                                        pygame.draw.rect(self.screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 3)

                                        self.crafting = False
                                    elif mouse_click[2]:
                                        block.craft(self.player.inventory, b, f, self.blocks, self, amount=5)
                                        pygame.draw.rect(self.screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 3)

                                        self.crafting = False

                            i += 1

    def draw_debug_settings(self, mouse_pos, mouse_click, kmod):
        if self.prompt_shown:
            return

        if kmod & pygame.KMOD_LCTRL:
            i = 0
            for d in self.debug:
                if self.debug[d]:
                    c = (0, 255, 0)
                else:
                    c = (255, 0, 0)
                if size * 40 < mouse_pos[1] < size * 41:
                    if i * size * 6 < mouse_pos[0] < (i + 1) * size * 6:
                        if self.debug[d]:
                            c = (200, 255, 200)
                        else:
                            c = (255, 100, 100)
                        if mouse_click[0]:
                            c = (255, 255, 255)
                            self.debug[d] = not self.debug[d]
                pygame.draw.rect(self.screen, c, (i * size * 6, size * 40, size * 6, size), 2)

                self.screen.blit(self.font.render(d, True, (255, 255, 255)), (i * size * 6, size * 40))

                i += 1

    def chat(self, text=None):
        if text is None:
            text = self.prompt

        self.previous_chats.append(text)

        # TODO: send to multiplayer other players

        if self.player.name is None:
            logger.warn("The player name is None!!")
            self.chat_history.append(Chat("Your player name is null!! (??)", 'e', 'ERROR'))
            return

        if text[0:1] == '/':
            self.command(text)

            logger.log(f'<{self.player.name}> ' + text)  # TODO: multiplayer players
        else:
            self.chat_history.append(Chat(text, 'c', self.player.name))

            logger.log(f'<{self.player.name}> ' + text)  # TODO: multiplayer players

    def info(self, *args):

        message = ' '.join(args)

        self.chat_history.append(Chat(message, 'c', "[INFO]"))
        logger.log(message)

    def warn(self, *args):

        message = ' '.join(args)

        self.chat_history.append(Chat(message, 'c', "[WARN]"))
        logger.log(message)

    def error(self, *args):

        message = ' '.join(args)

        self.chat_history.append(Chat(message, 'e', self.player.name))
        logger.error(message)

    def draw_chat(self):
        if self.prompt_shown:
            if pygame.time.get_ticks() // 200 % 2 == 0:
                cursor = '_'
            else:
                cursor = ''
            self.screen.blit(self.font.render("> " + self.prompt + cursor, True, (255, 255, 255)), (0, size * 39))

        y = size * 40 - size - size * len(self.chat_history)
        for c in self.chat_history:
            if c.type == 'c':
                color = 255 - c.time
                color = (color, color, color)
            elif c.type == 'e':
                color = (255, 0, 0)
            else:
                assert False, f'Unknown chat type: ' + "'" + c.type + "'"  # should this crash?

            if self.prompt_shown and color != (255, 0, 0):
                color = (255, 255, 255)

            if self.online:
                self.screen.blit(self.font.render('<' + c.username + '> ' + c.message, True, color), (0, y))
            else:
                self.screen.blit(self.font.render(c.message, True, color), (0, y))

            if not self.prompt_shown:
                c.time += 1
                if c.time == 255:
                    self.chat_history.remove(c)

            y += size

    def command(self, command: str):  # TODO: if in multiplayer check permissions
        def _isint(i: str):
            for c in i:
                if c not in '0123456789-':  # TODO: something like minecraft '~'
                    return False
            try:
                int(i)
                return True
            except ValueError:
                return False

        def _command(c: list, command_type: str):
            # TODO: if multiplayer send command to server

            split = command_type.split(' ')

            if not c:
                self.error(f"Command may not be empty!")

            if split[0] != c[0]:
                return False

            if len(c) != len(split):
                self.error(f"Syntax error '{' '.join(c)}', length {len(c)}, should be {len(split)}")
                return False

            i = 1
            for command in split[1:]:
                if command == 'int':
                    if not _isint(c[i]):
                        self.error(f"'{c[i]}' is not of type: '{command}'")
                        return False
                elif command == 'block':
                    if c[i] not in self.blocks:
                        self.error(f"Unknown block type: '{c[i]}'")
                        return False
                elif command == 'player':
                    if c[i] in ['@s', '@p', '@a']:
                        pass
                    # TODO: multiplayer players
                    else:
                        self.error(f"Unknown player '{c[i]}'")
                        return False
                elif command == 'gamerule':
                    if c[i] not in self.gameRule.__dict__:
                        self.error(f"Unknown gamerule '{c[i]}'")
                        return False
                else:
                    self.error(f"Unknown command parameter type '{command}'")
                i += 1

            return True

        if not command[0] == '/':
            self.error(f"game.Game.command(), '{command}' not command?")
        split = command[1:].split(' ')
        # self.chat(f"command: '{command}'")
        # self.chat(f"    split: '{split}'")

        # TODO: always allow host to execute commands
        if _command(split, 'set int int block'):
            if self.gameRule.permissionSetBlock:
                self.world.set(int(split[1]), int(split[2]), block.block(split[3], self.blocks))
                self.info("Set block " + split[1] + " " + split[2] + " to " + split[3])
            else:
                self.error('Not enough permissions to set a block!')
        elif _command(split, 'give player block int'):
            # TODO: not only to yourself
            if self.gameRule.permissionGive:
                self.player.inventory[split[2]] += int(split[3])
                self.info("Gave " + split[3] + " " + split[2] + " to " + self.player.name)
            else:
                s = 'Not enough permissions to give an item'

                if int(split[3]) != 1:
                    s += 's!'
                else:
                    s += "!"

                self.error(s)
        elif _command(split, 'fill int int int int block') or _command(split, 'fill int int int int block int'):
            from_x = int(split[1])
            to_x = int(split[3])
            from_y = int(split[2])
            to_y = int(split[4])
            b = split[5]

            if len(split) == 7:
                update = False
            else:
                update = True

            for x in range(from_x, to_x):
                for y in range(from_y, to_y):
                    if update:
                        self.world.set(x, y, block.block(b, self.blocks), block_update=(x == from_x or x == to_x - 1))
                    else:
                        self.world.set(x, y, block.block(b, self.blocks), block_update=False)
        elif split[0] == 'gamerule':
            if len(split) == 1:
                for rule in self.gameRule.__dict__:
                    self.chat(rule)
            elif _command(split, 'gamerule gamerule int'):
                if self.gameRule.permissionChangeGamerule:
                    self.gameRule.__dict__[split[1]] = not not int(split[2])
                    self.info("Changed gamerule " + split[1] + " to " + split[2])
                else:
                    self.error('Not enough permissions to change gamerules!')
        elif split[0] == 'kill':
            self.player.die(self.gameRule.keepInventory)
        elif split[0] == 'join':
            if len(split) == 1:
                self.join()
            elif len(split) == 2:
                self.join(split[1])
            else:
                self.error(f"use join as '/join' or '/join ip' not '{command}'")
        elif split[0] == 'host':
            if len(split) == 1:
                try:
                    self.host()
                except IOError as e:
                    self.error(str(e))
            elif len(split) == 2:
                try:
                    self.host(split[1])
                except IOError as e:
                    self.error(str(e))
            else:
                self.error(f"Use host as '/host' or '/host ip' not '{command}'")

        elif split[0] == 'save':
            if len(split) != 2:
                self.error(f"'{command}', '{split}' incorrect syntax, expected save name")
            else:
                self.save(split[1])
        elif split[0] == 'load':
            if len(split) != 2:
                self.error(f"'{command}', '{split}' incorrect syntax, expected save name")
            else:
                self.load(split[1])

        elif split[0] == 'temp':
            x = self.player.x // 20
            y = self.player.y // 20

            temp = self.world.temperature_gen.gen(int(x)) + int(y)

            self.chat(str(temp))

        elif _command(split, 'tp int int'):
            self.player.x = int(split[1])
            self.player.y = int(split[2])

        elif split[0] == 'x':
            try:
                self.chat(repr(eval(''.join(split[1:]))))
            except Exception as e:
                self.error(str(e))

        else:
            self.error('Unknown or improper command: ' + split[0])

    def join(self, ip='localhost'):
        self.connection = net.client(self.world, ip=ip)

        self.world = noise.world(noise.generator(0), self, gen_new=False, server=self.connection, serving=False)
        self.connection.world = self.world

        self.connection.players[self.connection.name] = net.player(True, self.blocks, server=self.connection, physics=False)
        self.player = self.connection.players[self.connection.name]

        self.online = True
        self.server = False

    def host(self, ip='localhost'):
        self.connection = net.Server(None, ip=ip)

        self.world = noise.world(noise.generator(0), self, True, self.connection, True)
        self.connection.world = self.world

        self.online = True
        self.server = True

    def save(self, filename: str):
        if 'saves' not in os.listdir('./'):
            os.mkdir('saves')

        save = {
            'world': self.world.save(),
            'version': VERSION,

            'player': self.player.save(),
            'gamerule': self.gameRule.save()
        }
        with open('./saves/' + filename + '.json', 'w') as file:
            json.dump(save, file)

    def load(self, filename: str):
        logger.log(f"loading world '{filename}'")

        if 'saves' not in os.listdir('./'):
            self.error('no saves folder')
            return

        if filename + '.json' not in os.listdir('./saves/'):
            self.error(f"world {filename} does not exist")
            return

        try:
            with open('./saves/' + filename + '.json', 'r') as file:
                save = json.load(file)
        except json.JSONDecodeError:
            self.error('corrupt save file')

        if 'version' in save:  # TODO: parse and check version number
            logger.log('Beta world')

            if save['version'] != VERSION:
                logger.warn(f"save version: '{save['version']}', current version: '{VERSION}'")

            self.world.load(save['world'])  # TODO: load player

            self.player.load(save['player'])  # TODO: store multiplayer other players
            self.gameRule.load(save['gamerule'])
        else:  # Alpha saves
            logger.log('Alpha world')
            self.world.load(save)
            self.player.x = 20
            self.player.y = 20

    def quit(self):
        if self.connection is not None:
            self.connection.exit()


class GameRule:
    def __init__(self):
        self.creative = False  # allows infinite items
        self.allowFly = False  # disables movement checks
        self.keepInventory = False

        # TODO: multiplayer permissions
        self.permissionChangeGamerule = True  # False: host, True: everyone
        self.permissionSetBlock = False
        self.permissionGive = False

    def save(self):
        return {i: self.__dict__[i] for i in self.__dict__ if not i.startswith('--')}

    def load(self, raw: dict):
        for i in raw:
            self.__dict__[i] = raw[i]


class Chat:
    def __init__(self, message, t, username):
        """:argument t 'c' or 'e', 'c' for chat message, 'e' for error message"""  # TODO: python 3.9 and typing.Literal
        self.message = message
        self.type = t
        self.username = username
        self.time = 0
