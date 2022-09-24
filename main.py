import pygame

import block
import noise
import math
pygame.init()

VERSION = 'Alpha 3'
size = 20

gen = noise.generator(10)
world = noise.world(gen)
blocks = world.blocks

world.gen_chunk(0)

px = 0.  # player position
py = 0.
pxv = 0.  # player velocity
pyv = 0.

pf = False  # player not on the ground
ps = 'grass'  # player block selection

pi = {}  # player inventory
for b in blocks:
    if blocks[b]['solid']:
        pi[b] = 0


def die():
    global px, py, pxv, pyv
    px = 0
    py = 0
    pxv = 0
    pyv = 0


font = pygame.font.SysFont('ubuntu', int(size / 1.1))
run = True
clock = pygame.time.Clock()
screen = pygame.display.set_mode((size * 40, size * 40 + size * 2))
pygame.display.set_caption('Mine and Craft game ' + VERSION)
while run:
    clock.tick(60)
    dt = 60 / max(clock.get_fps(), 0.001)  # delta time
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    key = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    mouse_press = pygame.mouse.get_pressed(5)
    if key[pygame.K_d] or key[pygame.K_RIGHT]:
        pxv += .1
    if key[pygame.K_a] or key[pygame.K_LEFT]:
        pxv -= .1

    if key[pygame.K_w] or key[pygame.K_UP]:
        if pf:
            pyv = -.55

    if mouse_press[2]:
        if world.get(math.floor(mouse_pos[0] / size + px), mouse_pos[1] // size).solid:
            pi[world.get(math.floor(mouse_pos[0] / size + px), mouse_pos[1] // size).name] += 1

        b = block.block('air', blocks)
        world.set(math.floor(mouse_pos[0] / size + px), mouse_pos[1] // size, b)
        world.to_update.append(b)
    if not world.get(math.floor(mouse_pos[0] / size + px), mouse_pos[1] // size).solid:
        if mouse_press[0]:
            if pi[ps] > 0:
                b = block.block(ps, blocks)
                world.set(math.floor(mouse_pos[0] / size + px), mouse_pos[1] // size, b)
                world.to_update.append(b)

                pi[ps] -= 1

    # player physics
    px += pxv
    while world.get(math.ceil(px) + 20, int(py) + 1).solid:
        px -= .01
        pxv = 0
    while world.get(math.floor(px) + 20, int(py) + 1).solid:
        px += .01
        pxv = 0
    pxv /= 2

    py += pyv
    pf = False
    pyv += .1

    for i in range(int(pyv * 10)):
        py += pyv / int(pyv * 10)

        if world.get(math.floor(px) + 20, int(py) + 1).solid or world.get(math.ceil(px) + 20, int(py) + 1).solid:
            pyv = 0
            break

    while world.get(math.floor(px) + 20, int(py) + 1).solid or world.get(math.ceil(px) + 20, int(py) + 1).solid:
        pyv = 0
        py -= .01
        pf = True

    hit = False
    while world.get(math.floor(px) + 20, int(py) - 0).solid or world.get(math.ceil(px) + 20, int(py)).solid:
        pyv = 0
        py += .01
        hit = True
    if hit:
        py -= .01

    if py > 60:
        die()

    for y in range(min(800 // size, 40)):
        for x in range(min(800 // size, 40)):
            b = world.get(x + math.floor(px), y)
            if b is not None:
                if b.render:
                    pygame.draw.rect(screen, b.color, (round((x - px % 1) * size), y * size, size, size))
                    # screen.blit(font.render(str(b.support), True, (100, 0, 0)), (round((x - px % 1) * size), y * size))
                    # screen.blit(font.render(str(b.y), True, (100, 0, 0)), (round((x - px % 1) * size), y * size))

                # if b in world.to_update:
                #     pygame.draw.rect(screen, (255, 0, 0), (round((x - px % 1) * size), y * size, size, size), 2)

            # if y == 0 and (int(px) - x) % 40 == 0:  # draw chunk borders
            #     pygame.draw.line(screen, (255, 0, 0), ((40 - x) * size, 0), ((40 - x) * size, 800))

    pygame.draw.rect(screen, (255, 255, 0), (screen.get_size()[0] // 2, round(py * size), size, size))

    if len(world.to_update) > 100:
        screen.blit(font.render('processing ' + str(len(world.to_update)), True, (255, 255, 255)), (0, 0))

    i = 0
    for b in pi:
        if 'color' in blocks[b]:
            c = blocks[b]['color']
        else:
            c = (0, 255, 0)

        pygame.draw.rect(screen, c, (i * size, size * 40, size, size))
        screen.blit(font.render(str(pi[b]), True, (255, 255, 255)), (i * size, size * 41))

        if ps == b:
            pygame.draw.rect(screen, ((255 - c[0]) % 255, (255 - c[1]) % 255, (255 - c[2]) % 255),
                             (i * size, size * 40, size, size), 1)

        if size * 40 < mouse_pos[1] < size * 41:
            if i * size < mouse_pos[0] < (i + 1) * size:
                pygame.draw.rect(screen, ((255 - c[0]) % 255, (255 - c[1]) % 255, (255 - c[2]) % 255), (i * size, size * 40, size, size), 2)

                if mouse_press[0]:
                    ps = b

                    pygame.draw.rect(screen, (255, 255, 255), (i * size, size * 40, size, size), 3)

        i += 1

    world.update()

    pygame.display.update()

pygame.quit()
