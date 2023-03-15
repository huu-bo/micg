import math
import pygame
import typing

import block
import net
import noise


VERSION = 'Alpha 6'
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

        self.prompt = ''
        self.prompt_shown = False
        self.chat_history = []

        gen = noise.generator(0)
        self.world = noise.world(gen)
        self.blocks = self.world.blocks

        self.players = {'self': net.player(False, self.blocks)}
        self.player = self.players['self']

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
        # TODO: player death in void
        # TODO: logging

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
                    else:
                        self.prompt += event.unicode

        kmod = pygame.key.get_mods()
        mouse_pos = pygame.mouse.get_pos()
        mouse_press = pygame.mouse.get_pressed(5)
        keys = pygame.key.get_pressed()

        if not self.prompt_shown:
            self.player.key = [keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d]]
        else:
            self.player.key = [False, False, False, False]
        self.player.physics(self.world)

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
                    if self.player.inventory[self.player.selection] > 0:
                        b = block.block(self.player.selection, self.blocks)
                        self.world.set(x, y, b)
                        self.world.to_update.append(b)

                        if mouse_pos[1] < size * 40:
                            self.player.inventory[self.player.selection] -= 1

        if self.server or not self.online:
            self.world.update(self.gameRule.fastPhysics)
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
                        # TODO: debug views
                        if self.debug['block_stress']:
                            screen.blit(self.font.render(str(b.support), True, (100, 0, 0)),
                                        (round((x - self.player.x % 1) * size), round((y - self.player.y % 1) * size)))

                    if self.debug['block_update']:
                        if b in self.world.to_update or b in self.world.to_append:
                            pygame.draw.rect(screen, (255, 0, 0),
                                             (round((x - self.player.x % 1) * size), round((y - self.player.y % 1) * size), size, size), 2)

        # draw player
        pygame.draw.rect(screen, (255, 255, 0),
                         (size * 20, size * 20, size, size))

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
            screen.blit(self.font.render(f'Position: {round(self.player.x, 3)} {round(self.player.y, 3)}', True, (255, 255, 255)), (10, 5))
            screen.blit(self.font.render(f'Motion: {round(self.player.xv, 3)} {round(self.player.yv, 3)}', True, (255, 255, 255)), (10, 25))
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
                                        block.craft(self.player.inventory, b, f, self.blocks)
                                        pygame.draw.rect(self.screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 3)
                                    elif mouse_click[0]:
                                        block.craft(self.player.inventory, b, f, self.blocks)
                                        pygame.draw.rect(self.screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 3)

                                        self.crafting = False
                                    elif mouse_click[2]:
                                        block.craft(self.player.inventory, b, f, self.blocks, amount=5)
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

        # TODO: send to multiplayer other players
        if text[0:1] == '/':
            self.chat_history.append(Chat(text, 'c', self.player.name))
            self.command(text)
        else:
            self.chat_history.append(Chat(text, 'c', self.player.name))

    def error(self, text: str):
        self.chat_history.append(Chat(text, 'e', self.player.name))

    def draw_chat(self):
        if self.prompt_shown:
            if pygame.time.get_ticks() // 200 % 2 == 0:
                cursor = '_'
            else:
                cursor = ''
            self.screen.blit(self.font.render(self.prompt + cursor, True, (255, 255, 255)), (0, size * 39))

        y = size * 40 - size - size * len(self.chat_history)
        for c in self.chat_history:
            if c.type == 'c':
                color = 255 - c.time
                color = (color, color, color)
            elif c.type == 'e':
                color = (255, 0, 0)
            else:
                assert False, f'unknown chat type: ' + "'" + c.type + "'"

            self.screen.blit(self.font.render(c.message, True, color), (0, y))
            c.time += 1
            if c.time == 255:
                self.chat_history.remove(c)
            y += size

    def command(self, command):  # TODO: if in multiplayer check permissions
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
            split = command_type.split(' ')

            if not c:
                self.error(f"command empty")

            if split[0] != c[0]:
                return False

            if len(c) != len(split):
                self.error(f"syntax error '{c}', length {len(c)}, should be {len(split)}")
                return False

            i = 1
            for command in split[1:]:
                if command == 'int':
                    if not _isint(c[i]):
                        self.error(f"'{c[i]}' is not of type: '{command}'")
                        return False
                elif command == 'block':
                    pass  # TODO: check block type
                else:
                    self.error(f"unknown command parameter type '{command}'")
                i += 1

            return True

        if not command[0] == '/':
            self.error(f"game.Game.command(), '{command}' not command?")
        split = command[1:].split(' ')
        # self.chat(f"command: '{command}'")
        # self.chat(f"    split: '{split}'")

        if _command(split, 'set int int block'):
            self.chat('set int int block')  # TODO: permissions
            self.world.set(int(split[1]), int(split[2]), block.block(split[3], self.blocks))


class GameRule:
    def __init__(self):
        self.creative = False  # allows infinite items
        self.allowFly = False  # disables movement checks
        self.keepInventory = False

        self.fastPhysics = False

        # TODO: multiplayer permissions


class Chat:
    def __init__(self, message, t, username):
        """:argument t 'c' or 'e', 'c' for chat message, 'e' for error message"""  # TODO: python 3.9 and typing.Literal
        self.message = message
        self.type = t
        self.username = username
        self.time = 0
