from network import WLAN
from machine import UART
import machine
import os

wlan = WLAN()
wlan.deinit()
uart = UART(0, baudrate=115200)
os.dupterm(uart)

machine.main('main.py')
