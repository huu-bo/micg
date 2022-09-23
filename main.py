import pygame

import block
import noise
import math
pygame.init()

VERSION = 'Alpha 1'
size = 20

gen = noise.generator(10)
world = noise.world(gen)
blocks = world.blocks

world.gen_chunk(0)

px = 0.
py = -20.
pxv = 0.
pyv = 0.

pf = False  # player not on the ground

run = True
clock = pygame.time.Clock()
screen = pygame.display.set_mode((800, 800))
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
    if key[pygame.K_d]:
        pxv += .1
    if key[pygame.K_a]:
        pxv -= .1

    if key[pygame.K_w]:
        if pf:
            pyv = -.55

    if mouse_press[2]:
        world.set(int(mouse_pos[0] / size + px), mouse_pos[1] // size, block.block('air', blocks))
    if not world.get(int(mouse_pos[0] / size + px), mouse_pos[1] // size).solid:
        if mouse_press[0]:
            world.set(int(mouse_pos[0] / size + px), mouse_pos[1] // size, block.block('grass', blocks))

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
    while world.get(math.floor(px) + 20, int(py) + 1).solid or world.get(math.ceil(px) + 20, int(py) + 1).solid:
        pyv = 0
        py -= .01
        pf = True

    hit = False
    while world.get(math.floor(px) + 20, int(py) - 0) == 1 or world.get(math.ceil(px) + 20, int(py)) == 1:
        pyv = 0
        py += .01
        hit = True
    if hit:
        py -= .01

    for y in range(min(800 // size, 40)):
        for x in range(min(800 // size, 40)):
            b = world.get(x + math.floor(px), y)
            if b is not None:
                if b.render:
                    pygame.draw.rect(screen, b.color, (round((x - px % 1) * size), y * size, size, size))

            # if y == 0 and (int(px) - x) % 40 == 0:  # draw chunk borders
            #     pygame.draw.line(screen, (255, 0, 0), ((40 - x) * size, 0), ((40 - x) * size, 800))

    pygame.draw.rect(screen, (255, 255, 0), (400, round(py * size), size, size))

    pygame.display.update()

pygame.quit()
