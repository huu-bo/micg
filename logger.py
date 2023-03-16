import pygame
import os
from time import gmtime, strftime


def log(message):
    print("[" + strftime("%H:%M:%S", gmtime()) + " / " + str(pygame.time.get_ticks()) + "] " + message)

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("[" + strftime("%H:%M:%S", gmtime()) + " / " + str(pygame.time.get_ticks()) + "] " + message + "\n")


def resetLog():
    if "latest.log" not in os.listdir('.'):
        with open("latest.log", 'w', encoding="UTF-8") as f:
            f.write("")
            return

    with open("latest.log", "w", encoding="UTF-8") as f2:
        f2.truncate()