import xbmc
import xbmcgui
import logging
import xbmcaddon

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))

class Skip(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def show_with_callback(self, callback):
    	self.callback = callback
    	self.show()

    def onClick(self, controlID):
        logger.debug('Notrobro onclick: ' + str(controlID))
        if controlID == 1:
            self.callback()
        pass
