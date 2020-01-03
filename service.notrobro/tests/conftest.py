import sys
import xbmcvfs as fxbmc

module = type(sys)('xbmcvfs')
module.exists = fxbmc.exists
module.File = fxbmc.File
sys.modules['xbmcvfs'] = module
