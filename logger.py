import pygame
import os
from datetime import datetime

import io
import traceback


def _log(message, colors, t):  # TODO: american english VS british english
    if t not in [0, 1, 2]:
        raise ValueError('unknown logger._log type')

    out = ''
    if colors:
        out += '\33[34m'
    out += '['
    out += (datetime.now().strftime("%H:%M:%S.%f")[:-4] + ' / ' + str(pygame.time.get_ticks())).ljust(19, ' ')
    out += '] '

    if t == 0:
        if colors:
            out += '\033[32m'
        out += '[INFO] '
    elif t == 1:
        if colors:
            out += '\033[33m'
        out += '[WARN] '
    elif t == 2:
        if colors:
            out += '\033[31m'
        out += '[ERROR]'

    if colors:
        out += '\033[0m'
    out += ' '

    if colors:
        "\33[36m"
    out += '('
    out += trace(colors, -4)
    if colors:
        '\33[36m'
    out += ')'
    if colors:
        out += '\33[0m'
    out += ' '  # TODO: (how) should they all be aligned

    if colors and t == 2:
        out += '\33[31m'
    out += str(message)
    if colors and t == 2:
        out += '\33[0m'

    return out


def log(message):
    print(_log(message, True, 0))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write(_log(message, False, 0) + '\n')


def warn(message):
    print(_log(message, True, 1))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write(_log(message, False, 1) + "\n")


def error(message):
    print(_log(message, True, 2))

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write(_log(message, False, 2) + "\n")


def exception(message, e):
    string = ''.join(traceback.format_exception(e, e, e.__traceback__))
    string = ''.join(['    ' + line + '\n' for line in string.split('\n')])[:-6]
    print(_log('Exception occurred ' + message, True, 2) + '\n' + string)

    with open('latest.log', 'a', encoding="UTF-8") as f:
        f.write(_log('Exception occurred ' + message, False, 2) + "\n" + string + '\n')


def reset_log():
    if "latest.log" not in os.listdir('.'):
        with open("latest.log", 'w', encoding="UTF-8") as f:
            f.write("")
            return

    with open("latest.log", "w", encoding="UTF-8") as f:
        f.truncate()


def trace(colors: bool, remove: int = -3) -> str:
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
    trace_string_formatted2 = ''.join(trace_string_formatted2.split(';')[:remove])  # remove this function and log function
    trace_string_formatted2 = trace_string_formatted2[:-2]  # remove the last ', '
    # print(trace_string_formatted)
    # print(trace_string_formatted2)
    return trace_string_formatted2
