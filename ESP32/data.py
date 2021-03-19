class Data:
    def __init__(self):
        """
        Initiation of Data class which is responsible for data managment. It starts with resetting all buffors required.
        """
        self.reset()

    def update(self, *args):
        """ Update all buffors with measured vales. """
        self.date_buf.append(args[0])
        self.runtime_buf.append(args[1])
        self.realtime_buf.append(args[2])
        self.hr_buf.append(args[3])
        self.spo2_buf.append(args[4])
        self.temp_buf.append(args[5])
        self.alarm_buf.append(args[6])

        # Preparing output buffor before sending.
        self.buffor[0] = self.date_buf
        self.buffor[1] = self.runtime_buf
        self.buffor[2] = self.realtime_buf
        self.buffor[3] = self.hr_buf
        self.buffor[4] = self.spo2_buf
        self.buffor[5] = self.temp_buf
        self.buffor[6] = self.alarm_buf

    def reset(self):
        """ Clear all data buffors. """
        self.date_buf = []
        self.runtime_buf = []
        self.realtime_buf = []
        self.hr_buf = []
        self.spo2_buf = []
        self.temp_buf = []
        self.alarm_buf = []
        self.buffor = 7 * [[]]

    def check_amount(self):
        """ Check amount of data collected in buffors. Equals to length of any of them. """
        return len(self.hr_buf)

    def get_buf(self):
        """ Get output buffor. """
        return self.buffor