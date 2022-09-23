import os
import json


def load(directory='blocks/'):
    out = {}
    for filename in os.listdir(directory):
        with open(directory + filename) as file:
            out[filename.split('.')[0]] = json.load(file)
    return out


class block:
    def __init__(self, name, blocks):
        self.blocks = blocks
        if name in blocks:
            if 'solid' in blocks[name]:  # there has got to be a better way to do this
                self.solid = blocks[name]['solid']
            else:
                print(name, "doesn't have property 'solid'")

            if 'render' in blocks[name]:
                self.render = blocks[name]['render']
            else:
                print(name, "doesn't have property 'render'")

            # optional parameters
            if 'color' in blocks[name]:
                self.color = tuple(blocks[name]['color'])
            else:
                self.color = (0, 255, 0)

            # template
            # if 'p' in blocks[name]:
            #     self.p = blocks[name]['p']
            # else:
            #     print(name, "doesn't have property 'p'")
        else:
            print('invalid block name:', name)

            self.solid = True
            self.render = True
