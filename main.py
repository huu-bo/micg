import pygame

import block
import noise
import math
pygame.init()

# hold control for debug menu
VERSION = 'Alpha 6'
size = 20
creative = True

gen = noise.generator(10)
world = noise.world(gen)
blocks = world.blocks

px = 0.  # player position
py = 0.
pxv = 0.  # player velocity
pyv = 0.

pf = False  # player not on the ground
ps = 'grass'  # player block selection

pi = {}  # player inventory
for b in blocks:
    if blocks[b]['solid']:
        pi[b] = 99 * creative

debug = {
    'chunk_border': False,
    'block_update': False,
    'block_stress': False,
    'player_info': False,
    'to_update': False,
    'fast_physics': False,
    'prompt': False  # cannot start out True
}
prompt_text = ''


def die():
    global px, py, pxv, pyv
    global pi, blocks

    px = 0
    py = 0

    for b in blocks:
        if blocks[b]['solid']:
            pi[b] = 0


font = pygame.font.SysFont('ubuntu', int(size / 1.1))
run = True
clock = pygame.time.Clock()
screen = pygame.display.set_mode((size * 40, size * 40 + size * 2))
pygame.display.set_caption('Mine and Craft game ' + VERSION)
pre_mouse_press = [False] * 5
while run:
    clock.tick(60)
    dt = 60 / max(clock.get_fps(), 0.001)  # delta time
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN and debug['prompt']:
            if event.key == pygame.K_BACKSPACE:
                prompt_text = prompt_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                debug['prompt'] = False
                prompt_text = ''
            elif event.key != pygame.K_RETURN:
                prompt_text += event.unicode
            else:
                # saving and loading
                if prompt_text.split(' ')[0] == '/load':
                    if len(prompt_text.split(' ')) == 1:
                        world.load()
                    elif len(prompt_text.split(' ')) == 2:
                        world.load(prompt_text.split(' ')[1] + '.json')
                elif prompt_text.split(' ')[0] == '/save':
                    if len(prompt_text.split(' ')) == 1:
                        world.save()
                    elif len(prompt_text.split(' ')) == 2:
                        world.save(prompt_text.split(' ')[1] + '.json')
                # crafting
                elif prompt_text.split(' ')[0] == '/craft':
                    print('craft')
                    if len(prompt_text.split(' ')) == 3:
                        block.craft(pi, prompt_text.split(' ')[1], prompt_text.split(' ')[2], blocks)
                    elif len(prompt_text.split(' ')) == 4:
                        block.craft(pi, prompt_text.split(' ')[1], prompt_text.split(' ')[2], blocks,
                                    amount=int(prompt_text.split(' ')[3]))
                    else:
                        print('aaaa')

                if creative:  # debug and cheats
                    if prompt_text.split(' ')[0] == '/kill':
                        die()
                    elif prompt_text.split(' ')[0] == '/give':
                        if len(prompt_text.split(' ')) == 3:
                            if prompt_text.split(' ')[1] in blocks:
                                pi[prompt_text.split(' ')[1]] += int(prompt_text.split(' ')[2])
                    elif prompt_text.split(' ')[0] == '/tp':
                        if len(prompt_text.split(' ')) == 2:
                            px = float(prompt_text.split(' ')[1])
                            py = 39 - world.gen.gen(int(px)) - 40
                    elif prompt_text.split(' ')[0] == '/set':
                        if len(prompt_text.split(' ')) == 4:
                            world.set(int(prompt_text.split(' ')[1]), int(prompt_text.split(' ')[2]),
                                      block.block(prompt_text.split(' ')[3], blocks))

                prompt_text = ''
                debug['prompt'] = False

    if not debug['prompt']:
        key = pygame.key.get_pressed()
    kmod = pygame.key.get_mods()
    mouse_pos = pygame.mouse.get_pos()
    mouse_press = pygame.mouse.get_pressed(5)
    mouse_click = [mouse_press[i] and not pre_mouse_press[i] for i in range(5)]
    pre_mouse_press = mouse_press
    if key[pygame.K_d] or key[pygame.K_RIGHT]:
        pxv += .1
    if key[pygame.K_a] or key[pygame.K_LEFT]:
        pxv -= .1

    if key[pygame.K_w] or key[pygame.K_UP]:
        if pf:
            pyv = -.55

    if key[pygame.K_t]:
        debug['prompt'] = True
    if key[pygame.K_SLASH] and not debug['prompt']:
        debug['prompt'] = True
        prompt_text += '/'

    if mouse_pos[1] < size * 40:
        if mouse_press[2]:
            if world.get(math.floor(mouse_pos[0] / size + px), math.floor(mouse_pos[1] / size + py) - 20).solid:
                pi[world.get(math.floor(mouse_pos[0] / size + px), math.floor(mouse_pos[1] / size + py) - 20).name] += 1

            b = block.block('air', blocks)
            world.set(math.floor(mouse_pos[0] / size + px), math.floor(mouse_pos[1] / size + py) - 20, b)
            world.to_update.append(b)
        if not world.get(math.floor(mouse_pos[0] / size + px), math.floor(mouse_pos[1] / size + py) - 20).solid:
            if mouse_press[0]:
                if pi[ps] > 0:
                    b = block.block(ps, blocks)
                    world.set(math.floor(mouse_pos[0] / size + px), math.floor(mouse_pos[1] / size + py) - 20, b)
                    world.to_update.append(b)

                    if mouse_pos[1] < size * 40:
                        pi[ps] -= 1

    # player physics
    px += pxv
    while world.get(math.ceil(px) + 20, math.floor(py) + 1).solid:
        px -= .01
        pxv = 0
    while world.get(math.floor(px) + 20, math.floor(py) + 1).solid:
        px += .01
        pxv = 0
    pxv /= 2

    pf = False
    pyv += .1

    for i in range(10):
        py += pyv / 10

        if world.get(math.floor(px) + 20, math.floor(py) + 1).solid or world.get(math.ceil(px) + 20, math.floor(py) + 1).solid:
            pyv = 0
            break

    while world.get(math.floor(px) + 20, math.floor(py) + 1).solid or world.get(math.ceil(px) + 20, math.floor(py) + 1).solid:
        pyv = 0
        py -= .01
        pf = True

    hit = False
    while world.get(math.floor(px) + 20, math.floor(py) - 0).solid or world.get(math.ceil(px) + 20, math.floor(py)).solid:
        pyv = 0
        py += .01
        hit = True
    if hit:
        py -= .01

    if py > 60:
        die()

    for y in range(min(800 // size, 40)):
        for x in range(min(800 // size, 40)):
            b = world.get(x + math.floor(px), y + math.floor(py) - 20)
            if b is not None:
                if b.render:
                    pygame.draw.rect(screen, b.color, (round((x - px % 1) * size), round((y - py % 1) * size), size, size))
                    if debug['block_stress']:
                        screen.blit(font.render(str(b.support), True, (100, 0, 0)),
                                    (round((x - px % 1) * size), round((y - py % 1) * size)))

                if debug['block_update']:
                    if b in world.to_update:
                        pygame.draw.rect(screen, (255, 0, 0), (round((x - px % 1) * size), round((y - py % 1) * size), size, size), 2)

            if debug['chunk_border']:
                if y == 0 and (int(px) - x) % 40 == 0:  # draw chunk borders
                    pygame.draw.line(screen, (255, 0, 0), ((40 - x) * size, 0), ((40 - x) * size, 800))

    # draw player
    pygame.draw.rect(screen, (255, 255, 0), (screen.get_size()[0] // 2, screen.get_size()[1] // 2 - size, size, size))

    if len(world.to_update) > 100 or debug['to_update']:
        screen.blit(font.render('processing ' + str(len(world.to_update)), True, (255, 255, 255)), (10, 10 + 75 * debug['player_info']))

    # inventory ui, will not be drawn if debug menu or chat is active
    if not kmod & pygame.KMOD_LCTRL and not debug['prompt']:
        i = 0
        for b in pi:
            if b in blocks:
                if 'color' in blocks[b]:
                    c = blocks[b]['color']
                else:
                    c = (0, 255, 0)
            else:
                c = (255, 10, 10)

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

    world.update(fast=debug['fast_physics'])

    if debug['player_info']:
        screen.blit(font.render(f'Position: {round(px, 4)} {round(py, 3)}', True, (255, 255, 255)), (10, 5))
        screen.blit(font.render(f'Motion: {round(pxv, 4)} {round(pyv, 3)}', True, (255, 255, 255)), (10, 25))
        screen.blit(font.render(f'onGround: {pf}', True, (255, 255, 255)), (10, 55))

    if debug['prompt']:
        if pygame.time.get_ticks() // 200 % 2 == 0:
            text = str(prompt_text)
        else:
            text = str(prompt_text) + '_'
        screen.blit(font.render(text, True, (255, 255, 255), (0, 0, 0)), (10, size * 40))

    if kmod & pygame.KMOD_LCTRL:  # debug menu
        i = 0
        for d in debug:
            if debug[d]:
                c = (0, 255, 0)
            else:
                c = (255, 0, 0)
            if size * 40 < mouse_pos[1] < size * 41:
                if i * size * 6 < mouse_pos[0] < (i + 1) * size * 6:
                    if debug[d]:
                        c = (200, 255, 200)
                    else:
                        c = (255, 100, 100)
                    if mouse_click[0]:
                        c = (255, 255, 255)
                        debug[d] = not debug[d]
            pygame.draw.rect(screen, c, (i * size * 6, size * 40, size * 6, size), 2)

            screen.blit(font.render(d, True, (255, 255, 255)), (i * size * 6, size * 40))

            i += 1

    pygame.display.update()

pygame.quit()
world.save()
