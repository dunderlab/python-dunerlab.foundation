from foundation.radiant.server import FrameworkAPI, FigureStream
from foundation.radiant.utils import environ

import os
import json
from browser import document, html
import material_3 as md


########################################################################
class BareMinimumWorker(FrameworkAPI):

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """"""
        super().__init__(*args, **kwargs)

        green_button = md.text_button('Green')
        orange_button = md.text_button('Orange')

        small_button = md.text_button('Small')
        big_button = md.text_button('Big')

        green_button.bind('click', self.set_green)
        orange_button.bind('click', self.set_orange)

        small_button.bind('click', self.set_small)
        big_button.bind('click', self.set_big)

        self.body <= green_button
        self.body <= orange_button
        self.body <= small_button
        self.body <= big_button

        self.figurestream = FigureStream()

        container = html.DIV()
        container <= self.figurestream.container

        container.style = {
            'width': '100vw',
            'height': '100vh',
        }

        self.body <= container

    # ----------------------------------------------------------------------
    def set_green(self, evt):
        """"""
        self.logging.warning('Green')
        self.figurestream.set('color', 'C2')
        self.figurestream.set('dpi', '100')
        self.figurestream.set('width', '1000')
        self.figurestream.set('height', '500')
        self.figurestream.update()

    # ----------------------------------------------------------------------
    def set_orange(self, evt):
        """"""
        self.logging.warning('Orange')
        self.figurestream.set('color', 'C1')
        self.figurestream.set('dpi', '100')
        self.figurestream.set('width', '1000')
        self.figurestream.set('height', '500')
        self.figurestream.update()

    # ----------------------------------------------------------------------
    def set_small(self, evt):
        """"""
        self.figurestream.set('dpi', '100')
        self.figurestream.set('width', '1000')
        self.figurestream.set('height', '500')
        self.figurestream.update()

    # ----------------------------------------------------------------------
    def set_big(self, evt):
        """"""
        self.figurestream.set('dpi', '60')
        self.figurestream.set('width', '1000')
        self.figurestream.set('height', '500')
        self.figurestream.update()


if __name__ == '__main__':

    scripts = (
        ('/app/worker/stream.py', environ('STREAM', '5001')),
        ('stream.py', environ('STREAM', '5001')),
    )

    BareMinimumWorker(scripts=scripts)
