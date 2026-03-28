#!/usr/bin/env python
# encoding: utf-8

import status.settings

class Version:
    def __init__(self):
        self.major_version = status.settings.major_version
        self.minor_version = status.settings.minor_version
        self.patch_version = status.settings.patch_version
        self.name = status.settings.app_name
        self.app_version_string = self.name + " " + self.major_version + "." + self.minor_version + "." + self.patch_version
        self.version_string = self.major_version + "." + self.minor_version + "." + self.patch_version

    def print_version(self):
        print(self.app_version_string)

    def get_version(self):
        return self.version_string

if __name__ == '__main__':
    pass