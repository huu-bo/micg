import random
import math
import block

import logger
import net


class Random:
    m = 4294967296
    a = 1664525
    c = 1

    def __init__(self, seed: int):
        self.values = {
            -1: self._gen(seed + 1),
            0: seed,
            1: self._gen(seed)
        }

        self.min_gen = -1
        self.max_gen = 1

    def gen(self, i: int) -> float:
        if i in self.values:
            return self.values[i] / self.m
        else:
            if i > self.max_gen:
                for j in range(self.max_gen, i+2):
                    self.values[j+1] = self._gen(self.values[j])
            else:
                # print('less', self.min_gen, i-2, list(range(self.min_gen, i-2)))
                j = self.min_gen
                while j != i-1:
                    self.values[j-1] = self._gen(self.values[j])
                    j -= 1

            return self.values[i] / self.m

    def _gen(self, seed):
        seed = (self.a * seed + self.c) % self.m
        return seed

    def save(self):
        return {
            'values': self.values,
            'min': self.min_gen,
            'max': self.max_gen
        }

    def load(self, raw: dict):
        # json does not allow int indexes?
        self.values = {int(i): raw['values'][i] for i in raw['values']}
        self.min_gen = raw['min']
        self.max_gen = raw['max']


class generator:
    def __init__(self, seed, floor=10, clamp=None):
        self.seed = seed
        self.clamp = clamp

        self.generator = Random(self.seed)

        # holes in the floor are a feature

        # a start to generate more world next to
        self.generated = {i: floor for i in range(-10, 11)}

        self.min_gen = -10
        self.min_gen_value = self.generated[self.min_gen]
        self.min_gen_slope = 0

        self.max_gen = 10
        self.max_gen_value = self.generated[self.max_gen]
        self.max_gen_slope = 0

    def gen(self, i):
        if i in self.generated:
            return self.generated[i]
        else:
            if i < self.min_gen - 1:
                for x in range(self.min_gen, i - 1, -1):
                    self._gen(x)
            elif i > self.max_gen + 1:
                for x in range(self.max_gen, i + 1):
                    self._gen(x)
            else:
                self._gen(i)

            return self.generated[i]

    def _gen(self, i):
        if i in self.generated:
            return self.generated[i]
        else:
            if i == self.min_gen - 1:
                self.min_gen_slope = min(max(-1, self.min_gen_slope + int(self.generator.gen(i) * 3) - 1), 1)
                self.min_gen_value += self.min_gen_slope
                if self.clamp is not None:
                    self.min_gen_value = min(max(self.clamp[0], self.min_gen_value), self.clamp[1])
                    if self.min_gen_value in self.clamp:
                        self.min_gen_slope = 0
                self.generated[i] = self.min_gen_value
                self.min_gen = i
            elif i == self.max_gen + 1:
                self.max_gen_slope = min(max(-1, self.max_gen_slope + int(self.generator.gen(i) * 3) - 1), 1)
                self.max_gen_value += self.max_gen_slope
                if self.clamp is not None:
                    self.max_gen_value = min(max(self.clamp[0], self.max_gen_value), self.clamp[1])
                    if self.max_gen_value in self.clamp:
                        self.max_gen_slope = 0
                self.generated[i] = self.max_gen_value
                self.max_gen = i
            else:
                logger.warn(f"generating default value 10 for index {i}")
                self.generated[i] = 10

            if self.clamp is not None:
                self.generated[i] = min(max(self.clamp[0], self.generated[i]), self.clamp[1])

            return self.generated[i]

    def load(self, raw: dict):
        self.seed = raw['seed']

        self.generated = raw['gen']

        self.min_gen = raw['min_gen']
        self.min_gen_value = raw['min_gen_value']
        self.min_gen_slope = raw['min_gen_slope']

        self.max_gen = raw['max_gen']
        self.max_gen_value = raw['max_gen_value']
        self.max_gen_slope = raw['max_gen_slope']

        self.generator.load(raw['generator'])

    def save(self):
        return {
            'seed': self.seed,

            'gen': self.generated,

            'min_gen': self.min_gen,
            'min_gen_value': self.min_gen_value,
            'min_gen_slope': self.min_gen_slope,

            'max_gen': self.max_gen,
            'max_gen_value': self.max_gen_value,
            'max_gen_slope': self.max_gen_slope,

            'generator': self.generator.save()
        }


class Perlin_generator:
    def __init__(self, seed, scale):
        self.scale = scale

        generator = Random(seed)

        small_seed = generator._gen(seed + 2)
        self.small_generator = Random(small_seed)

        big_seed = generator._gen(seed + 4)
        self.big_generator = Random(big_seed)

    def gen(self, i):
        x = i // self.scale

        #  + self.big_generator.gen((x + 1) // self.scale) * self.scale * self.scale

        a = (i - x * self.scale) / self.scale
        out = self._interp(
            self.small_generator.gen(x) * self.scale,
            self.small_generator.gen(x + 1) * self.scale,
            a
        )

        i = i / self.scale
        x = int(i // self.scale)
        a = (i - x * self.scale) / self.scale
        out += self._interp(
            self.big_generator.gen(x) * self.scale,
            self.big_generator.gen(x + 1) * self.scale,
            a
        ) * self.scale
        return round(out)

    def _interp(self, a, b, x):
        mu = math.cos(x * math.pi) / 2 + .5
        return a * mu + b * (1 - mu)

    def save(self):
        return {
            'scale': self.scale,
            'big': self.big_generator.save(),
            'small': self.small_generator.save()
        }

    def load(self, raw: dict):
        self.scale = raw['scale']
        self.big_generator.load(raw['big'])
        self.small_generator.load(raw['small'])


class Perlin_filtered:
    def __init__(self, seed, scale, floor):
        self.perlin = Perlin_generator(seed, scale)

        self.min_gen = -20
        self.min_gen_value = floor
        self.max_gen = 20
        self.max_gen_value = floor

        self.values = {i: floor for i in range(-20, 21)}

    def gen(self, i):
        if i in self.values:
            return self.values[i]
        else:
            if i > self.max_gen:
                for j in range(self.max_gen, i+1):
                    d = self.perlin.gen(j)

                    if d == self.max_gen_value:
                        pass
                    elif d > self.max_gen_value:
                        self.max_gen_value += 1
                    else:
                        self.max_gen_value -= 1

                    self.max_gen += 1
                    self.values[self.max_gen] = self.max_gen_value
            else:
                if self.min_gen < i:
                    logger.warn(f'warning: discrepancy between min_gen and max_gen, returning min_gen_value')
                    return self.min_gen_value

                j = self.min_gen
                while j != i:
                    d = self.perlin.gen(j)

                    if d == self.min_gen_value:
                        pass
                    elif d > self.min_gen_value:
                        self.min_gen_value += 1
                    else:
                        self.min_gen_value -= 1

                    self.min_gen -= 1
                    self.values[self.min_gen] = self.min_gen_value

                    j -= 1

            return self.values[i]

    def load(self, raw: dict):
        self.min_gen = raw['min_gen']
        self.min_gen_value = raw['min_gen_value']

        self.max_gen = raw['max_gen']
        self.max_gen_value = raw['max_gen_value']

        self.perlin.load(raw['generator'])

    def save(self):
        return {
            'min_gen': self.min_gen,
            'min_gen_value': self.min_gen_value,

            'max_gen': self.max_gen,
            'max_gen_value': self.max_gen_value,

            'generator': self.perlin.save()
        }


class world:
    def __init__(self, seed: int, floor: int, game, gen_new=True, server=None, serving=False):
        self.gen = Perlin_filtered(seed, 40, floor)
        self.temperature_gen = generator(seed, 20, (-50, 50))
        self.cloud_gen = generator(seed + 1, floor=0, clamp=(0, 5))
        self.world = {}

        self.game = game

        self.gen_new = gen_new
        self.server = server
        self.serving = serving

        self.blocks = block.load()

        self.to_update = []  # TODO: make this update entire chunks instead of blocks
        self.to_append = []

        self.filename = None

        if self.serving and self.server is None:
            assert False, 'you did it wrong'
        if self.server is not None:
            if type(self.server) is not net.Server and type(self.server) is not net.client:
                print(self.server)
                raise ValueError('???????????????????')

    def gen_chunk(self, x, y):
        # print('chunk', x)
        # if self.filename is not None:
        #     with open('saves/' + self.filename, 'r') as file:
        #         w = json.load(file)
        #         if x in w:
        #             return w[x]

        if (x, y) in self.world:
            return

        c = []
        for dy in range(40):
            line = []
            for dx in range(40):
                line.append(block.block('air', self.blocks))
            c.append(line)

        if y <= 0:
            temperature = self.temperature_gen.gen(x) + y

            for i in range(40):
                height = self.gen.gen(i + x * 40) + y * 40
                for dy in range(min(height, 40)):
                    if temperature > 40:
                        bn = 'sand'
                    elif temperature > 30:
                        bn = 'dirt'
                    elif temperature > 3:
                        bn = 'grass'
                    elif temperature > 0:
                        bn = 'dirt'
                    else:
                        bn = 'ice'

                    if dy == 0 and y == 0:
                        b = block.block('bedrock', self.blocks)

                    elif dy == height - 1:
                        b = block.block(bn, self.blocks)
                    elif dy == height - 2:
                        b = block.block(bn, self.blocks)

                    elif dy == height - 3:
                        if temperature > 41:
                            bn = 'sand'
                        elif temperature > -10:
                            bn = 'dirt'
                        else:
                            bn = 'ice'

                        b = block.block(bn, self.blocks)
                    elif dy == height - 4:
                        if temperature > 42:
                            bn = 'sand'
                        elif temperature > -20:
                            bn = 'dirt'
                        else:
                            bn = 'ice'

                        b = block.block(bn, self.blocks)
                    elif dy == height - 5:
                        if temperature > 43:
                            bn = 'sand'
                        elif temperature > -30:
                            bn = 'dirt'
                        else:
                            bn = 'ice'

                        b = block.block(bn, self.blocks)

                    else:
                        if height - dy - 1 > 100 and random.random() > max(.99, 1 - (height - dy - 101) / 10):
                            b = block.block('diamond', self.blocks)
                        elif height - dy - 1 > 100 and random.random() > .9 - (height - dy - 101) / 50:
                            b = block.block('coal', self.blocks)
                        else:
                            b = block.block('stone', self.blocks)

                    b.x = i + x * 40
                    b.y = 39 - dy + y * 40

                    b.support = height - dy - 1
                    b.on_floor = True

                    c[39 - dy][i % 40] = b

            for i in range(40):
                if y * 40 == -800:
                    if c[0][i % 40].name == 'air':
                        for j in range(self.cloud_gen.gen(i + x * 40)):
                            c[j][i % 40] = block.block('cloud', self.blocks)

        self.world[(x, y)] = c

    def get(self, x, y):
        if (x // 40, y // 40) in self.world:
            return self.world[(x // 40, y // 40)][y % 40][x % 40]
        else:
            if self.gen_new:
                self.gen_chunk(x // 40, y // 40)
            else:
                if self.server is not None:
                    self.server.get_chunk(x // 40, y // 40)
                else:
                    raise ValueError('if world.gen_new == False, you should give net.client')
            if (x // 40, y // 40) in self.world:
                return self.get(x, y)
            else:
                return block.block('air', self.blocks)

    def set(self, x, y, value: block.block, update=True, block_update=True):
        value.x = x
        value.y = y

        if y < 40:
            if self.gen_new and block_update:
                self.to_append += [self.get(value.x - 1, value.y), self.get(value.x, value.y - 1),
                                   self.get(value.x + 1, value.y), self.get(value.x, value.y + 1),

                                   self.get(value.x + 1, value.y + 1), self.get(value.x + 1, value.y - 1),
                                   self.get(value.x - 1, value.y + 1), self.get(value.x - 1, value.y - 1), value]

            if (x // 40, y // 40) in self.world:
                self.world[(x // 40, y // 40)][y % 40][x % 40] = value
                if self.server is not None and self.serving and update:
                    self.server.send_all('AP' + str(x) + ' ' + str(y) + ' ' + value.name)
                elif self.server is not None and not self.serving and update:  # multiplayer client
                    self.server.set_block(x, y, value)
            else:
                self.get(x, y)  # load the chunk

    def update(self, tick: int) -> int:
        update_amount = 0
        for b in self.to_update:
            if b.y is not None:
                if b.y < 40:
                    if b.last_update_tick != tick:
                        update_amount += 1
                        self.to_append += b.update(self)
                        b.last_update_tick = tick

        self.to_update = self.to_append
        self.to_append = []

        return update_amount

        # TODO: chunk unloading

    def save(self):
        w = {}
        for i in self.world:
            c = []
            for j in self.world[i]:
                row = []
                for b in j:
                    if type(b) != block.block:
                        logger.warn(f"block {b} in chunk {i[0]}, {i[1]} is not a Block")
                        # print('error:', b)
                        row.append({'name': 'air', 'support': 0})
                    else:
                        row.append({'name': b.name, 'support': b.support})
                c.append(row)
            w[str(i[0]) + ' ' + str(i[1])] = c

        w['data'] = {}
        w['data']['gen'] = self.gen.save()

        return w

    def load(self, raw: dict):
        # TODO: this is really slow
        self.world = {}
        logger.log(f'world chunks size {len(raw.keys())}')
        for i in raw:
            if i != 'data':
                c = []
                y = int(i.split(' ')[1]) * 40
                for j in raw[i]:
                    row = []
                    x = int(i.split(' ')[0]) * 40
                    for ib in j:
                        b = block.block(ib['name'], self.blocks)
                        b.support = ib['support']

                        b.x = x
                        b.y = y

                        b.on_floor = True

                        row.append(b)
                        x += 1
                    y += 1
                    c.append(row)
                # print(i)
                self.world[(int(i.split(' ')[0]), int(i.split(' ')[1]))] = c
            else:
                self.gen.load(raw[i]['gen'])
                # TODO: also load other players if multiplayer server

        logger.log('Loaded!')

    def serialize_chunk(self, x, y):
        out = ''
        if (x, y) not in self.world:
            self.gen_chunk(x, y)
        chunk = self.world[(x, y)]
        for row in chunk:
            for b in row:
                out += b.name + ','
        return out

    def deserialise_chunk(self, data: str):
        chunk = []
        split = data.split(' ')
        if len(split) != 3:
            raise Exception('chunk incorrectly formatted')
        x = 0
        y = 0
        row = []
        for b in split[2].split(','):
            b = block.block(b, self.blocks)
            b.x = x
            b.y = y
            row.append(b)
            x += 1

            if x == 40:
                chunk.append(row)
                row = []
                x = 0
                y += 1

        logger.warn(f'deserialised chunk {int(split[0])} {int(split[1])}, size: {len(chunk[0])}, {len(chunk)}')

        self.world[(int(split[0]), int(split[1]))] = chunk

        # warn(self.world[(int(split[0]), int(split[1]))][39][20].name)
        # warn(str([c for c in self.world]))
