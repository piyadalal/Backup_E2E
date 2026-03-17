# encoding: utf-8

from .constants import *

from .base_stb_action import BaseStbAction
from .base_cherry_action import BaseCherryAction

from .action_00100_exit_to_fullscreen_video import ExitToFullscreenVideo as _00100
from .action_01400_global_navigation import GlobalNavigation as _01400
from .action_01403_tile_interaction import TileInteraction as _01403
from .action_04002_app_launch import AppLaunch as _04002
from .action_05348_assets_available_to_puchase import AssetsAvailableToPurchase as _05348


ACTIONS = {_00100.ACTION: _00100,
           _01400.ACTION: _01400,
           _01403.ACTION: _01403,
           _04002.ACTION: _04002,
           _05348.ACTION: _05348
           }




