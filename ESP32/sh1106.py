import framebuf
import time
import machine

"Address of each register."
set_contrast = 0x81
set_norm_inv = 0xa6
set_disp = 0xae
set_scan_dir = 0xc0
set_seg_remap = 0xa0
low_column_address = 0x00
high_column_address = 0x10
set_page_address = 0xB0


class SH1106:
    def __init__(self, external_vcc, width, height):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc

        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MVLSB)
        self.framebuf = fb

        # Shortcuts of the methods of framebuf
        self.fill = fb.fill
        self.fill_rect = fb.fill_rect
        self.hline = fb.hline
        self.vline = fb.vline
        self.line = fb.line
        self.rect = fb.rect
        self.pixel = fb.pixel
        self.scroll = fb.scroll
        self.text = fb.text
        self.blit = fb.blit

        self.init_display()

    def init_display(self):
        self.reset()
        self.fill(0)
        self.poweron()
        self.show()

    def poweroff(self):
        self.write_cmd(set_disp | 0x00)

    def poweron(self):
        self.write_cmd(set_disp | 0x01)

    def rotate(self, flag, update=True):
        if flag:
            self.write_cmd(set_seg_remap | 0x01)  # Mirror display vertically.
            self.write_cmd(set_scan_dir | 0x08)  # Mirror display vertically.
        else:
            self.write_cmd(set_seg_remap | 0x00)
            self.write_cmd(set_scan_dir | 0x00)
        if update:
            self.show()

    def sleep(self, value):
        self.write_cmd(set_disp | (not value))

    def contrast(self, contrast):
        self.write_cmd(set_contrast)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(set_norm_inv | (invert & 1))

    def show(self):
        for page in range(self.height // 8):
            self.write_cmd(set_page_address | page)
            self.write_cmd(low_column_address | 2)
            self.write_cmd(high_column_address | 0)
            self.write_data(self.buffer[ self.width * page:self.width * page + self.width])

    def reset(self, res):
        if res is not None:
            res(1)
            time.sleep_ms(1)
            res(0)
            time.sleep_ms(20)
            res(1)
            time.sleep_ms(20)

    def setup(self):
        self.poweron()
        self.sleep(False)
        self.clear()

    def clear(self):
        self.fill(0)

class Spi(SH1106):
    def __init__(self, width=128, height=64,
                 spi=machine.SPI(1, baudrate=10000000,
                                 sck=machine.Pin(14),
                                 mosi=machine.Pin(13)),
                 dc=machine.Pin(16),
                 res=machine.Pin(17),
                 cs=machine.Pin(15),
                 external_vcc=False):

        self.rate = 10 * 1000 * 1000
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs

        self.dc.init(self.dc.OUT, value=0)
        if self.res is not None:
            self.res.init(self.res.OUT, value=0)
        if self.cs is not None:
            self.cs.init(self.cs.OUT, value=1)

        super().__init__(external_vcc, width, height)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        if self.cs is not None:
            self.cs(1)
            self.dc(0)
            self.cs(0)
            self.spi.write(bytearray([cmd]))
            self.cs(1)
        else:
            self.dc(0)
            self.spi.write(bytearray([cmd]))

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        if self.cs is not None:
            self.cs(1)
            self.dc(1)
            self.cs(0)
            self.spi.write(buf)
            self.cs(1)
        else:
            self.dc(1)
            self.spi.write(buf)

    def reset(self):
        super().reset(self.res)

    def setup(self):
        super().setup()

    def clear(self):
        super().clear()