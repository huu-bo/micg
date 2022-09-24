import random
import block


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
            # recursive, cannot teleport more than 40 * 999 blocks into not generated terrain
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

    def gen_chunk(self, x):
        c = []
        for y in range(40):
            line = []
            for dx in range(40):
                line.append(block.block('air', self.blocks))
            c.append(line)

        for i in range(40):
            for y in range(self.gen.gen(i + x * 40)):
                if y == 0:
                    b = block.block('bedrock', self.blocks)
                else:
                    b = block.block('grass', self.blocks)

                b.x = i
                b.y = 39 - y

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

    def update(self):
        # print(self.to_update)
        while len(self.to_update):
            b = self.to_update[0]
            if b.y is not None:
                if b.y < 40:
                    self.to_append += b.update(self)
            self.to_update.pop(0)
        for b in self.to_append:
            if b not in self.to_update:
                self.to_update.append(b)
        self.to_append = []
