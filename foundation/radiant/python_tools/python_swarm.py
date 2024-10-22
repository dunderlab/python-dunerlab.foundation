from radiant.framework.server import PythonHandler
from foundation.utils.swarm import Swarm


admin = Swarm()


########################################################################
class swarm(PythonHandler):
    """"""

    # ----------------------------------------------------------------------
    def services(self):
        """"""
        return admin.services

    # ----------------------------------------------------------------------
    def get_join_command(self):
        """"""
        return admin.get_join_command()

    # # ----------------------------------------------------------------------

    # def pitagoras(self, a, b):
        # """"""
        # return math.sqrt(a**2 + b**2)

    # # ----------------------------------------------------------------------

    # def test(self):
        # """"""
        # return True

