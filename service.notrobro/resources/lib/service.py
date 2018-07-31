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

class NotrobroPlayer(xbmc.Player):

    playing = False
    
    def __init__(self, *args, **kwargs):
        self.file = None
        self.intro_start_time = None
        self.intro_end_time = None
        self.outro_start_time = None
        self.outro_end_time = None
        logger.debug("NotrobroPlayer init...")

    def onAVChange(self):
        logger.debug("Player got a stream (audio or video)")

    def onAVStarted(self):
        if self.isPlayingVideo() and not self.playing:
            logger.debug("Kodi actually started playing a media item/displaying frames")
            self.playing = True
            self.file = self.getPlayingFile()            
            name, _ = os.path.splitext(self.file)
            try:
                with open(name + ".txt", "r") as f:
                    times = f.read()
            except Exception as ex:
                logger.debug(ex)
            intro = times.split("\n")[0].split()
            if intro[0] is not "None":
                self.intro_start_time = float(intro[0])
            if intro[1] is not "None":
                self.intro_end_time = float(intro[1])
            outro = times.split("\n")[1].split()
            if outro[0] is not "None":
                self.outro_start_time = float(outro[0])
            if outro[1] is not "None":
                self.outro_end_time = float(outro[1])

    def onPlayBackEnded(self):
        logger.debug("Playback has ended")

    def onPlayBackStopped(self):
        if not self.isPlayingVideo() and self.playing:
            logger.debug("Playback has been stopped")
            self.playing = False
            self.file = None
            self.intro_start_time = None
            self.intro_end_time = None
            self.outro_start_time = None
            self.outro_end_time = None
    
    def onPlayBackPaused(self):
        logger.debug("Playback has been paused")

    def onPlayBackResumed(self):
        logger.debug("Playback was resumed")

    def onPlayBackSeek(self, time, offset):
        logger.debug("User seeked to the given time")


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
            currentTime = player.getTime()
            if currentTime > player.intro_start_time and currentTime < player.intro_end_time and status_intro:
                status_intro = False
                response = DIALOG.yesno('Intro', 'Skip Intro?', yeslabel='Yes', nolabel='No')
                if response:
                    player.seekTime(player.intro_end_time - 1)

            if currentTime > player.outro_start_time and currentTime < player.outro_end_time and status_outro:
                status_outro = False
                response = DIALOG.yesno('Outro', 'Skip Outro?', yeslabel='Yes', nolabel='No')
                if response:
                    player.seekTime(player.outro_end_time - 1)
        else:
            status_intro = True
            status_outro = True

        player.onPlayBackStopped()
        