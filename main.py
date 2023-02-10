import pygame

import block
import noise
import math
import net
pygame.init()

# hold control for debug menu
VERSION = 'Alpha 6'
size = 20
creative = True
username = 'test1'

# todolist:
#     multiplayer implement:
#           inventory
#           clients know about other clients
#     saving:
#           save player inventory
#           save player position
#     add chat
#     add typing
#     client deserializes chunks in a separate thread
#     give packets a timestamp and if packet is old recalculate for example player position,
#       there should be a time limit to stop hackers sending ancient packets to teleport
#     change block update algorithm to be faster
#     maybe not use a hashmap for noise.world
#     when client joins let them know about the other clients

gen = noise.generator(10)
world = noise.world(gen)
blocks = world.blocks

px = 0.  # player position
py = 0.
pxv = 0.  # player velocity
pyv = 0.

pf = False  # player falling
ps = 'grass'  # player block selection

pi = {}  # player inventory
for b in blocks:
    if blocks[b]['solid']:
        pi[b] = 0 + creative * 100

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
prompt_history = []

online = False
server = False
connection = None

crafting = False


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
            elif prompt_text[0] != '/':
                prompt_history.insert(0, username + ': ' + prompt_text)
                prompt_text = ''
                debug['prompt'] = False
            else:
                c = prompt_text.split(' ')
                # saving and loading
                if c[0] == '/load':
                    if len(c) == 1:
                        world.load()
                    elif len(c) == 2:
                        world.load(c[1] + '.json')
                elif c[0] == '/save':
                    if len(c) == 1:
                        world.save()
                    elif len(c) == 2:
                        world.save(c[1] + '.json')
                # crafting
                elif c[0] == '/craft':
                    if len(c) == 3:
                        block.craft(pi, c[1], c[2], blocks)
                    elif len(c) == 4:
                        block.craft(pi, c[1], c[2], blocks, amount=int(c[3]))
                    else:
                        print('incorrect amount of options')
                # multiplayer
                elif c[0] == '/join':
                    online = True
                    server = False

                    if connection is not None:
                        connection.exit()

                    if len(c) == 2:
                        connection = net.client(world, ip=c[1])
                    else:
                        connection = net.client(world)

                    world = noise.world(noise.generator(0), gen_new=False, server=connection)
                    connection.world = world  # if we don't do this the net has a pointer to the old world
                elif c[0] == '/host':
                    online = True
                    server = True

                    if connection is not None:
                        connection.exit()

                    if len(c) == 2:
                        connection = net.server(world, ip=c[1])
                    else:
                        connection = net.server(world)

                    world = noise.world(noise.generator(0), gen_new=True, server=connection, serving=True)
                    connection.world = world  # if we don't do this the net has a pointer to the old world

                if creative:  # debug and cheats
                    if c[0] == '/kill':
                        die()
                    elif c[0] == '/give':
                        if len(c) == 3:
                            if c[1] in blocks:
                                pi[c[1]] += int(c[2])
                    elif c[0] == '/tp':
                        if len(c) == 2:
                            px = float(c[1])
                            py = 39 - world.gen.gen(int(px)) - 40
                    elif c[0] == '/set':
                        if len(c) == 4:
                            world.set(int(c[1]), int(c[2]),
                                      block.block(c[3], blocks))
                    elif c[0] == '/locate':
                        m = 5000
                        if len(c) == 3:
                            m = 100000
                        if len(c) == 2 or len(c) == 3:
                            found = False
                            i = 0
                            while not found:
                                value = world.gen.gen(i)
                                if i % 100 == 0:
                                    print(('#' * value) + (' ' * (int(c[1]) - value)) + '|')
                                if value >= int(c[1]):
                                    print(('#' * value) + (' ' * (int(c[1]) - value)) + '|')
                                    found = True
                                if i > m:
                                    print('could not find')
                                    break
                                i += 1
                            if found:
                                px = i
                                py = -(world.gen.gen(i))
                        elif len(c) == 1:
                            m = 0
                            i = 0
                            while i < 5000:
                                value = world.gen.gen(i)
                                m = max(value, m)
                                i += 1
                            print('max', m)

                prompt_text = ''
                debug['prompt'] = False

    if not debug['prompt']:
        key = pygame.key.get_pressed()
    kmod = pygame.key.get_mods()
    mouse_pos = pygame.mouse.get_pos()
    mouse_press = pygame.mouse.get_pressed(5)
    mouse_click = [mouse_press[i] and not pre_mouse_press[i] for i in range(5)]
    pre_mouse_press = mouse_press

    if server or not online or True:
        if key[pygame.K_d] or key[pygame.K_RIGHT]:
            pxv = .1 + creative * 1
        if key[pygame.K_a] or key[pygame.K_LEFT]:
            pxv = -(.1 + creative * 1)

        if key[pygame.K_w] or key[pygame.K_UP]:
            if pf or creative:
                pyv = -.55

        if key[pygame.K_s] and creative:
            pyv = .55
    elif server and online:
        pass

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
    py += pyv

    pxv /= 1.1
    pyv /= 1.1
    if not creative:
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

    if online and not server:
        px, py = connection.update(key, world)
        px -= 20
    elif online and server:
        connection.update(world)

    if py > 60:
        die()

    # world rendering
    for y in range(41):
        for x in range(41):
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

    # draw online players
    if online and server:
        for p in connection.players:
            # pygame.draw.rect(screen, (255, 0, 0), ((p.x - px) * size, (p.y - py) * size, size, size))
            # pygame.draw.rect(screen, (255, 0, 0), (round(p.x * size), p.y * size, size, size))
            pygame.draw.rect(screen, (255, 0, 0), (round((p.x - px) * size), round((p.y - py + 20) * size), size, size))
    elif online and not server:
        for i in connection.players:
            p = connection.players[i]
            pygame.draw.rect(screen, (255, 0, 0), (round((p.x - px) * size), round((p.y - py + 20) * size), size, size))

    if len(world.to_update) > 100 or debug['to_update']:
        screen.blit(font.render('processing ' + str(len(world.to_update)), True, (255, 255, 255)), (10, 10 + 75 * debug['player_info']))

    # inventory ui, will not be drawn if debug menu or chat is active
    pygame.draw.rect(screen, (0, 0, 0), (0, size * 40, size * 40, size * 2))  # black background
    if not kmod & pygame.KMOD_LCTRL and not debug['prompt']:
        if not crafting:
            i = 0
            for b in pi:
                c = block.color(b, blocks)

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
            pygame.draw.rect(screen, (255, 255, 255), (i * size, size * 40, size, size))
            if size * 40 < mouse_pos[1] < size * 41:
                if i * size < mouse_pos[0] < (i + 1) * size:
                    pygame.draw.rect(screen, (0, 0, 0), (i * size, size * 40, size, size), 2)

                    if mouse_press[0]:
                        crafting = True

                        pygame.draw.rect(screen, (0, 0, 0), (i * size, size * 40, size, size), 3)
        else:
            i = 0
            for b in pi:
                if b in blocks:
                    bc = block.color(b, blocks)
                    r = block.recipies(b, blocks)
                    if r:
                        for f in r:
                            c = block.color(f, blocks)

                            pygame.draw.rect(screen, c, (i * size, size * 40, size, size))  # craft this block
                            pygame.draw.rect(screen, bc, (i * size, size * 41, size, size))  # from this block

                            if size * 40 < mouse_pos[1] < size * 42:
                                if i * size < mouse_pos[0] < (i + 1) * size:
                                    pygame.draw.rect(screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 2)

                                    if kmod & pygame.KMOD_SHIFT and mouse_press[0]:
                                        block.craft(pi, b, f, blocks)
                                        pygame.draw.rect(screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 3)
                                    elif mouse_click[0]:
                                        block.craft(pi, b, f, blocks)
                                        pygame.draw.rect(screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 3)

                                        crafting = False
                                    elif mouse_click[2]:
                                        block.craft(pi, b, f, blocks, amount=5)
                                        pygame.draw.rect(screen, (0, 0, 0), (i * size, size * 40, size, size * 2), 3)

                                        crafting = False

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

        y = size * 39
        for text in prompt_history:
            screen.blit(font.render(text, True, (255, 255, 255), (0, 0, 0)), (10, y))
            y -= size

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
if connection is not None:
    connection.exit()
