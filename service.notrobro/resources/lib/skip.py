import xbmc
import xbmcgui
import logging
import xbmcaddon

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))

class Skip(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.isVisible = False

    def show_with_callback(self, callback):
        self.callback = callback
        if self.get_isVisible() is False:
            self.show()
            self.set_isVisible()

    def onClick(self, controlID):
        logger.debug('Notrobro onclick: ' + str(controlID))
        if controlID == 1:
            self.callback()

    def get_isVisible(self):
        return self.isVisible    

    def set_isVisible(self):
        self.isVisible = not self.isVisible
