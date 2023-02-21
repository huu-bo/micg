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
        self.chat_history = []  # [[10, 'Hello, World!'], [7, 'a']] list of amount of frames chat is on screen

        gen = noise.generator(0)
        self.world = noise.world(gen)
        self.blocks = self.world.blocks

        self.players = {'self': net.player(False, self.blocks)}
        self.player = self.players['self']

        self.pre_mouse = [False * 3]
        self.font = pygame.font.SysFont('ubuntu', int(size / 1.1))
        self.crafting = False

        # TODO: players
        # TODO: multiplayer
        # TODO: player inventory and block selection HUD
        # TODO: make net.player send packets to server if online
        # TODO: chat and prompt
        # TODO: fix player physics
        # TODO: make the player snap to coordinates if above hole and low x velocity
        # TODO: draw multiplayer players

    def update(self) -> bool:
        """:returns a bool which is False when the game should quit"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        kmod = pygame.key.get_mods()
        mouse_pos = pygame.mouse.get_pos()
        mouse_press = pygame.mouse.get_pressed(5)
        keys = pygame.key.get_pressed()

        self.player.key = [keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d]]
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
            self.world.update(False)  # TODO: fast update
        else:
            self.world.to_update = []
            self.world.to_append = []

        return True

    def draw(self):
        screen = self.screen
        screen.fill((0, 0, 0))

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
                        # if debug['block_stress']:
                        #     screen.blit(font.render(str(b.support), True, (100, 0, 0)),
                        #                 (round((x - self.player.x % 1) * size), round((y - self.player.y % 1) * size)))

                    # if debug['block_update']:
                    #     if b in self.world.to_update:
                    #         pygame.draw.rect(screen, (255, 0, 0),
                    #                          (round((x - self.player.x % 1) * size), round((y - self.player.y % 1) * size), size, size), 2)

                # if debug['chunk_border']:
                #     if y == 0 and (int(self.player.x) - x) % 40 == 0:  # draw chunk borders
                #         pygame.draw.line(screen, (255, 0, 0), ((40 - x) * size, 0), ((40 - x) * size, 800))

        # draw player
        pygame.draw.rect(screen, (255, 255, 0),
                         (size * 20, size * 20, size, size))

        # inventory ui
        self.draw_inventory(mouse_pos, mouse_press, mouse_click)

        self.pre_mouse = mouse_press

    def draw_inventory(self, mouse_pos, mouse_press, mouse_click):
        kmod = pygame.key.get_mods()
        if kmod & pygame.KMOD_CTRL:  # TODO debug menu
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


class GameRule:
    def __init__(self):
        self.creative = False  # allows infinite items
        self.allowFly = False  # disables movement checks
        self.keepInventory = False
