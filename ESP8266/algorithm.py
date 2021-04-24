import mathfunctions as math

# Indexes of specified samples types.
IR = -1
RED = -2
IR_PREVIOUS = -3
RED_PREVIOUS = -4
TIME = -5
TIME_PREVIOUS = -6
# Previous sample of ir equals to ir-2, previous sample of red equals to red-2, and previous sample of time equals to
# time-1.


class HrSpOalgorithm:
    def __init__(self):
        """
        Initiation of HrSpOalgorithm responsible for calculation hr and spo2 based on readings from IR and RED leds.
        Variables declared in __init__ are overwritten through algorithm work, so they can be declared only once.
        """
        self.setup()

        # Rising and falling edge flags.
        self.rising_edge = 2 * [0]
        self.falling_edge = 2 * [0]

        # Variables saving maxes and mins occured.
        self.max = 2 * [0]
        self.min = 2 * [0]

        # Extremum type detection flag.
        self.extremum = 2 * [0]

        # Minimum difference in readings after max to determine it was a beat. At the beginning the goal of declaring
        # these was to avoid small changes of read values being recognized as a beat, and they were equal to [10,20].
        # But actually higher values make algorithm not recognizing beat under some circumstances so they were change
        # to almost 0.
        self.after_max_min_diff = [2, 2]

        # Alternating part, direct part of each signal and their ratio.
        self.ac = 2 * [0]
        self.dc = 2 * [0]
        self.acdc_ratio = 2 * [0]

        # Minimum and maximum difference between two local maxes occured to determine that it was a heartbeat, not
        # a body shake.
        self.min_diff = 0
        self.max_diff = 1500

        # Beat occured flag.
        self.beat = False

        # R variable value. Needed to count spo2.
        self.r = 0

        # New values flag.
        self.new_values = False

    def setup(self):
        """ Declaration of variables which have to be cleared before every measure try. """
        # Samples buffor.
        self.sample = 6 * [0]

        # Amount of beats occured.
        self.beats = 0

        # Last beat bpm value.
        self.bpm = 0

        # Buffor with collected bpm values.
        self.bpm_buf = []

        # Beat time. [-1] is present one, [-2] is previous one.
        self.beat_time = 2 * [0]

        # Last spo2 value.
        self.spo = 0

        # Buffor with collected spo2 values.
        self.spo_buf = []

        # Buffors with true local maximums and minimums and their times. True extremum is a local extremum of signal
        # waveform, not caused by body shake or any other, unexpected change of value
        self.local_max = 4 * [0]
        self.local_min = 4 * [0]
        self.local_max_time = 4 * [0]
        self.local_min_time = 4 * [0]

        # Buffor with local max detected flags.
        self.local_max_detected = 4 * [0]

    def reorder_samples(self, ir_value, red_value, time_value):
        """ Set previous sample as current before proceeding next one. Set gotten sample as current. """
        self.sample[IR_PREVIOUS] = self.sample[IR]
        self.sample[RED_PREVIOUS] = self.sample[RED]
        self.sample[TIME_PREVIOUS] = self.sample[TIME]

        self.sample[IR] = ir_value
        self.sample[RED] = red_value
        self.sample[TIME] = time_value

    def detect_edge(self, i):
        """
        Detect if any edge occured. If detected, set specific flag to True and save present sample as max or min.
        """
        if self.sample[i] > self.sample[i - 2]:
            self.rising_edge[i] = True
            self.max[i] = self.sample[i]
        elif self.sample[i] < self.sample[i - 2]:
            self.falling_edge[i] = True
            self.min[i] = self.sample[i]
        else:
            return

    def detect_extremum(self, i):
        """
        Detect if any true extremum occued. If detected, set specific flag to true, save the value and time
        of it. Also save the previous extremum value and time. Return True if local maximum occured and False
        if it is local minimum. Else return None type.
        """
        if self.rising_edge[i] and (self.sample[i-2] - self.sample[i]) >= self.after_max_min_diff[i]:
            # If rising edge is set to True, and previous sample is higher then present by min_diff, then
            # assume it could be true local maximum of signal not caused by body shake.
            self.local_max_detected[i-2] = self.local_max_detected[i]
            self.local_max_detected[i] = True
            self.local_max[i-2] = self.local_max[i]
            self.local_max[i] = self.max[i]
            self.local_max_time[i-2] = self.local_max_time[i]
            self.local_max_time[i] = self.sample[TIME_PREVIOUS]
            self.rising_edge[i] = False
            self.extremum[i] = True
        elif self.rising_edge[i] and self.sample[i-2] == self.min[i] and self.local_max_detected[i]:
            # If rising edge is set to True, and previous sample is present minimum, and local_max was detected shortly
            # before, then assume it could be true local minimum of signal not caused by body shake.
            self.local_max_detected[i] = False
            self.local_min[i-2] = self.local_min[i]
            self.local_min[i] = self.min[i]
            self.local_min_time[i-2] = self.local_min_time[i]
            self.local_min_time[i] = self.sample[TIME_PREVIOUS]
            self.falling_edge[i] = False
            self.extremum[i] = False
        else:
            self.extremum[i] = None

    def get_dc_value(self, i):
        """ Get a dc of last local maximum of given signal."""
        nom = self.local_min[i-2] - self.local_min[i]
        denom = self.local_min_time[i-2] - self.local_min_time[i]
        dc = (nom / denom) * self.local_max_time[i] + (self.local_min[i-2] - (nom / denom) * self.local_min_time[i-2])
        return dc

    @staticmethod
    def moving_average(data, n):
        """ Get moving average buffor for given data. """
        sum_buf, output = [0], []
        for i, x in enumerate(data, 1):
            sum_buf.append(sum_buf[i - 1] + x)
            if i >= n:
                result = (sum_buf[i] - sum_buf[i - n]) / n
                output.append(result)

        return output

    def count_hr_spo(self, ir_value, red_value, time_value):
        """ Main algorithm responsible for all calculations."""
        self.new_values = False
        self.reorder_samples(ir_value, red_value, time_value)
        # Calculations are made for both of signals.
        for signal in [IR, RED]:
            previous = signal - 2
            # Try to detect any edge and any extremum.
            self.detect_edge(signal)
            self.detect_extremum(signal)
            # Heartbeat is detected based on value from IR led.
            if signal == IR:
                # If true local maximum was detected and difference between it and the previouse one is higher than
                # minimal declared value and higher than maximal declared value count it as a heartbeat.
                max_min_diff = self.local_max[signal] - self.local_min[signal]
                if (self.extremum[signal]) and (max_min_diff > self.min_diff) and (max_min_diff < self.max_diff):
                    # Save previous time as a present beat time, then count time between present and previous beat time.
                    self.beat_time[-1] = self.sample[TIME_PREVIOUS]
                    delta = self.beat_time[-1] - self.beat_time[-2]
                    # Calculate the bpm based on delta time in ms.
                    bpm = 60 / (delta/1000)
                    # If time between beats is greater than 3 seconds then setting everything up again is needed.
                    if delta >= 3000 and self.beats > 2:
                        self.setup()
                        continue
                    # Anti shake condition. If difference between saved and gotten bpm is lower by value set then the
                    # measure is likely valid. It counts as soon as 10 continous beats are obtained. Every measure
                    # counts if saved bpm is lower than 50
                    if (self.bpm < 50) or (math.abs(bpm - self.bpm) < 20) or (self.beats < 10):
                        self.beat_time[-2] = self.beat_time[-1]
                        self.beats += 1
                        if self.beats > 1:
                            # If more than one beat collected append the bpm buffor with this value.
                            self.bpm_buf.append(bpm)
                            if len(self.bpm_buf) > 10:
                                # If more than 10 values collected, reject the oldest one.
                                self.bpm_buf = self.bpm_buf[1::]
                            # Calculate bpm value as a mean of last 2-10 values gotten. It lowers impact of incorrect
                            # values gotten. Set beat and new values flag as true.
                            self.bpm = int(math.mean(self.bpm_buf))
                            self.new_values = True
                            self.beat = True
                        else:
                            # It has to be more than one true local maximum collected to properly count the bpm.
                            pass
                    else:
                        # If difference between saved and gotten bpm is greater by offset value set then the measure is
                        # likely faulty.
                        pass
            if self.extremum[signal] == False and self.beat:
                # If true local minimum occured and beat was detected before then spo2 calculation can start.
                if self.local_min[previous] != 0:
                    # It has to be two local minimums detected to calculate the spo2 value.
                    self.dc[signal] = self.get_dc_value(signal)
                    self.ac[signal] = self.local_max[signal] - self.dc[signal]
                    self.acdc_ratio[signal] = self.ac[signal]/self.dc[signal]
                    # If the processed signal is a signal from the RED LED, then the signal from the IR LED has already
                    # been processed in this cycle.
                    if signal == RED:
                        try:
                            # Try to count R factor. Leave function if ZeroDivisionError occurs.
                            self.r = self.acdc_ratio[RED] / self.acdc_ratio[IR]
                        except ZeroDivisionError:
                            return
                        # Count spo2 value based on equation from AN6409 maxim integrated PDF.
                        spo = 104 - 17 * self.r
                        if 100 > spo > 60:
                            # Spo can not be higher than 100. Value lower than 60 is likely unlikely.
                            self.spo_buf.append(spo)
                            if len(self.spo_buf) > 10:
                                # If more than 10 values collected, reject the oldest one.
                                self.spo_buf = self.spo_buf[1::]
                            # Calculate spo2 value as a mean of last 2-10 values gotten, and round it to two decimals.
                            # Set beat flag as False.
                            self.spo = round(math.mean(self.spo_buf),2)
                            self.beat = False
                else:
                    # Two local minimums have to be detected to corrcetly count spo2 value.
                    pass

        return self.new_values, self.bpm, self.spo