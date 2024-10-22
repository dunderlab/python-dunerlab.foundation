# FigureStream replace any Figure object
from figurestream import FigureStream
import time

import numpy as np
from datetime import datetime
import sys

port = sys.argv[1]


########################################################################
class Stream(FigureStream):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.axis = self.add_subplot(111)
        self.x = np.array(range(100))
        self.t0 = time.time()
        self.y = [self.t0] * 100

        self.axis.set_title('FigureStream')
        self.axis.set_xlabel('Time [s]')
        self.axis.set_ylabel('Amplitude')

        self.axis.set_ylim(0, 60)
        #axis.set_xlim(0, 3)

        # Lines objects
        self.line1, *_ = self.axis.plot(self.x, np.zeros(self.x.size))

        self.stream()

    # ----------------------------------------------------------------------
    def stream(self):
        """"""
        while True:
            self.y.pop(0)
            self.y.append(1 / (time.time() - self.t0))
            self.t0 = time.time()

            self.line1.set_ydata(self.y)
            self.feed()

    # ----------------------------------------------------------------------
    def interact_color(self, color):
        """"""
        self.line1.set_color(color)
        # self.update(props)


if __name__ == '__main__':
    Stream(host='0.0.0.0', port=port)
