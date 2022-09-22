import random


class generator:
    def __init__(self, seed, floor=10):
        self.seed = seed

        self.generated = {
            -1: floor,
            0: floor,
            1: floor
        }

        self.min_gen = -1
        self.min_gen_value = self.generated[self.min_gen]

        self.max_gen = 1
        self.max_gen_value = self.generated[self.max_gen]

    def gen(self, i):
        if i in self.generated:
            return self.generated[i]
        else:
            if i < self.min_gen - 1:
                self.gen(i + 1)
            elif i > self.max_gen + 1:
                self.gen(i - 1)

            if i < self.min_gen:
                self.min_gen_value += int(random.random() * 3) - 1
                self.generated[i] = self.min_gen_value
                self.min_gen = i
            elif i > self.max_gen:
                self.max_gen_value += int(random.random() * 3) - 1
                self.generated[i] = self.max_gen_value
                self.max_gen = i

            return self.generated[i]


class world:
    def __init__(self, gen: generator):
        self.gen = gen
        self.world = {}

    def gen_chunk(self, x):
        c = []
        for y in range(40):
            line = []
            for dx in range(40):
                line.append(0)
            c.append(line)

        for i in range(40):
            for y in range(self.gen.gen(i + x * 40)):
                c[39 - y][i] = 1

        self.world[x] = c

    def get(self, x, y):
        if x // 40 in self.world:
            if 40 > y > 0:
                return self.world[x // 40][y][x % 40]
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
