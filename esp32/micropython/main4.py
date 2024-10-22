from m5stack import *
from m5stack_ui import *
from uiflow import *
import ujson
import network
import urequests
import time
import sys

# Initialize screen and labels
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x000000)

# WiFi Connection


def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to the network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass


# Constants and initial values
T = 3
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkzNTIxNDgzLCJpYXQiOjE2OTM0MzUwODMsImp0aSI6IjRjYWFiODQxYmQ1MDQ3OTNhZTEyODQyZWE3YjkwZTZjIiwidXNlcl9pZCI6MX0.1iBHRBvjhjjKy0DTdCkUJ1nr7PWun3FN8rb4Aq6Z_uk"
HEADER = {'content-type': 'application/json', 'Authorization': "Bearer {}".format(TOKEN)}
control = None
server_time_prev = 0
client_time_prev = 0

blue_label = M5Label("Starting...")
blue_label.set_align(1, x=10, y=10)
blue_label.set_text_color(0x00ff00)

ping_label5 = M5Label("Timestamp:")
ping_label5.set_align(1, x=10, y=30)
ping_label5.set_text_color(0x00ff00)

ping_label = M5Label("Local:")
ping_label.set_align(1, x=10, y=50)
ping_label.set_text_color(0x00ff00)

ping_label2 = M5Label("Server:")
ping_label2.set_align(1, x=10, y=70)
ping_label2.set_text_color(0x00ff00)

ping_label3 = M5Label("Local diff:")
ping_label3.set_align(1, x=10, y=90)
ping_label3.set_text_color(0x00ff00)

ping_label4 = M5Label("Server diff:")
ping_label4.set_align(1, x=10, y=110)
ping_label4.set_text_color(0x00ff00)

# ping_label5 = M5Label("Delta:")
# ping_label5.set_align(1, x=10, y=110)
# ping_label5.set_text_color(0x00ff00)

ping_label6 = M5Label("API:")
ping_label6.set_align(1, x=10, y=140)
ping_label6.set_text_color(0x00ff00)

ping_label7 = M5Label("")
ping_label7.set_align(1, x=10, y=160)
ping_label7.set_text_color(0x00ff00)

# Request and processing


def ping_url(url, timestamp):
    global control, server_time_prev, client_time_prev

    try:
        response = urequests.get("{}ping/?timestamp={}".format(url, timestamp / 1000), headers=HEADER)
    except:
        client_time_control = time.ticks_ms()
        control = None
        ping_label6.set_text('API: ping fail')
        time.sleep(3)
        return False

    if response.status_code == 200:
        try:
            resp = ujson.loads(response.text)
        except:
            client_time_control = time.ticks_ms()
            control = None
            ping_label6.set_text('API: resp fail')
            time.sleep(3)
            return Fasle

        client_time_curr = float(resp['client_timestamp'])
        server_time_curr = float(resp['server_timestamp'][3:])

        if control is None:
            control = server_time_curr
            return False

        server_time_curr -= control

        # Calculate time differences
        v1 = client_time_curr - client_time_prev - T
        v2 = server_time_curr - server_time_prev - T

        # Update UI labels
        update_ui(client_time_curr, server_time_curr, v1, v2, timestamp / 1000)

        # Send data to the server
        send_data_to_server(url, timestamp / 1000, v1, v2)

        # Update previous time values
        client_time_prev = client_time_curr
        server_time_prev = server_time_curr

        response.close()

        return True


def update_ui(client_time, server_time, v1, v2, timestamp):
    ping_label.set_text('Local: {} s'.format(client_time))
    ping_label2.set_text('Server: {} s'.format(server_time))
    ping_label3.set_text('Local diff: {} s'.format(v1))
    ping_label4.set_text('Server diff: {} s'.format(v2))
    ping_label5.set_text('Timestamp: {} s'.format(timestamp))


def send_data_to_server(url, timestamp, v1, v2):
    data = {
        'source': 'esp32_core2',
        'measure': 'latency',
        'timestamps': [timestamp],
        'values': {'esp32': [v1], 'server': [v2]}
    }
    data = ujson.dumps(data)
    response = urequests.post("{}timeserie/".format(url), headers=HEADER, data=data)
    if response.status_code in [200, 201]:
        ping_label6.set_text('API: ok')
    else:
        ping_label6.set_text('API: timeserie fail')
    response.close()


# Main loop
blue_label.set_text("Foundation PING")
client_time_control = time.ticks_ms()
connect_to_wifi('HOME CHICAS SUPERPODEROSAS', 'LaGuaridaDeMaka0910')
c = 0
while c < 1000:

    t0 = time.ticks_ms()
    r = ping_url('http://192.168.1.54:51102/timescaledbapp/', time.ticks_ms() - client_time_control)
    if not r:
        continue
    ping_label7.set_text('C={}'.format(c))
    t1 = time.ticks_ms()

    blue_label.set_text("{}${}${}".format((t1, t0, t1 - t0)))

    time.sleep(T - ((t1 - t0) * 1000))
    c += 1

screen.clean_screen()
screen.set_screen_bg_color(0x000000)
blue_label.set_text("DONE!!!")


