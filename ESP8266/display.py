import symbols
from sh1106 import Spi

class Display(Spi):
    def __init__(self):
        """
        Initiation of Display class which is responsible for custom display managment functions. It is based on Spi
        class imported from sh1106.py module.
        """
        self.display = Spi()
        super().__init__()

    def show_time(self, time, date, id):
        """ Show present date, time and device id on display. These are being displayed constantly. """
        # Fill the 128x16 pixels rectangle starting from 0x0 with 0s. It makes this part of display
        # completely clean. Any part of display may be cleared like this. It can be also filled with
        # 1s. 0 is dark pixel, seen as no pixel, 1 is 'blue' pixel.
        self.display.fill_rect(0, 0, 128, 16, 0)

        # Display text 'str(id)' starting from 0x0.
        self.display.text(str(id), 0, 0, 1)
        self.display.text(time, 32, 0, 1)
        self.display.text(date, 24, 8, 1)
        self.display.show()

    def show_values(self, bpm, spo, temperature):
        """ Show measured values on display. """
        self.display.fill_rect(0, 36, 128, 28, 0)
        self.display.text('Pulse: ' + str(int(bpm)) + ' bpm', 0, 36, 1)
        self.display.text('SpO2 : ' + str("%.2f" % spo) + " %", 0, 46, 1)
        self.display.text('Temp.: ' + str("%.2f" % temperature) + "  C", 0, 56, 1)
        for y, row in enumerate(symbols.circle):
            for x, c in enumerate(row):
                self.display.pixel(x + 104, y + 56, c)

    def show_wifi_status(self, status):
        """ Show WiFi status on display."""
        if status:
            self.display.setup()
            self.display.text('Connection', 24, 20, 1)
            self.display.text('to WiFi', 36, 28, 1)
            self.display.text('succeed!', 32, 36, 1)
            self.display.show()
        else:
            self.display.setup()
            self.display.text('Connection', 24, 20, 1)
            self.display.text('to WiFi', 36, 28, 1)
            self.display.text('failed!', 36, 36, 1)
            self.display.show()

    def show_alarm(self, alarm):
        """ Show alarm if any occured. """
        if alarm != '':
            self.display.fill_rect(0, 23, 128, 8, 0)
            self.display.text('ALARM!', 40, 23, 1)
        else:
            self.display.fill_rect(0, 23, 128, 8, 0)

    def idle_state(self):
        """ Set display in its idle state. Lower part of display is cleared. """
        self.display.fill_rect(0, 23, 128, 41, 0)

    def work_state(self):
        """ Set display in its work state. Inform that sensor tries to measure. """
        self.display.fill_rect(0, 23, 128, 41, 0)
        self.display.text('Waiting for beat!', 0, 23, 1)

    def clear(self):
        """ Clear whole display. """
        self.display.clear()

    def setup(self):
        """
         Call all the functions responsible for running display such as powerup, turn off sleep mode and clear pixels.
         Just in case.
         """
        self.display.setup()