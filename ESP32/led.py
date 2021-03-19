import utime
from machine import Pin

class Led():
    def __init__(self):
        """ Initiatin of Led class responsible for led managamnet. Actually only one function is needed. """
        self.led = Pin(2, Pin.OUT)

    def toggle(self):
        """ Turn on the led just for 1ms. """
        self.led(1)
        utime.sleep_ms(2)
        self.led(0)