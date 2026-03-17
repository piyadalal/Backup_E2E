# encoding: utf-8

from __future__ import unicode_literals
from .base_stb_action import BaseStbAction, HEADING


class AppLaunch(BaseStbAction):

    ACTION = "04002"

    HEADINGS = [{HEADING: "App Name"}]


    # ------------------------------------------------------------------------
    # Properties that map to headings...

    @property
    def app_name(self):
        return self.action.get('app_name', '?')
