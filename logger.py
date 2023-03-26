import pygame
import os
from time import gmtime, strftime


def log(message):
    print("\033[34m[" +
          strftime("%H:%M:%S", gmtime()) +
          " / " + str(pygame.time.get_ticks())
          + "] \033[32m[INFO]\033[0m "
          + str(message))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [INFO] "
                + str(message)
                + "\n")


def logw(message, location):
    print("\033[34m[" +
          strftime("%H:%M:%S", gmtime()) +
          " / " + str(pygame.time.get_ticks())
          + "] \033[32m[INFO]\033[36m (" + str(location) + ")\033[0m "
          + str(message))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [INFO] "
                + "(" + str(location) + ") "
                + str(message)
                + "\n")


def warn(message):
    print("\033[34m["
          + strftime("%H:%M:%S", gmtime())
          + " / "
          + str(pygame.time.get_ticks())
          + "] \033[33m[WARN]\033[0m "
          + str(message))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [WARN] "
                + str(message)
                + "\n")


def warnw(message, location):
    print("\033[34m["
          + strftime("%H:%M:%S", gmtime())
          + " / "
          + str(pygame.time.get_ticks())
          + "] \033[33m[WARN]\033[36m (" + str(location) + ")\033[0m "
          + str(message))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [WARN] "
                + "(" + str(location) + ") "
                + str(message)
                + "\n")

def error(message):
    print("\033[34m["
          + strftime("%H:%M:%S", gmtime())
          + " / "
          + str(pygame.time.get_ticks())
          + "] \033[31m[ERROR] "
          + str(message)
          + "\033[0m")

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [ERROR] "
                + str(message)
                + "\n")

def errorw(message, location):
    print("\033[34m["
          + strftime("%H:%M:%S", gmtime())
          + " / "
          + str(pygame.time.get_ticks())
          + "] \033[31m[ERROR]\033[36m (" + str(location) + ")\033[31m "
          + message
          + "\033[0m")

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [ERROR] "
                + "(" + str(location) + ") "
                + message
                + "\n")


def resetLog():
    if "latest.log" not in os.listdir('.'):
        with open("latest.log", 'w', encoding="UTF-8") as f:
            f.write("")
            return

    with open("latest.log", "w", encoding="UTF-8") as f2:
        f2.truncate()
