import xbmc
import xbmcgui
from platform import machine
import logging
import xbmcaddon

OS_MACHINE = machine()
ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))

class Skip(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        self.isSkip = False
        if OS_MACHINE[0:5] == 'armv7':
            xbmcgui.WindowXMLDialog.__init__(self)
        else:
            xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onClick(self, controlID):
        logger.debug('Notrobro onclick: ' + str(controlID))
        if controlID == 1:
            self.isSkip = True
        pass
