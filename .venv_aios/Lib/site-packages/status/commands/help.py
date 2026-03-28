#!/usr/bin/env python
# encoding: utf-8

import status.settings

class Help:
    def __init__(self):
        self.help = status.settings.help

    def print_help(self):
        print(self.help)

if __name__ == '__main__':
    pass