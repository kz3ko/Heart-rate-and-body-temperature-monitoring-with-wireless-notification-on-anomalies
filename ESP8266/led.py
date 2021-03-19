import utime
from machine import Pin

class Led():
    def __init__(self):
        """ Initiatin of Led class responsible for led managamnet. Actually only one function is needed. """
        self.led = Pin(2, Pin.OUT)
        self.led.on() # Defualt states are swapped -> on==off and off==on.

    def toggle(self):
        """ Turn on the led just for 1ms. """
        self.led.off()
        utime.sleep_ms(1)
        self.led.on()