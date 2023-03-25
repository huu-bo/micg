import os
import json


def load(directory='blocks/'):
    out = {}
    for filename in os.listdir(directory):
        with open(directory + filename) as file:
            out[filename.split('.')[0]] = json.load(file)
    return out


class block:
    def __init__(self, name, blocks):
        self.blocks = blocks
        self.support = 0
        self.name = name

        self.x = None  # should be set by noise.world.set()
        self.y = None

        self.on_floor = False  # solid block under this block, only used if self.h_support

        if name in blocks:
            if 'solid' in blocks[name]:  # there has got to be a better way to do this
                self.solid = blocks[name]['solid']
            else:
                print(name, "doesn't have property 'solid'")

            if 'render' in blocks[name]:
                self.render = blocks[name]['render']
            else:
                print(name, "doesn't have property 'render'")

            # optional parameters
            if 'color' in blocks[name]:
                self.color = tuple(blocks[name]['color'])
            else:
                self.color = (0, 255, 0)

            if 'max support' in blocks[name]:
                self.max_support = blocks[name]['max support']
            else:
                self.max_support = 10

            if 'gravity' in blocks[name]:
                self.gravity = blocks[name]['gravity']
            else:
                self.gravity = True

            if 'h support' in blocks[name]:
                self.h_support = blocks[name]['h support']
            else:
                self.h_support = False

            # template
            # if 'p' in blocks[name]:
            #     self.p = blocks[name]['p']
            # else:
            #     print(name, "doesn't have property 'p'")
        else:
            print('invalid block name:', name)

            self.solid = True
            self.render = True

            self.color = (255, 30, 30)
            self.max_support = 1

            self.gravity = True
            self.h_support = False

    def update(self, world):
        if self.x is None or not self.solid or not self.gravity:
            return []

        pre_x = self.x
        pre_y = self.y

        moved = False

        if world.get(self.x, self.y + 1).solid and not self.on_floor and self.gravity:
            moved = True
            self.on_floor = world.get(self.x, self.y + 1).on_floor
        if (world.get(self.x - 1, self.y).solid or world.get(self.x + 1, self.y).solid) and\
                not world.get(self.x, self.y + 1).solid:
            self.on_floor = world.get(self.x - 1, self.y).on_floor or world.get(self.x + 1, self.y).on_floor

            if not self.on_floor and self.h_support:
                self.support += 1

        if (not world.get(self.x, self.y + 1).solid) and\
                ((not world.get(self.x - 1, self.y).solid) and (not world.get(self.x + 1, self.y).solid) or not self.h_support):
            world.set(self.x, self.y, block('air', self.blocks))
            self.y += 1
            world.set(self.x, self.y, self)
            moved = True
        else:
            if world.get(self.x, self.y - 1).solid:
                if self.support != world.get(self.x, self.y - 1).support + 1:
                    moved = True
                self.support = world.get(self.x, self.y - 1).support + 1

            elif world.get(self.x + 1, self.y).solid and self.h_support:  # TODO: directional
                if self.support != world.get(self.x + 1, self.y).support + 1:
                    moved = True
                self.support = world.get(self.x + 1, self.y).support + 1

            elif world.get(self.x - 1, self.y).solid and self.h_support:
                if self.support != world.get(self.x - 1, self.y).support + 1:
                    moved = True
                self.support = world.get(self.x - 1, self.y).support + 1

            else:
                if self.support != 0:
                    moved = True
                self.support = 0

            if self.support > self.max_support:
                if not world.get(self.x + 1, self.y + 1).solid:
                    world.set(self.x, self.y, block('air', self.blocks))
                    self.y += 1
                    self.x += 1
                    world.set(self.x, self.y, self)
                    moved = True
                elif not world.get(self.x - 1, self.y + 1).solid:
                    world.set(self.x, self.y, block('air', self.blocks))
                    self.y += 1
                    self.x -= 1
                    world.set(self.x, self.y, self)
                    moved = True

        if moved:
            if self.solid:
                assert self.name != 'air', 'wtf'
                y = self.y + 1
                if world.get(self.x, self.y - 1).solid:
                    self.support = world.get(self.x, self.y - 1).support + 1
                else:
                    self.support = 0
                support = self.support
                while world.get(self.x, y).solid and y < 39:
                    support += 1
                    world.get(self.x, y).support = support
                    y += 1
                    if y > 40:
                        break
            # update neighbouring blocks
            return [world.get(self.x - 1, self.y), world.get(self.x, self.y - 1),
                    world.get(self.x + 1, self.y), world.get(self.x, self.y + 1),

                    world.get(self.x - 1, self.y - 1), world.get(self.x + 1, self.y - 1),
                    world.get(self.x - 1, self.y + 1), world.get(self.x + 1, self.y + 1),

                    world.get(pre_x - 1, pre_y),
                    world.get(pre_x + 1, pre_y), world.get(pre_x, pre_y - 1),

                    world.get(pre_x - 1, pre_y - 1), world.get(pre_x + 1, pre_y - 1),
                    world.get(pre_x - 1, pre_y + 1), world.get(pre_x + 1, pre_y + 1),

                    self]
        else:
            return []


def craft(pi, b, f, blocks, game, amount=1):
    if b not in blocks:
        game.error(f"block {b}, does not exist")
        return
    if 'craft' not in blocks[b]:
        game.error(f"can't craft {b}")
        return
    if f not in blocks[b]['craft']:
        game.error(f"can't craft {b} from {f}")
        return
    if pi[f] < amount * blocks[b]['craft'][f]:
        game.error(f"not enough {f}, amount: {pi[f]}, amount needed: {amount * blocks[b]['craft'][f]}")
        return

    pi[f] -= amount * blocks[b]['craft'][f]
    pi[b] += amount
    return


def recipies(b, blocks):
    if b not in blocks:
        return False
    if 'craft' not in blocks[b]:
        return False
    return blocks[b]['craft']


def color(b, blocks):
    if b in blocks:
        if 'color' in blocks[b]:
            c = blocks[b]['color']
        else:
            c = (0, 255, 0)
    else:
        c = (255, 10, 10)
    return c
