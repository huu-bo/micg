import random
import block


class generator:
    def __init__(self, seed, floor=10):
        self.seed = seed  # unused

        # holes in the floor are a feature

        # a start to generate more world next to
        self.generated = {
            -1: floor,
            0: floor,
            1: floor
        }

        self.min_gen = -1
        self.min_gen_value = self.generated[self.min_gen]
        self.min_gen_slope = 0

        self.max_gen = 1
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

    def set(self, x, y, value):
        if x // 40 in self.world:
            if 40 > y > 0:
                self.world[x // 40][y][x % 40] = value
        else:
            self.get(x, y)  # load the chunk
            self.world[x // 40][y][x % 40] = value
