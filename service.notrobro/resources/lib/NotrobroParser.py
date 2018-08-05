# -*- coding: utf-8 -*-

import os


class NotrobroParser():
    def __init__(self, file, logger):
        self.logger = logger
        self.times = self.getTimings(file)

    def getTimings(self, file):
        name, _ = os.path.splitext(file)
        file_name = name + ".edl"
        timings = []
        if os.path.exists(file_name):
            with open(file_name, "r") as f:
                timings = f.readlines()
        else:
            self.logger.debug("Timings file not found.")
        return timings

    @property
    def intro(self):
        try:
            intro = self.times[0].strip().split()
            return float(intro[0]), float(intro[1])
        except Exception as ex:
            self.logger.debug(ex)
        return None, None

    @property
    def outro(self):
        try:
            outro = self.times[1].strip().split()
            return float(outro[0]), float(outro[1])
        except Exception as ex:
            self.logger.debug(ex)
        return None, None
