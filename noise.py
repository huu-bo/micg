import os
import random
import block
import json


class generator:
    def __init__(self, seed, floor=10):
        self.seed = seed  # unused

        # holes in the floor are a feature

        # a start to generate more world next to
        self.generated = {
            19: floor,
            20: floor,
            21: floor,
        }

        self.min_gen = 19
        self.min_gen_value = self.generated[self.min_gen]
        self.min_gen_slope = 0

        self.max_gen = 21
        self.max_gen_value = self.generated[self.max_gen]
        self.max_gen_slope = 0

    def gen(self, i):
        if i in self.generated:
            return self.generated[i]
        else:
            # recursive, cannot teleport more than 999 blocks into not generated terrain
            if i < self.min_gen - 1:
                self.gen(i + 1)
            elif i > self.max_gen + 1:
                self.gen(i - 1)

            if i < self.min_gen:
                self.min_gen_slope = min(max(-1, self.min_gen_slope + int(random.random() * 3) - 1), 1)
                self.min_gen_value += self.min_gen_slope
                self.generated[i] = self.min_gen_value
                self.min_gen = i
            elif i > self.max_gen:
                self.max_gen_slope = min(max(-1, self.max_gen_slope + int(random.random() * 3) - 1), 1)
                self.max_gen_value += self.max_gen_slope
                self.generated[i] = self.max_gen_value
                self.max_gen = i

            return self.generated[i]


class world:
    def __init__(self, gen: generator):
        self.gen = gen
        self.world = {}

        self.blocks = block.load()

        self.to_update = []
        self.to_append = []

        self.filename = None

    def gen_chunk(self, x):
        # print('chunk', x)
        # if self.filename is not None:
        #     with open('saves/' + self.filename, 'r') as file:
        #         w = json.load(file)
        #         if x in w:
        #             return w[x]

        if x in self.world:
            return

        c = []
        for y in range(40):
            line = []
            for dx in range(40):
                line.append(block.block('air', self.blocks))
            c.append(line)

        for i in range(40):
            height = max(min(self.gen.gen(i + x * 40), 39), 0)
            for y in range(height):
                if y == 0:
                    b = block.block('bedrock', self.blocks)

                elif y == height - 1:
                    b = block.block('grass', self.blocks)
                elif y == height - 2:
                    b = block.block('grass', self.blocks)

                elif y == height - 3:
                    b = block.block('dirt', self.blocks)
                elif y == height - 4:
                    b = block.block('dirt', self.blocks)
                elif y == height - 5:
                    b = block.block('dirt', self.blocks)

                else:
                    b = block.block('stone', self.blocks)

                b.x = i + x * 40
                b.y = 39 - y

                b.support = height - y - 1
                b.on_floor = True

                c[39 - y][i] = b

        self.world[x] = c

    def get(self, x, y):
        if x // 40 in self.world:
            if 40 > y > 0:
                return self.world[x // 40][y][x % 40]
            else:
                return block.block('air', self.blocks)  # out of bounds
        else:
            self.gen_chunk(x // 40)
            return self.get(x, y)

    def set(self, x, y, value: block.block):
        value.x = x
        value.y = y

        if 39 > y > 1:
            self.to_append += [self.get(value.x - 1, value.y), self.get(value.x, value.y - 1),
                               self.get(value.x + 1, value.y), self.get(value.x, value.y + 1), value]

        if x // 40 in self.world:
            if 40 > y > 0:
                self.world[x // 40][y][x % 40] = value
        else:
            self.get(x, y)  # load the chunk
            self.world[x // 40][y][x % 40] = value

    def update(self, fast=False):
        # print(self.to_update)
        i = 0
        while len(self.to_update) and (i < 100 or fast):
            b = self.to_update[0]
            if b.y is not None:
                if b.y < 40:
                    self.to_append += b.update(self)
            self.to_update.pop(0)

            i += 1
        if not len(self.to_update):
            for b in self.to_append:
                if b not in self.to_update:
                    self.to_update.append(b)
            self.to_append = []

        # TODO: chunk unloading

    def save(self, file: str = None):
        if file is not None:
            self.filename = file

        if self.filename is not None:
            if self.filename not in os.listdir('saves'):
                with open('saves/' + self.filename, 'w') as file:
                    json.dump({}, file)

            with open('saves/' + self.filename, 'r') as file:
                w = json.load(file)
            w2 = {}
            for c in w:
                if c not in self.world:
                    w2[c] = w[c]
                else:
                    w2[c] = self.world[c]
            for c in self.world:
                if c not in w2:
                    w2[c] = self.world[c]
            with open('saves/' + self.filename, 'w') as file:
                w3 = {}
                for i in w2:
                    c = []
                    for j in w2[i]:
                        row = []
                        for b in j:
                            if type(b) != block.block:
                                print('error:', b)
                                row.append({'name': 'air', 'support': 0})
                            else:
                                row.append({'name': b.name, 'support': b.support})
                        c.append(row)
                    w3[i] = c
                json.dump(w3, file)

    def load(self, file: str = None):
        if file is not None:
            self.filename = file

        if self.filename is not None:
            with open('saves/' + self.filename, 'r') as file:
                raw = json.load(file)

                self.world = {}
                # self.world = {0: [[block.block('air', self.blocks)] * 40] * 40}
                for i in raw:
                    c = []
                    y = 0
                    for j in raw[i]:
                        row = []
                        x = 0
                        for ib in j:
                            b = block.block(ib['name'], self.blocks)
                            b.support = ib['support']

                            b.x = x
                            b.y = y

                            row.append(b)
                            x += 1
                        y += 1
                        c.append(row)
                    self.world[int(i)] = c

                print('loaded')
