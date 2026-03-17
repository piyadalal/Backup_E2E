# encoding: utf-8

from __future__ import unicode_literals
from .base_stb_action import BaseStbAction, HEADING


class TileInteraction(BaseStbAction):

    ACTION = "01403"

    HEADINGS = [{HEADING: "Signpost Info"}]

    @property
    def signpost(self):
        return self.action.get('signpost')

    @property
    def tile_name(self):
        return self.action.get('tileName')

    @property
    def tile_position_x(self):
        return self.action.get('tilePositionX')

    @property
    def tile_position_y(self):
        return self.action.get('tilePositionY')

    # ------------------------------------------------------------------------
    # Properties that map to headings...

    @property
    def signpost_info(self):
        return ("{signpost} ({x},{y}) \n"
                "{name}".format(signpost=self.signpost,
                                x=self.tile_position_x,
                                y=self.tile_position_y,
                                name=self.tile_name))
