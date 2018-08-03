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

class NotrobroUtils():
    def __init__(self, file):
        self.times = self.getTimings(file)

    def getTimings(self, file):
        name, _ = os.path.splitext(file)        
        timings = []
        try:
            with open(name + ".txt", "r") as f:
                timings = f.readlines()
        except Exception as ex:
            logger.debug(ex)
        return timings

    def getIntro(self):
        try:
            intro = self.times[0].strip().split()
            if intro[0] is not "None":
                return float(intro[0]), float(intro[1])
            else:
                return None, None
        except Exception as ex:
            logger.debug(ex)
            return None, None

    def getOutro(self):
        try:
            outro = self.times[1].strip().split()
            if outro[0] is not "None":
                return float(outro[0]), float(outro[1])
            else:
                return None, None
        except Exception as ex:
            logger.debug(ex)
            return None, None

class NotrobroPlayer(xbmc.Player):

    playing = False
    
    def __init__(self, *args, **kwargs):
        logger.debug("NotrobroPlayer init...")
        self.initialState()

    def onAVChange(self):
        logger.debug("Player got a stream (audio or video)")

    def onAVStarted(self):
        if self.isPlayingVideo() and not self.playing:
            logger.debug("Kodi actually started playing a media item/displaying frames")
            self.playing = True
            self.file = self.getPlayingFile()
            utils = NotrobroUtils(self.file)
            self.intro_start_time, self.intro_end_time = utils.getIntro()
            self.outro_start_time, self.outro_end_time = utils.getOutro()            

    def onPlayBackEnded(self):
        logger.debug("Playback has ended")

    def onPlayBackStopped(self):
        if not self.isPlayingVideo() and self.playing:
            logger.debug("Playback has been stopped")
            self.initialState()
    
    def onPlayBackPaused(self):
        logger.debug("Playback has been paused")

    def onPlayBackResumed(self):
        logger.debug("Playback was resumed")

    def onPlayBackSeek(self, time, offset):
        logger.debug("User seeked to the given time")

    def initialState(self):
        self.playing = False
        self.file = None
        self.intro_start_time = None
        self.intro_end_time = None
        self.outro_start_time = None
        self.outro_end_time = None

    def hasIntro(self):
        currentTime = self.getTime()
        if currentTime > self.intro_start_time and currentTime < self.intro_end_time:
            return True
        return False

    def skipIntro(self):
        self.seekTime(self.intro_end_time - 1)

    def hasOutro(self):
        currentTime = self.getTime()
        if currentTime > self.outro_start_time and currentTime < self.outro_end_time:
            return True
        return False 

    def skipOutro(self):
        self.seekTime(self.outro_end_time - 1)


class NotbroMonitor(xbmc.Monitor):

    def __init__(self):
        logger.debug("NotrobroMonitor init...")

    def onSettingsChanged(self):
        logger.debug("You can use this event to change any variables that depend on the addon settings")


def run():

    logger.info("Notrobro service started...")

    # Instantiate player event listener
    player = NotrobroPlayer()

    # Instantiate your monitor
    monitor = NotbroMonitor()
    
    status_intro = True
    status_outro = True

    while not monitor.abortRequested():
        # Sleep/wait for abort for 1 second
        if monitor.waitForAbort(1):
            # Abort was requested while waiting. We should exit
            break

        player.onAVStarted()

        if player.isPlayingVideo():
            if player.hasIntro() and status_intro:
                status_intro = False
                response = DIALOG.yesno('Intro', 'Skip Intro?', yeslabel='Yes', nolabel='No')
                if response:
                    player.skipIntro()

            if player.hasOutro() and status_outro:
                status_outro = False
                response = DIALOG.yesno('Outro', 'Skip Outro?', yeslabel='Yes', nolabel='No')
                if response:
                    player.skipOutro()
        else:
            status_intro = True
            status_outro = True

        player.onPlayBackStopped()
        