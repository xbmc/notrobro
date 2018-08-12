# -*- coding: utf-8 -*-

from resources.lib import kodiutils
from resources.lib.notrobroparser import NotrobroParser
from resources.lib.skip import Skip
import logging
import xbmc
import xbmcgui
import xbmcaddon
import os

ADDON = xbmcaddon.Addon()
DIALOG = xbmcgui.Dialog()
logger = logging.getLogger(ADDON.getAddonInfo('id'))


class NotrobroPlayer(xbmc.Player):

    def __init__(self, *args, **kwargs):
        logger.debug("NotrobroPlayer init...")
        self.skip = Skip("service-notrobro-buttonskip.xml", ADDON.getAddonInfo('path'), "default", "1080i")
        self._initialState()

    def onAVStarted(self):
        if self.isPlayingVideo() and not self.playing:
            logger.debug(
                "Kodi actually started playing a media item/displaying frames")
            self.playing = True
            self.file = self.getPlayingFile()
            parser = NotrobroParser(self.file, logger)
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
        self.seekTime(self.intro_end_time)

    @property
    def hasOutro(self):
        currentTime = self.getTime()
        return currentTime > self.outro_start_time and currentTime < self.outro_end_time

    def skipOutro(self):
        self.seekTime(self.outro_end_time)


class NotrobroMonitor(xbmc.Monitor):

    def __init__(self):
        logger.debug("NotrobroMonitor init...")

    # def onSettingsChanged(self):
    #     logger.debug("You can use this event to change any variables that depend on the addon settings")


def run():

    logger.info("Notrobro service started...")

    # Instantiate player event listener
    player = NotrobroPlayer()

    # Instantiate your monitor
    monitor = NotrobroMonitor()

    while not monitor.abortRequested():
        # Sleep/wait for abort for 1 second
        if monitor.waitForAbort(1):
            # Abort was requested while waiting. We should exit
            break

        if player.isPlayingVideo():
            if player.hasIntro:
                player.skip.show()
                if player.skip.isSkip is True:
                    player.skipIntro()
                    player.skip.isSkip = False
                    player.skip.close()

            if player.hasOutro:
                player.skip.show()
                if player.skip.isSkip is True:
                    player.skipOutro()
                    player.skip.isSkip = False
                    player.skip.close()
