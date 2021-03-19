from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class Plot():
    def __init__(self, frame, type):
        """
        Initiaton of Plot class responsible for drawing plots at each page. Arguments are frame and type of plot.
        """
        plt.style.use('fivethirtyeight')
        self.frame = frame
        self.type = type

        # Plot initiation functions.
        self.type_set()
        self.create_figure()
        self.clear_axis_labels()
        self.setup_plots()
        self.draw_graph()

    def type_set(self):
        """ Determine type of plot. Set titles, ylabel and thresholds for given one."""
        if self.type == 'Pulse':
            self.title = 'Heartrate [bpm]'
            self.ylabel = 'bpm'
            self.lower_threshold = 50
            self.upper_threshold = 90
        elif self.type == 'SpO2':
            self.title = 'SpO2 [%]'
            self.ylabel = '%'
            self.lower_threshold = 93
            self.upper_threshold = None
        elif self.type == 'Temperature':
            self.title = 'Temperature [°C]'
            self.ylabel = '°C'
            self.lower_threshold = None
            self.upper_threshold = 37
        self.xlabel = 'Time [hh:mm:ss]'

    def create_figure(self, width=11.3, height=3, fontsize=16):
        """
        Create figure with subplot. Arguments are width, height and fontsize - all set by default to fit properly to
        FHD display.
        """
        self.fig = plt.figure(figsize=(width, height), tight_layout=True)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.set_title(self.title, fontsize=fontsize)

    def clear_axis_labels(self):
        """ Axis labels are cleard by default. """
        self.ax.xaxis.set_major_formatter(plt.NullFormatter())
        self.ax.yaxis.set_major_formatter(plt.NullFormatter())

    def setup_plots(self):
        """ Setup all of the plots. There are three - line with measure values, and min and max threshold lines. """
        self.measure, = self.ax.plot([], [], linewidth=1.5)
        self.min, = self.ax.plot([], [], linewidth=1.2, color='r', linestyle='--')
        self.max, = self.ax.plot([], [], linewidth=1.2, color='r', linestyle='--')

    def draw_graph(self):
        """ Prepare graph to collecting data. """
        self.graph = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.graph.draw()
        self.graph.get_tk_widget().pack(in_=self.frame, fill='both', anchor='nw', expand=True)

    def setup_axis_labels(self, runtime, time, ymin, ymax, xtick_amount=5):
        """
        Setup axis labels based on runtime, time, and ylims. This functions is responsible for dynamically managing
        axises and axises labels.
        """
        xtick_step = round(len(runtime)/xtick_amount)
        self.ax.set_xlim(runtime[0], runtime[-1])
        self.ax.set_xticks(runtime[::-xtick_step])
        self.ax.set_xticklabels(time[::-xtick_step])

        self.ax.yaxis.set_major_formatter(plt.ScalarFormatter())
        self.ax.set_ylim(ymin, ymax)

        self.ax.set_xlabel(self.xlabel, fontsize=13)
        self.ax.set_ylabel(self.ylabel, fontsize=13)
        self.ax.tick_params(axis='both', labelsize=12)

    def update(self, runtime, y, time, ymin, ymax):
        """ Udpdate plot by given data. It draws thresholds and show legend in the left corner of hr graph. """
        self.measure.set_data(runtime, y)

        if self.lower_threshold:
            self.min.set_data(runtime, self.lower_threshold)
        if self.upper_threshold:
            self.max.set_data(runtime, self.upper_threshold)

        self.setup_axis_labels(runtime, time, ymin, ymax)

        if self.type == 'Pulse':
            self.measure.set_label('Measured value')
            self.max.set_label('Threshold')
            self.ax.legend(loc='upper left')

        # Redraw the graph.
        self.graph.draw_idle()


class Bar(Plot):
    def __init__(self, frame, type):
        """ Initation of Bar class which inheritates from Plot class. Many functions and concept are same. """
        plt.style.use('fivethirtyeight')
        self.frame = frame
        self.type = type

        self.ids = []
        self.avg = 45*[0]
        self.ymax = None
        self.ymin = None

        super().type_set()
        super().create_figure(width=10.75)
        super().clear_axis_labels()
        super().draw_graph()

    def setup_bars(self):
        """ This set amount of empty bars equals to amount of clients connected. """
        # The x variable is made like this to avoid half of bar cutting.
        x = range(1, self.amount+1)
        self.bars = self.ax.bar(x, self.amount*[0], edgecolor='black')

    def draw_threshold(self):
        """ Draw threshold lines at whole graph. """
        x = range(-10, self.amount+10)
        self.min, = self.ax.plot(x, len(x)*[self.lower_threshold], linewidth=1.5, color='r', linestyle='--')
        self.max, = self.ax.plot(x, len(x)*[self.upper_threshold], linewidth=1.5, color='r', linestyle='--')

    def setup_axis_labels(self):
        """ Function responsible for axies management. """
        self.ax.yaxis.set_major_formatter(plt.ScalarFormatter())
        self.ax.xaxis.set_major_formatter(plt.ScalarFormatter())

        self.ax.set_xticks(range(1, self.amount+1))
        self.ax.set_xlim(0.5, self.amount+0.5)

        self.ax.set_xlabel('Device ID', fontsize=13)
        self.ax.set_ylabel(self.ylabel, fontsize=13)
        self.ax.tick_params(axis='both', labelsize=12)

        self.ax.set_xticklabels(self.ids)

    def data_update(self, id, avg, buf):
        """ Function responsible for update data of each bar. """
        self.id = id
        self.ids = set(self.ids)
        self.ids.add(self.id)
        self.ids = list(self.ids)
        self.buf = buf

        self.amount = len(self.ids)

        self.avg[self.id] = avg
        self.values = []

        self.update_max()
        self.update_min()

        # All bars heights are collected in values buffor. It allow to simplify whole process just to updating this
        # buffor and set the bars heights based on this.
        for i, value in enumerate(self.avg):
            if value == 0:
                continue
            else:
                self.values.append(float(value))

    def update_max(self):
        """ Function responsible for updating ymax based on received data. """
        ymax = max(self.buf)

        if self.ymax != None and ymax < self.ymax:
            return

        if self.type == 'Pulse':
            self.ymax = ymax + 5
        elif self.type == 'SpO2':
            self.ymax = ymax + 2
            if self.ymax > 100:
                self.ymax = 100
        elif self.type == 'Temperature':
            self.ymax = ymax + 2

    def update_min(self):
        """ Function responsible for updating ymin based on received data. """
        ymin = min(self.buf)

        if self.ymin != None and ymin > self.ymin:
            return

        if self.type == 'Pulse':
            self.ymin = ymin - 5
        elif self.type == 'SpO2':
            self.ymin = ymin - 2
            if self.ymin > 100:
                self.ymin = 100
        elif self.type == 'Temperature':
            self.ymin = ymin - 2

    def update(self):
        """
        Update bar height by received data. This function clears whole graph before process to avoid drawing new bar
        on old one. Some of processess must be repeated.
        """
        try:
            self.ax.clear()
            super().clear_axis_labels()
            self.ax.set_title(self.title, fontsize=16)
            self.setup_bars()
            self.ax.set_ylim(self.ymin, self.ymax)
            self.draw_threshold()
            self.setup_axis_labels()
            for i, bar in enumerate(self.bars):
                self.bars[i].set_height(self.values[i])
            self.graph.draw_idle()
        except AttributeError:
            return
