from m5stack import *
from m5stack_ui import *
from uiflow import *
import ujson

import network
import urequests
import time

screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x000000)

T = 3
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkzMjQwMjMyLCJpYXQiOjE2OTMxNTM4MzIsImp0aSI6IjhhMGEzZWViY2ViYzQ0YTA4MzAxMzY1MmNiZjQ4ZTIwIiwidXNlcl9pZCI6MX0.nFDLuPQNrWMhmgv4cBTTXfzeXeN7Q-ijDZtQzL-2c5M"
HEADER = {
    'content-type': 'application/json',
    'Authorization': "Bearer {}".format(TOKEN),
    }

def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a la red...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass

server_diff_last = 0
client_diff = 0
sever_diff = 0

def ping_url(url, time_):
    global client_diff, sever_diff, server_diff_last
    response = urequests.get("{}ping/?timestamp={}".format(url, time_/1000), headers=HEADER)

    if response.status_code == 200:
        resp = ujson.loads(response.text)

        client_time = float(resp['client_timestamp'])
        server_time = float(resp['server_timestamp'][7:])

        ping_label.set_text('Local: {:} s'.format(client_time))
        ping_label2.set_text('Server: {:} s'.format(server_time))

        v1 = client_time - client_diff - T
        v2 = server_diff_last

        ping_label3.set_text('Local diff: {:} s'.format(v1))
        ping_label4.set_text('Server diff: {:} s'.format(v2))

        ping_label5.set_text('Delta: {:} ms'.format(1000 * (client_time - client_diff - T - server_diff_last)))

        data = {
            'source': 'esp32_core2',
            'measure': 'latency',
            'timestamps': [time_],
            'values': {
                'esp32': [v1],
                'server': [v2],
            }
        }

        data = ujson.dumps(data)
        response = urequests.post("{}timeserie/".format(url), headers=HEADER, data=data)

        if response.status_code in [200, 201]:
            ping_label6.set_text('API: ok')
        else:
            ping_label6.set_text('API: fail')

    else:
        ping_label.set_text('ERROR')

    server_diff_last = server_time - sever_diff - T
    client_diff = client_time
    sever_diff = server_time

    response.close()

blue_label = M5Label("Starting...")
blue_label.set_align(1, x=10, y=10)
blue_label.set_text_color(0x00ff00)

blue_label.set_text("Foundation PING")
connect_to_wifi('HOME CHICAS SUPERPODEROSAS', 'LaGuaridaDeMaka0910')
# connect_to_wifi('yeisonisapenguin', '?1n9u1n0')

ping_label = M5Label("Local:")
ping_label.set_align(1, x=10, y=30)
ping_label.set_text_color(0x00ff00)

ping_label2 = M5Label("Server:")
ping_label2.set_align(1, x=10, y=50)
ping_label2.set_text_color(0x00ff00)

ping_label3 = M5Label("Local diff:")
ping_label3.set_align(1, x=10, y=70)
ping_label3.set_text_color(0x00ff00)

ping_label4 = M5Label("Server diff:")
ping_label4.set_align(1, x=10, y=90)
ping_label4.set_text_color(0x00ff00)

ping_label5 = M5Label("Delta:")
ping_label5.set_align(1, x=10, y=110)
ping_label5.set_text_color(0x00ff00)

ping_label6 = M5Label("API:")
ping_label6.set_align(1, x=10, y=130)
ping_label6.set_text_color(0x00ff00)

while True:
    # ping_url('http://192.168.161.22:8000/timescaledbapp/ping/', time.ticks_ms())
    ping_url('http://192.168.1.54:49051/timescaledbapp/', time.ticks_ms())
    time.sleep(T)

