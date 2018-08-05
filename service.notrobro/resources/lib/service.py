# -*- coding: utf-8 -*-

from resources.lib import kodiutils
import logging
import xbmc
import xbmcgui
import xbmcaddon
import os

ADDON = xbmcaddon.Addon()
DIALOG = xbmcgui.Dialog()
logger = logging.getLogger(ADDON.getAddonInfo('id'))

class NotrobroParser():
    def __init__(self, file):
        self.times = self.getTimings(file)

    @staticmethod
    def getTimings(file):
        name, _ = os.path.splitext(file)
        fname = name + ".edl"
        timings = []
        if os.path.exists(fname):
            with open(fname, "r") as f:
                timings = f.readlines()
        return timings

    @property 
    def intro(self):
        try:
            intro = self.times[0].strip().split()
            return float(intro[0]), float(intro[1])
        except Exception as ex:
            logger.debug(ex)
        return None, None

    @property
    def outro(self):
        try:
            outro = self.times[1].strip().split()
            return float(outro[0]), float(outro[1])
        except Exception as ex:
            logger.debug(ex)
        return None, None

class NotrobroPlayer(xbmc.Player):

    def __init__(self, *args, **kwargs):
        logger.debug("NotrobroPlayer init...")
        self._initialState()

    def onAVStarted(self):
        if self.isPlayingVideo() and not self.playing:
            logger.debug("Kodi actually started playing a media item/displaying frames")
            self.playing = True
            self.file = self.getPlayingFile()
            parser = NotrobroParser(self.file)
            self.intro_start_time, self.intro_end_time = parser.intro
            self.outro_start_time, self.outro_end_time = parser.outro            

    def onPlayBackEnded(self):
        logger.debug("Playback has ended")
        self._initialState()

    def onPlayBackStopped(self):
        if not self.isPlayingVideo() and self.playing:
            logger.debug("Playback has been stopped")
            self._initialState()

    def _initialState(self):
        self.playing = False
        self.file = None
        self.intro_start_time = None
        self.intro_end_time = None
        self.outro_start_time = None
        self.outro_end_time = None

    @property
    def hasIntro(self):
        currentTime = self.getTime()
        return currentTime > self.intro_start_time and currentTime < self.intro_end_time

    def skipIntro(self):
        self.seekTime(self.intro_end_time - 1)

    @property
    def hasOutro(self):
        currentTime = self.getTime()
        return currentTime > self.outro_start_time and currentTime < self.outro_end_time

    def skipOutro(self):
        self.seekTime(self.outro_end_time - 1)


class NotrobroMonitor(xbmc.Monitor):

    def __init__(self):
        logger.debug("NotrobroMonitor init...")

    def onSettingsChanged(self):
        logger.debug("You can use this event to change any variables that depend on the addon settings")


def run():

    logger.info("Notrobro service started...")

    # Instantiate player event listener
    player = NotrobroPlayer()

    # Instantiate your monitor
    monitor = NotrobroMonitor()
    
    status_intro = True
    status_outro = True

    while not monitor.abortRequested():
        # Sleep/wait for abort for 1 second
        if monitor.waitForAbort(1):
            # Abort was requested while waiting. We should exit
            break

        if player.isPlayingVideo():
            if player.hasIntro and status_intro:
                status_intro = False
                response = DIALOG.yesno('Intro', 'Skip Intro?', yeslabel='Yes', nolabel='No')
                if response:
                    player.skipIntro()

            if player.hasOutro and status_outro:
                status_outro = False
                response = DIALOG.yesno('Outro', 'Skip Outro?', yeslabel='Yes', nolabel='No')
                if response:
                    player.skipOutro()
        else:
            status_intro = True
            status_outro = True        