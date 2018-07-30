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
    
    def __init__(self, *args, **kwargs):
        self.intro_start_time = None
        self.intro_end_time = None
        self.outro_start_time = None
        self.outro_end_time = None
        logger.debug("NotrobroPlayer init...")

    def onAVChange(self):
        logger.debug("Player got a stream (audio or video)")

    def onAVStarted(self):
        logger.debug("Kodi actually started playing a media item/displaying frames")
    
    def onPlayBackEnded(self):
        logger.debug("Playback has ended")

    def onPlayBackStopped(self):
        logger.debug("Playback has been stopped")
    
    def onPlayBackPaused(self):
        logger.debug("Playback has been paused")

    def onPlayBackResumed(self):
        logger.debug("Playback was resumed")

    def onPlayBackSeek(self, time, offset):
        logger.debug("User seeked to the given time")

    def setTime(self, category, position, t_sec):
        if category is "intro":
            if position is 0:
                self.intro_start_time = t_sec
            if position is 1:
                self.intro_end_time = t_sec
        elif category is "outro":
            if position is 0:
                self.outro_start_time = t_sec
            if position is 1:
                self.outro_end_time = t_sec

    def getAll(self):
        output = " Notrobro Intro: Start Time- " + str(self.intro_start_time) + " End Time- " + str(self.intro_end_time) + " Outro: Start Time- " + str(self.outro_start_time) + " End Time- " + str(self.outro_end_time)
        return output

    

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

        if player.isPlaying():
                currentFile = player.getPlayingFile()
                logger.debug("Kodi is playing the file: %s" % currentFile)
                currentTime = player.getTime()
                logger.debug("Current player time is: %s %s" % (currentTime, type(currentTime)))
                name, _ = os.path.splitext(currentFile)
                try:
                    times = open(name + ".txt", "r").read().split("\n")
                    intro = times[0].split()
                    player.setTime("intro", 0, float(intro[0]))
                    player.setTime("intro", 1, float(intro[1]))
                    # response_intro 
                    if currentTime > float(intro[0]) and currentTime < float(intro[1]) and status_intro:
                        status_intro = False
                        response = DIALOG.yesno('Intro', 'Skip Intro?', yeslabel='Yes', nolabel='No')
                        if response:
                            player.seekTime(float(intro[1])-1)

                    outro = times[1].split()
                    player.setTime("outro", 0, float(outro[0]))
                    player.setTime("outro", 1, float(outro[1]))
                    #response outro
                    if currentTime > float(outro[0]) and currentTime < float(outro[1]) and status_outro:
                        status_outro = False
                        response = DIALOG.yesno('Outro', 'Skip Outro?', yeslabel='Yes', nolabel='No')
                        if response:
                            player.seekTime(float(outro[1])-1)

                    logger.debug(player.getAll())
                except:
                    logger.debug("Exception in Service Notrobro")
        else:
            status_intro = True
            status_outro = True

dfklnknkm



