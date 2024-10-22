
from m5stack import *
from m5stack_ui import *
from uiflow import *
import ujson
import network
import urequests
import time
import sys


from m5stack_ui import FONT_MONT_14


IP = 'http://192.168.7.22:51102/timescaledbapp/'
TOKEN = {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyNTIyODA1OSwiaWF0IjoxNjkzNjkyMDU5LCJqdGkiOiIyMjg3Zjc2MTk5MDY0MzJiYTc0ZTZiMWQ4NWNiYzBiNCIsInVzZXJfaWQiOjF9.6wq-irScHTJ8nf8U0ruByrrYiEvEkqAbZFKTyF_A8Yc",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkzNzc4NDU5LCJpYXQiOjE2OTM2OTIwNTksImp0aSI6ImRhZDgzNTU3NTk3MDQ3YzA5NDZhZWQ1OTczZmU5OWNkIiwidXNlcl9pZCI6MX0.RcO7-ms8tj8F-9JkOzfACYMhtByi7BKspOla7bhpAK0"
}

# SSID = 'HOME CHICAS SUPERPODEROSAS'
# PASSWORD = 'LaGuaridaDeMaka0910'

SSID = 'yeisonisapenguin'
PASSWORD = '?1n9u1n0'


class Foundation():

    def __init__(self, url, token):
        """"""
        self.url = url
        self.header = {'content-type': 'application/json', 'Authorization': "Bearer {}".format(token)}

    def connect_to_wifi(self, ssid, password):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            wlan.connect(ssid, password)
            while not wlan.isconnected():
                pass

    def ping(self, bytes=0):
        """"""
        try:
            start = time.ticks_ms()
            response = urequests.get("{}ping/".format(self.url))
            ping = time.ticks_ms() - start
            response.close()
            if response.status_code in [200, 201]:
                return ping
        except:
            pass

    def send_data_to_server(self, timestamp, data):
        """"""
        data = {
            'source': 'esp32_core2',
            'measure': 'latency',
            'timestamps': timestamp,
            'values': data,
        }
        data = ujson.dumps(data)
        t0 = time.ticks_ms()
        response = urequests.post("{}timeserie/".format(self.url), headers=self.header, data=data)
        ping = time.ticks_ms() - start
        response.close()
        if response.status_code in [200, 201]:
            return ping


class UI():

    def __init__(self):
        """"""

        self.screen = M5Screen()
        self.screen.clean_screen()
        self.screen.set_screen_bg_color(0x000000)

    def message(self, text):
        """"""
        w = 200
        self.msg = M5Msgbox(['Ok'], x=(320 - w) // 2, y=50, w=w, h=100)
        self.msg.set_text(text)


ui = UI()
foundation = Foundation(IP, TOKEN["access"])
foundation.connect_to_wifi(SSID, PASSWORD)
ui.message('Connected to "{}"'.format(SSID))


# Feed button
btn_feed = M5Btn("Feed", x=0, y=185, w=90, h=50, bg_c=0x3C0D85, text_c=0xC4B4FF, font=FONT_MONT_14)


def released_btn_feed():
    ping = foundation.send_data_to_server(
        timestamp=[time.ticks_ms()],
        data={'esp32_v6': [1], 'server_v6': [2]},
    )
    # ui.message('Feed: {} ms'.format(ping))
    ui.message('Feed: XXX ms')


btn_feed.released(released_btn_feed)


# WiFi button
btn_connect = M5Btn("Connect...", x=97, y=185, w=120, h=50, bg_c=0x3C0D85, text_c=0xC4B4FF, font=FONT_MONT_14)


def released_btn_connect():
    foundation.connect_to_wifi(SSID, PASSWORD)
    ui.message('Connected to "{}"'.format(SSID))


btn_connect.released(released_btn_connect)


# Ping button
btn_ping = M5Btn("Ping", x=225, y=185, w=90, h=50, bg_c=0x3C0D85, text_c=0xC4B4FF, font=FONT_MONT_14)


def released_btn_ping():
    ping = foundation.ping()
    ui.message('Ping: {} ms'.format(ping))


btn_ping.released(released_btn_ping)






