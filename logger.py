import pygame
import os
from time import gmtime, strftime

import io
import traceback


def log(message):
    print("\033[34m[" +
          strftime("%H:%M:%S", gmtime()) +
          " / " + str(pygame.time.get_ticks())
          + "] \033[32m[INFO]\033[0m "
          + "\33[36m(" + trace(True) + "\33[36m)\33[0m "
          + str(message))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [INFO] "
                + "(" + trace(False) + ") "
                + str(message)
                + "\n")


def warn(message):
    print("\033[34m["
          + strftime("%H:%M:%S", gmtime())
          + " / "
          + str(pygame.time.get_ticks())
          + "] \033[33m[WARN]\033[0m "
          + "\33[36m(" + trace(True) + "\33[36m) \33[0m"
          + str(message))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [WARN] "
                + "(" + trace(False) + ") "
                + str(message)
                + "\n")


def error(message):
    print("\033[34m["
          + strftime("%H:%M:%S", gmtime())
          + " / "
          + str(pygame.time.get_ticks())
          + "] \033[31m[ERROR] "
          + "\33[36m(" + trace(True) + "\33[36m) \33[31m"
          + str(message)
          + "\033[0m")

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write("["
                + strftime("%H:%M:%S", gmtime())
                + " / "
                + str(pygame.time.get_ticks())
                + "] [ERROR] "
                + "(" + trace(False) + ") "
                + str(message)
                + "\n")


def reset_log():
    if "latest.log" not in os.listdir('.'):
        with open("latest.log", 'w', encoding="UTF-8") as f:
            f.write("")
            return

    with open("latest.log", "w", encoding="UTF-8") as f2:
        f2.truncate()


def trace(colors: bool) -> str:
    trace = io.StringIO()
    traceback.print_stack(file=trace)
    trace_string = trace.getvalue()
    trace.close()
    trace_string_formatted = ''
    space = False
    even = True
    for c in trace_string:
        if c == '\n':
            if not even:
                trace_string_formatted += ';'
                even = True
            else:
                even = False

            trace_string_formatted += ' '
            space = True
        elif c == ' ':
            pass
        else:
            space = False

        if not space:
            trace_string_formatted += c

    trace_string_formatted2 = ''
    filename = ''
    state = 0
    line = ''
    i = 0
    while i < len(trace_string_formatted):
        c = trace_string_formatted[i]
        if state == 0:
            if c == '"':
                state = 1
        elif state == 1:
            if c != '"':
                filename += c
            else:
                if colors:
                    trace_string_formatted2 += '\33[94m'
                trace_string_formatted2 += os.path.basename(filename)
                filename = ''
                state = 2

        elif state == 2:
            j = i + 7
            while j < len(trace_string_formatted) and trace_string_formatted[j] != ',':
                line += trace_string_formatted[j]
                j += 1
            state = 3
            i = j

        elif state == 3:
            j = i + 4
            func = ''
            while j < len(trace_string_formatted) and trace_string_formatted[j] != ' ':
                func += trace_string_formatted[j]
                j += 1
            state = 4

            if colors:
                trace_string_formatted2 += '\33[0m'
            trace_string_formatted2 += f':{func}:{line}, '
            line = ''
        elif state == 4:
            if trace_string_formatted[i] == ';':  # TODO: you can't have a semicolon in the python
                trace_string_formatted2 += ';'
                state = 0

        i += 1
    trace_string_formatted2 = ''.join(trace_string_formatted2.split(';')[:-3])  # remove this function and log function
    trace_string_formatted2 = trace_string_formatted2[:-2]  # remove the last ', '
    # print(trace_string_formatted)
    # print(trace_string_formatted2)
    return trace_string_formatted2
