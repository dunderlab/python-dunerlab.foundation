from foundation.radiant.server import FrameworkAPI, render
from browser import html, document

# Material 3
# https://m3.material.io/develop/web
import material_3 as md


########################################################################
class BareMinimum(FrameworkAPI):

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """"""
        super().__init__(*args, **kwargs)
        self.add_css_file('styles/styles.css')

        # md_list = md.list()
        # self.body <= md_list
        # for i, service in enumerate(self.MyClass.services()):
            # list_item = md.list_item(headline=service, active=(i == 0))
            # md_list <= list_item

        self.body <= self.main_area()

        md_list = md.list()
        document.select_one('#radiant-drawer') <= md_list
        for i in range(10):
            list_item = md.list_item(headline=f'Item {i}', active=(i == 0))
            md_list <= list_item

        # button = md.text_button('Logging')
        # button.bind('click', self.send_log)
        # self.body <= button

        document.select_one('#radiant-main_area') <= html.PRE(self.swarm.get_join_command())

    # # ----------------------------------------------------------------------
    # def send_log(self, evt):
        # """"""
        # print('logging message')
        # self.logging.warning('logging message')

    # ----------------------------------------------------------------------
    def main_area(self):
        """"""
        return render('templates/main_area.html', context={})


if __name__ == '__main__':
    BareMinimum(logs=False)
