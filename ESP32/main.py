import utime
import ujson
import uasyncio
from ntptime import settime
from led import Led
from display import Display
from max30102 import Max30102
from algorithm import HrSpOalgorithm
from wireless import Wireless
from data import Data

async def start_async():
    await uasyncio.gather(
        main(),
        update_datetime(),
    )

async def update_datetime():
    # Get actual date and time. Then split them to hh:mm:ss and dd.mm.yy formats. Display when done.
    global realtime, date

    # Set RTC.
    time_set = False
    if wireless.wifi_status():
        settime()
        time_set = True

    while True:
        if wireless.wifi_status() and time_set:
            [y, m, d, h, min, s] = utime.localtime()[0:6]
            h = 0 if h == 23 else h + 1
            realtime = str("%02d" % h) + ':' + str("%02d" % min) + ':' + str("%02d" % s)
            date = str("%02d" % d) + '.' + str("%02d" % m) + '.' + str(y)
        else:
            realtime = '--------'
            date = '----------'
        display.show_time(realtime, date, device_id)
        await uasyncio.sleep_ms(100)

async def main():
    """ Main function running on uc. The part before while loop runs only once. """
    # Make needed variables globalky accessible.
    global device_id, wireless, sensor, algorithm, display, led, data

    # Declare device id. This one is first made.
    device_id = '1'

    # Declare all of the instances needed.
    wireless = Wireless(id=device_id)
    sensor = Max30102()
    algorithm = HrSpOalgorithm()
    display = Display()
    led = Led()
    data = Data()

    # Connect with WiFi and MQTT.
    wireless.wifi_connect()
    wireless.mqtt_connect()

    # Show WiFi connection status for 3 seconds. Clear the display when time elapse.
    display.show_wifi_status(wireless.wifi_status())
    utime.sleep(3)
    display.clear()

    # Prepare buffors responsible for collecting IR and RED leds data.
    red_buf = []
    ir_buf = []
    time_buf = []

    # Remember runtime just before running the while loop.
    previous_time = utime.ticks_ms()

    # Setup display before the while loop.
    display.setup()

    while True:
        await uasyncio.sleep_ms(50)

        # Read values measured by sensor. Take time of measure in account as well.
        red, ir, temperature = sensor.read_values()
        time = utime.ticks_ms() - previous_time

        # Determine if any body was detected by sensor based on IR value.
        if ir <= 30000:
            # No body was detected. Set the idle state and start the loop from the beginning.
            display.idle_state()
            sensor.set_idle_current()
            continue
        elif ir > 30000 and ir < 70000:
            # Something was detected. Don't know what exactly though. Prepare algorithm and sensor to work.
            # Start loop from the beginning.
            algorithm.setup()
            sensor.set_work_current()
            continue
        elif ir > 70000 and algorithm.beats == 0:
            # Most likely the human body was detected. Set work state of display and go on with loop.
            data.reset()
            display.work_state()

        # Collect measured values to buffors.
        red_buf.append(int(red))
        ir_buf.append(int(ir))
        time_buf.append(time)

        # At least n readings are needed to succesfully count the hr and spo2 values.
        n = 5
        if len(red_buf) > n:
            red_buf = red_buf[1::]
            ir_buf = ir_buf[1::]
            time_buf = time_buf[1::]
        elif len(red_buf) == n:
            pass
        else:
            continue

        # Count moving average of obtained data. n samples are beineg averaged.
        red_averaged = algorithm.moving_average(red_buf, n)
        ir_averaged = algorithm.moving_average(ir_buf, n)
        time_averaged = algorithm.moving_average(time_buf, n)

        # Get the last measured values.
        ir_value = int(ir_averaged[-1])
        red_value = int(red_averaged[-1])
        now = time_averaged[-1]

        # Try to count hr and spo2 values based on readings. Start loop from beggining if any error occured.
        # Most of the time it is ZeroDivisionEror but except all errors to make sure device will not hang on.
        try:
            new, hr, spo2 = algorithm.count_hr_spo(ir_value, red_value, now)
        except:
            continue

        # If new values gotten, and both of hr and spo2 are not zeros it can be assumed that proper value was obtained.
        if new and hr != 0 and spo2 != 0:
            # Save beat time and temperature rounded to two decimals as seperated variables. Just for convenience.
            beat_time = int(algorithm.beat_time[-1])
            temperature = round(temperature, 2)

            # Turn on the led shortly just to inform that new data was received.
            led.toggle()

            # Display gotten values.
            display.show_values(hr, spo2, temperature)

            # Start verifying if any alarm was detected by making new, empty string variable. Then decide what type
            # of alarm occured and add suitable information to alarm variable.
            alarm =''

            hr_min = 50
            hr_max = 90
            spo2_min = 93
            temperature_max = 37

            if hr < hr_min:
                alarm += ('HR_TOO_LOW|')
            elif hr > hr_max:
                alarm += ('HR_TOO_HIGH|')

            if spo2 < spo2_min:
                alarm += ('SPO2_TOO_LOW|')

            if temperature > temperature_max:
                alarm += ('TEMP_TOO_HIGH')

            # Show if alarm detected.
            display.show_alarm(alarm=alarm)

            # Check if connected to any broker. If not this point is loops end.
            if wireless.mqtt_status:
                # If alarm was not detected change it to '-'. PC app receiving data reads it like this.
                if alarm == '':
                    alarm = '-'

                # Update data with all needed values.
                data.update(date, realtime, beat_time, hr, spo2, temperature, alarm )

                # Send data to broker if 10 measures collected. Then reset the data buffor.
                if data.check_amount() >= 10:
                    wireless.publish(ujson.dumps(data.get_buf()))
                    data.reset()


if __name__ == '__main__':
    uasyncio.run(start_async())