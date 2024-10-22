from radiant.framework.server import PythonHandler
from foundation.utils import kafkalogs
import logging as logging_orig


########################################################################
class logging(PythonHandler):
    """"""

    # # ----------------------------------------------------------------------
    # def __getattr__(self, attribute):
        # """"""
        # instance = getattr(logging_orig, attribute)
        # if callable(instance):
            # def inset(*args, **kwargs):
                # """"""
                # instance(*args, **kwargs)
            # return inset
        # else:
            # return instance

    # ----------------------------------------------------------------------
    def warning(self, msg):
        """"""
        logging_orig.warning(msg)

