from m5stack import *
from m5stack_ui import *
from uiflow import *
import ujson
import network
import urequests
import time
import sys


class Foundation:

    def __init__(self, ip, token=None):
        """"""
        # Initialize screen and labels
        screen = M5Screen()
        screen.clean_screen()
        screen.set_screen_bg_color(0x000000)

        self.header = {'content-type': 'application/json', 'Authorization': "Bearer {}".format(token)}
        self.ip = ip
        self.set_ui()

    def connect_to_wifi(self, ssid, password):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            wlan.connect(ssid, password)
            while not wlan.isconnected():
                pass

    def set_ui(self):
        """"""
        self.labels = {}

        self.labels['header'] = M5Label("Starting...", font=FONT_MONT_16)
        self.labels['header'].set_align(1, x=10, y=5)
        self.labels['header'].set_text_color(0x00ff00)

        self.labels['local'] = M5Label("")
        self.labels['local'].set_align(1, x=10, y=20)
        self.labels['local'].set_text_color(0x00ff00)

        self.labels['local diff'] = M5Label("")
        self.labels['local diff'].set_align(1, x=10, y=40)
        self.labels['local diff'].set_text_color(0x00ff00)

        self.labels['server'] = M5Label("")
        self.labels['server'].set_align(1, x=10, y=60)
        self.labels['server'].set_text_color(0x00ff00)

        self.labels['server diff'] = M5Label("Local diff:")
        self.labels['server diff'].set_align(1, x=10, y=80)
        self.labels['server diff'].set_text_color(0x00ff00)

        self.labels['status'] = M5Label("")
        self.labels['status'].set_align(1, x=10, y=110)
        self.labels['status'].set_text_color(0x00ff00)

        self.labels['message'] = M5Label("")
        self.labels['message'].set_align(1, x=10, y=120)
        self.labels['message'].set_text_color(0x00ff00)

    def write(self, label, text):
        """"""
        self.labels[label].set_text(text)

    def ping(self):
        """"""
        timestamp = time.ticks_ms()

        try:
            response = urequests.get("{}ping/?timestamp={}".format(self.ip, timestamp / 1000), headers=self.header)
            if response.status_code == 200:
                response_json = ujson.loads(response.text)
                client = float(response_json['client_timestamp'])
                server = float(response_json['server_timestamp'][2:])
                self.write('local', 'Local: {}'.format(client))
                self.write('server', 'Server: {}'.format(server))
                return {'ping_client': client, 'ping_server': server}
        except:
            pass

        self.write('local', 'Local: ----------------')
        self.write('server', 'Server: ----------------')
        self.write('message', 'PING: fail')
        return False

    def send_data_to_server(self, ping):
        """"""
        data = {
            'source': 'esp32_core2',
            'measure': 'latency',
            'timestamps': [ping['ping_client']],
            'values': {'esp32_v6': [ping['ping_client']], 'server_v6': [ping['ping_server']]}
        }
        data = ujson.dumps(data)
        response = urequests.post("{}timeserie/".format(self.ip), headers=self.header, data=data)
        if response.status_code in [200, 201]:
            self.write('message', 'API: ok')
        else:
            self.write('message', 'API: timeserie fail')
        response.close()
