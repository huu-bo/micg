import pygame
import game
import logger

size = game.size

pygame.init()
screen = pygame.display.set_mode((size * 40, size * 42))

g = game.Game(screen)
clock = pygame.time.Clock()
run = True

logger.reset_log()
g.load_config()
logger.log("Game Initialized")

while run:
    clock.tick(60)

    try:
        run = g.update()
    except Exception as e:
        logger.exception('while updating game', e)
        logger.log('exiting')

        try:
            g.save_config()  # TODO: if this were to crash due to invalid state, the config would be lost, make some kind of copy before saving
            g.quit()
        except Exception as e:
            logger.exception('while updating game and exiting raised another exception', e)

        pygame.quit()
        exit(1)

    g.draw()
    pygame.display.update()

g.save_config()

g.quit()
pygame.quit()
logger.log('Game quit successfully')
