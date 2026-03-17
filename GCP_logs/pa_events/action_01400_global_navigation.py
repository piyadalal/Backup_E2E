# encoding: utf-8

from __future__ import unicode_literals
from .base_stb_action import BaseStbAction, HEADING


class GlobalNavigation(BaseStbAction):

    ACTION = "01400"

    HEADINGS = [{HEADING: "Move"}]

    @property
    def origin(self):
        return self.action.get('orig', {})

    @property
    def origin_screen_name(self):
        return self.origin.get('screenname')

    @property
    def origin_x(self):
        return self.origin.get('tilePositionX')

    @property
    def origin_y(self):
        return self.origin.get('tilePositionY')

    @property
    def destination(self):
        return self.action.get('dest')

    @property
    def destination_screen_name(self):
        return self.destination.get('screenname')

    @property
    def destination_x(self):
        return self.destination.get('tilePositionX')

    @property
    def destination_y(self):
        return self.destination.get('tilePositionY')

    # ------------------------------------------------------------------------
    # Properties that map to headings...

    @property
    def move(self):
        origin_x_y = f" ({self.origin_x},{self.origin_y})" if self.origin_x and self.origin_y else ''
        destination_x_y = f" ({self.destination_x},{self.destination_y})" if self.destination_x and self.destination_y else ''
        return (f"{self.origin_screen_name}{origin_x_y}"
                "\n->\n"
                f"{self.destination_screen_name}{destination_x_y}")
