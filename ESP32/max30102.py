from machine import Pin, I2C
import time
import mathfunctions as math


# Address of each register.
interrupt_status_1 = 0x00  # Points at type of interrupt which tripped.
interrupt_status_2 = 0x01  # -||-
interrupt_enable_1 = 0x02  # Allows to set any type of interrupt.
interrupt_enable_2 = 0x03  # -||-
fifo_write_pointer = 0x04  # Decides about location in FIFO where data are written.
overflow_counter = 0x05    # FIFO overflow counter.
fifo_read_pointer = 0x06   # Decides about location in FIFO from which data are read.
fifo_data_register = 0x07  # Output data buffer.
fifo_config = 0x08         # FIFO configuration.
mode_config = 0x09         # Mode configuration.
spo_config = 0x0a          # Configuration of SpO2 mode.
led_pa_1 = 0x0c            # Decides about current of each LED.
led_pa_2 = 0x0d            # -||-
multi_led_1 = 0x11         # Decides which LEDs are active in multi-LED mode.
multi_led_2 = 0x12         # -||-
temp_integer = 0x1f        # Integer value of temperature
temp_fraction = 0x20       # Fraction value of temperature.
temp_config = 0x21         # Temperature read mode configuration

# Default I2C address of MAX30102 sensor.
address = 0x57


class Max30102:
    def __init__(self, scl = Pin(18), sda = Pin(19), freq = 400000):
        """
        Initiate MAX30102 class ond each function responsible for correct device start-up.
        """
        # Define I2C connections and frequence.
        self.i2c = I2C(0, scl = scl, sda = sda, freq = freq)
        # Reset registers to default values.
        self.reset()
        time.sleep(1)
        # Read 1 byte from interrupt register. It clears interrupt register.
        self.i2c.readfrom_mem(address, interrupt_status_1, 1)
        # Start setup function.
        self.setup()

    def write(self, reg, value):
        """
        Set value named 'value' in register named 'reg'.
        """
        data = bytearray(1)  # One byte long array.
        data[0] = value
        self.i2c.writeto_mem(address, reg, data)

    def reset(self):
        """
        Set default values of all registers.
        """
        self.write(mode_config, 0x40)  # 0b01000000 = 0x40

    def shutdown(self):
        """
        Shutdown the device.
        """
        self.write(mode_config, 0x80)  # 0b10000000 = 0x80

    def setup(self):
        """
        Set all registers needed to correct work of sensor.
        """
        # Enable interrupt from temperature conversion end.
        self.write(interrupt_enable_2, 0x02)

        # FIFO pointers setting. Should start writing and reading from same register.
        # Also set the overflow counter start at 0x00.
        self.write(fifo_write_pointer, 0x00)
        self.write(fifo_read_pointer, 0x00)
        self.write(overflow_counter, 0x00)

        # FIFO config settings - sample average = 4, fifo rollover = enable(?), fifo almost full value = 17.
        self.write(fifo_config, 0x5f) # 0b010 1 1111 = 0x5f

        # Set mode. HR mode - 0b010; SpO2 mode - 0b011; Multi-LED mode - 0b111.
        self.write(mode_config, 0x03) # 0b011 = 0x03

        # SpO2 mode settings. ADC range (15,63 / 4096) - 01; Sample frequence - 400 - 011; LED pulse width - 411us - 11.
        self.write(spo_config, 0x27)  # 0b0 01 001 11 = 0x27 # For sample frequenc equal 400 0x2f.

        # Set idle current level for each LED.
        self.set_idle_current()

    def set_idle_current(self):
        """
        Set lower current when no body was detected. Let us save power by a bit.
        """
        self.write(led_pa_1, 0x10)
        self.write(led_pa_2, 0x0)

    def set_work_current(self):
        """
        Set current value before work start.
        """
        self.write(led_pa_1, 0x2f)
        self.write(led_pa_2, 0x2f)

    def get_data_samples(self):
        """
        Check amount of samples ready to read.
        """
        write_pointer = self.i2c.readfrom_mem(address, fifo_write_pointer, 1)[0]
        read_pointer = self.i2c.readfrom_mem(address, fifo_read_pointer, 1)[0]
        samples = write_pointer - read_pointer

        if samples < 0:
            samples += 32  # Take pointer wrap around into account.
        else:
            pass

        return samples

    def read_fifo(self):
        """
        Read red and ir values from the FIFO register.
        """
        # Clear both buffors with FIFO data read last time.
        red = None
        ir = None

        # Read 6 byte long data from the device.
        fifo_data = self.i2c.readfrom_mem(address, fifo_data_register, 6)

        # Mask bytes unused bytes[23:18]. Channels are swapped in used model of sensor.
        ir = (fifo_data[0] << 16 | fifo_data[1] << 8 | fifo_data[2]) & 0x3ffff # 0x3ffff = 2^18 - 1
        red = (fifo_data[3] << 16 | fifo_data[4] << 8 | fifo_data[5]) & 0x3ffff

        return red, ir

    def read_values(self):
        """
        Read 'samples' samples from FIFO. Return ready to process data.
        """
        red_buf = []
        ir_buf = []
        samples = self.get_data_samples()

        while samples > 0:
            red, ir = self.read_fifo()
            red_buf.append(red)
            ir_buf.append(ir)
            samples -= 1

        red = math.mean(red_buf)
        ir = math.mean(ir_buf)
        temperature = self.read_temperature()
        return red, ir, temperature

    def read_temperature(self):
        """
        Read temperature as sum of integer and fraction value.
        """
        # Initiate single temperature read.
        self.write(temp_config, 0x01)  # 0b00000001 = 0x01

        # Wait for end of A/C processing. If conversion status is equal to 2 then A/C processing has been done properly.
        # Otherwise something has gone wrong. Go on with function if 5 attempts are failed.
        status = self.i2c.readfrom_mem(address, interrupt_status_2, 1)[0]
        count = 1
        while status != 2 and count < 5:
            status = self.i2c.readfrom_mem(address, interrupt_status_2, 1)
            count += 1

        # Read register holding integer and fraction values. Add them to get temperature.
        integer = self.i2c.readfrom_mem(address, temp_integer, 1)[0]
        fraction = self.i2c.readfrom_mem(address, temp_fraction, 1)[0]
        temperature = float(integer) + (float(fraction) * 0.0625)

        return temperature