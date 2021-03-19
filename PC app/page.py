import tkinter as tk
import paho.mqtt.client as mqtt
import json
import threading
import csv
import os
import pathlib
from tkinter import ttk
from graph import Plot

class Page(tk.Frame):
    def __init__(self, client_id, update_time, *args, **kwargs):
        """
        Initiation of Page class which is responsible for displaying details about each device connected. It has two
        arguments needed, which are client id and uppdate time.
        """
        tk.Frame.__init__(self, *args, **kwargs)
        self.client_id = client_id
        self.style = ttk.Style()
        self.font = 'Segoe'

        self.update_time = update_time

        # Initiation of all functions and widgets.
        self.data_buf_init()
        self.mqtt_init()
        self.id_choose_init()
        self.logs_init()
        self.buttons_init()
        self.connected_label_init()

        # Graph is not visible by default.
        self.graph_visible = False

        # Running threads from beginning.
        self.threads_start()

    def threads_start(self):
        """
        Setting up some new threads. There four working sperately:
            - main loop - being responsible for most functions and features,
            - each graph update - updating hr, spo2 and temperature graph.
        Graphs are runinng seperately to avoid lags which were happening when they ran as one thread.
        """
        self.main_loop = threading.Thread(target=self.main, daemon=True)
        self.hr_graph_update_loop = threading.Thread(target=self.hr_graph_update, daemon=True)
        self.spo2_graph_update_loop = threading.Thread(target=self.spo2_graph_update, daemon=True)
        self.temperature_graph_update_loop = threading.Thread(target=self.temperature_graph_update, daemon=True)

        self.main_loop = threading.Thread(target=self.main, daemon=True)
        self.main_loop.start()

        self.hr_graph_update_loop.start()
        self.spo2_graph_update_loop.start()
        self.temperature_graph_update_loop.start()

    def main(self):
        """ Main loop. Responsible for calling all needed funtions if new message is received. """
        if self.connected:
            try:
                self.client.loop_start()
            except:
                return
            if self.new_message:
                self.new_message = False
                self.data = json.loads(self.data)
                self.data_split()
                self.data_buf_extend()
                self.pack_size_check()
                self.max_buf_len_check()
                self.hr_last = self.hr[-1]
                self.spo2_last = "%.2f" % self.spo2[-1]
                self.temperature_last = "%.2f" % self.temperature[-1]
                self.logs_update()
                self.log_to_file()
            else:
                pass
        else:
            pass

        self.after(int(self.update_time/5), self.main)

    def mqtt_init(self):
        """
        Initiation of MQTT. Declaring MQTT client, broker IP, on message function. It conencts to broker as well. There
        are some variables declared, such as new message flag, and connected flag, which are set to False by default.
        Pack size equals to 0 by default.
        """
        self.client = mqtt.Client(f"HP Laptop / Mikolaj Skrzyniarz /ID: {self.client_id}")
        self.broker = "192.168.0.87"
        self.client.on_message = self.on_message
        self.client.connect(self.broker)
        self.topic = ''
        self.new_message = False
        self.pack_size = 0
        self.connected = False

    def on_message(self, client, userdata, message):
        """
        This function is called automatically by MQTT Client everytime new message is received. It switches new message
        flag to True and saves decoded data.
        """
        self.new_message = True
        self.data = message.payload.decode("utf-8")

    def connect(self):
        """
        Connect function which actually works more like subscribe, because client is connected to broker all the
        time. It starts from disconnect function, then set the topic, susbcribes it and changes connected flag. At the
        end it shows calls function responsible for showing 'Connected' label.
        """
        self.disconnect()
        self.set_topic()
        self.client.subscribe(self.topic)
        self.connected = True
        self.connected_label_show()

    def disconnect(self):
        """
        Disconnect function which actually works more like unsubscribe. It tries to unsubscribe topic, excepting
        ValueError because it is called in 'connect' function before subscribing. After that it set connected flag to
        False and hide 'Connected' label.
        """
        try:
            self.client.unsubscribe(self.topic)
        except ValueError:
            pass
        self.connected = False
        self.connected_label_hide()

    def delete(self):
        """ Disconnect with broker and delet client. Being called when page is deleted. """
        self.client.disconnect(self.broker)
        del self.client

    def set_topic(self):
        """ Set the topic. 'esp8266/' is constant part of topic, because is set the same in ESP device. """
        self.id = self.id_choose_entry.get()
        self.topic = 'esp8266/' + str(self.id)

    def graph_show(self):
        """
        Show graph unless it is visible already. It creates frame where are placed three plots, which are instances of
        graph.Plot class.
        """
        if self.graph_visible:
            return
        self.graph_visible = True
        self.frame = tk.Frame(self, width=1200, height=915)
        self.hr_graph = Plot(self.frame, type ='Pulse')
        self.spo2_graph = Plot(self.frame, type = 'SpO2')
        self.temp_graph = Plot(self.frame, type ='Temperature')
        self.frame.place(x=775, y=45)

    def graph_hide(self):
        """ Hide graph frame unles it is hidden already. It destroys graph frame actually. """
        if not self.graph_visible:
            return
        self.graph_visible = False
        self.frame.place_forget()
        self.frame = None

    def hr_graph_update(self):
        """ Update hr graph every 'update_time'. """
        self.after(self.update_time, self.hr_graph_update)
        if not self.graph_visible:
            return

        try:
            ymin = min(self.hr_buf[-1800:]) - 5
            ymax = max(self.hr_buf[-1800:]) + 5
            self.hr_graph.update(self.run_time_buf[-1800:], self.hr_buf[-1800:], self.time_buf[-1800:], ymin, ymax)
        except:
            return

    def spo2_graph_update(self):
        """ Update spo2 graph every 'update_time'. """
        self.after(self.update_time, self.spo2_graph_update)
        if not self.graph_visible:
            return

        try:
            ymin = min(self.spo2_buf[-1800:]) - 3
            ymax = 100
            self.spo2_graph.update(self.run_time_buf[-1800:], self.spo2_buf[-1800:], self.time_buf[-1800:], ymin, ymax)
        except:
            return

    def temperature_graph_update(self):
        """ Update temperature graph every 'update_time'. """
        self.after(self.update_time, self.temperature_graph_update)
        if not self.graph_visible:
            return

        try:
            ymin = min(self.temp_buf[-1800:]) - 5
            ymax = 41
            self.temp_graph.update(self.run_time_buf[-1800:], self.temp_buf[-1800:], self.time_buf[-1800:], ymin, ymax)
        except:
            return

    def buttons_init(self):
        """ Show all buttons declared. """
        self.style.configure('W.TButton', font=(self.font, 14))

        self.connect_button = ttk.Button(self, text="Connect", style='W.TButton', command=self.connect)
        self.disconnect_button = ttk.Button(self, text="Disconnect", style='W.TButton', command=self.disconnect)
        self.logs_clear_button = ttk.Button(self, text="Clear logs", style='W.TButton', command=self.logs_clear)
        self.graph_show_button = ttk.Button(self, text="Show graph", style='W.TButton', command=self.graph_show)
        self.graph_hide_button = ttk.Button(self, text="Hide graph", style='W.TButton', command=self.graph_hide)

        self.connect_button.place(x=10, y=10, height=35, width=110)
        self.disconnect_button.place(x=130, y=10, height=35, width=140)
        self.logs_clear_button.place(x=280, y=10, height=35, width=130)
        self.graph_show_button.place(x=1640, y=10, height=35, width=130)
        self.graph_hide_button.place(x=1780, y=10, height=35, width=130)

    def id_choose_init(self):
        """ Show entry box responsible for getting ID. At default it has client id typed in. """
        self.entry = tk.StringVar()
        self.id_choose_entry = ttk.Entry(self, textvariable=self.entry, font=(self.font, 14, 'normal'))
        self.id_choose_label = ttk.Label(self, text=f'ID', font=(self.font, 17, 'normal'))
        self.id_choose_label.place(x=670, y=9, height=32.5, width=35)
        self.id_choose_entry.place(x=705, y=11, height=32.5, width=50)
        self.entry.set(str(self.client_id))

    def connected_label_init(self):
        """ Setup 'Connected' label. """
        self.connected_label = ttk.Label(self, text='Connected', font=(self.font, 17, 'normal'))

    def connected_label_show(self):
        self.connected_label.place(x=480, y=9, height=32.5, width=140)

    def connected_label_hide(self):
        self.connected_label.place_forget()

    def logs_init(self):
        """
        Setup logs. Actually logs are treeview with scrollbar added on the left side, responsible for changing treeview
        horizontally. It
        """
        columns_width = [30,125,125,70,70,125,200]
        width = sum(columns_width)

        self.logs = ttk.Treeview(self, selectmode='extended', style='Treeview')
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.logs.yview)

        self.logs.place(x=10, y=55, width=width, height=895)
        self.vsb.place(x=width+10, y=55, height=895)

        self.logs.configure(yscrollcommand=self.vsb.set)

        # Declaring tags for treeview. If any alarm occured then te row wil be red.
        self.style.map("Treeview", background=self.fixed_map("background"))
        self.logs.tag_configure('alarm', background='#FF3C3C')
        self.logs.tag_configure('noalarm', background='#FFFFFF')

        self.logs["columns"] = ("1", "2", "3", "4", "5", "6","7")
        self.logs['show'] = 'headings'
        headings = ["ID" ,"Date [dd:mm:yy]", "Time [hh:mm:ss]", "Hr [bpm]",
                    "SpO2 [%]", "Temperature [°C]", "Information"]

        for id in self.logs["columns"]:
            i = int(id) - 1
            if i == 6:
                self.logs.column(id, width=columns_width[i] - 2, anchor='c')
            else:
                self.logs.column(id, width=columns_width[i], anchor='c')
            self.logs.heading(id, text=headings[i])

        # To keep newest values at the top it was needed to start indexing from the last index.
        self.index = -self.max_amount

    def logs_update(self):
        """ Update logs with received data. """
        for i in range(-self.pack_size, 0, 1):
            if self.alarm_buf[i] != '-':
                alarm =''
                alarms = self.alarm_buf[i].split('|')
                for msg in alarms:
                    if msg == 'HR_TOO_LOW':
                        alarm += 'HR↓ '
                    elif msg == 'HR_TOO_HIGH':
                        alarm += 'HR↑ '
                    elif msg == 'SPO2_TOO_LOW':
                        alarm += 'SPO2↓ '
                    elif msg == 'TEMP_TOO_HIGH':
                        alarm += 'TEMPERATURE↑'
            else:
                alarm = self.alarm_buf[i]

            values = (str(self.id),
                      str(self.date_buf[i]),
                      str(self.time_buf[i]),
                      str(self.hr_buf[i]),
                      str("%.2f" % self.spo2_buf[i]),
                      str("%.2f" % self.temp_buf[i]),
                      alarm,)

            if self.alarm_buf[i] != '-':
                tag = 'alarm'
            else:
                tag = 'noalarm'

            self.logs.insert("", self.index, values=values, tags=tag)
            self.index += 1

        # Delete last 3600 measures f index is equal to 0 (24*3600 measures are in logs).
        if self.index == 0:
            self.index = -3600
            for row in self.logs.get_children()[self.index:]:
                self.logs.delete(row)

    def logs_clear(self):
        """ Clear all of the logs. """
        self.logs.delete(*self.logs.get_children())
        self.index = -self.max_amount

    def fixed_map(self, option):
        """ Function needed to set colors in treeview. """
        return [elm for elm in self.style.map("Treeview", query_opt=option)
                if elm[:2] != ("!disabled", "!selected")]

    def data_buf_init(self):
        """ Making needed buffors for collected data. """
        self.date_buf = []
        self.time_buf = []
        self.run_time_buf = []
        self.hr_buf = []
        self.spo2_buf = []
        self.temp_buf = []
        self.alarm_buf = []

        # Max amount in buffor is 24*3600 measures.
        self.max_amount = 24 * 3600

    def data_split(self):
        """ Split received data. """
        self.date = self.data[0]
        self.clock = self.data[1]
        self.run_time = self.data[2]
        self.hr = self.data[3]
        self.spo2 = self.data[4]
        self.temperature = self.data[5]
        self.alarm = self.data[6]

    def pack_size_check(self):
        """ Check size of received pack."""
        self.pack_size = len(self.date)

    def data_buf_extend(self):
        """ Extend data buffors with received ones. """
        self.date_buf.extend(self.date)
        self.time_buf.extend(self.clock)
        self.run_time_buf.extend(self.run_time)
        self.hr_buf.extend(self.hr)
        self.spo2_buf.extend(self.spo2)
        self.temp_buf.extend(self.temperature)
        self.alarm_buf.extend(self.alarm)

    def max_buf_len_check(self):
        """ Check if data buffors do not exceed max amount. """
        if len(self.date_buf) >= self.max_amount:
            # If they do, reject oldest 3600 measures and set index as -3600.
            self.date_buf = self.date_buf[3600:self.max_amount]
            self.time_buf = self.time_buf[3600:self.max_amount]
            self.run_time_buf = self.run_time_buf[3600:self.max_amount]
            self.hr_buf = self.hr_buf[3600:self.max_amount]
            self.spo2_buf = self.spo2_buf[3600:self.max_amount]
            self.temp_buf = self.temp_buf[3600:self.max_amount]
            self.alarm_buf = self.alarm_buf[3600:self.max_amount]

            self.index = -3600

    def get_recent_data(self):
        """ Get recent 1800 data, which will be transmitted to homepage. """
        try:
            if len(self.time_buf) >= 1800:
                begin = self.time_buf[len(self.time_buf)-1800]
            else:
                begin = self.time_buf[0]
            data = [self.id,
                    self.date_buf[-1],
                    begin,
                    self.time_buf[-1],
                    self.hr_buf[-1800:],
                    self.spo2_buf[-1800:],
                    self.temp_buf[-1800:],
                    self.alarm_buf[-1800:]]
            return data
        except IndexError:
            # It raises when no data was collected at the beginning of app work.
             return None


    def log_to_file(self):
        """
        Logs data to CSV file. If file or directory does not exist it being created. If file exists - it being extended.
        Logs directory is in the same directory as main.exe or main.py file. Files are defaultly placed at:
        ".../esp8266/{device id}/{date}.csv". All exceptions are made in case file will be opened while app is logging to
        it. Then it simply stops logging, but all others functionalities of application stay.
        """
        self.actual_date = self.date[-1]
        self.actual_date = self.actual_date.replace('.','-')
        self.file_loc = f'{os.path.dirname(os.path.abspath(__file__))}/logs/{self.topic}/'
        self.file = f'{self.file_loc}/{self.actual_date}.csv'
        self.exist = os.path.isfile(self.file)

        if self.exist:
            try:
                self.f = open(self.file, mode='a', newline='')
            except PermissionError:
                return

        else:
            try:
                self.f = open(self.file, mode='w', newline='')
            except FileNotFoundError:
                pathlib.Path(self.file_loc).mkdir(parents=True, exist_ok=True)
                self.f = open(self.file, mode='w', newline='')
            except PermissionError:
                return

        self.headings = ["Time [hh:mm:ss]", "Hr [bpm]", "SpO2 [%]",
                    "Temperature [°C]", "Information", "Runtime[ms]"]

        try:
            self.writer = csv.DictWriter(self.f, fieldnames=self.headings, delimiter=';')


            if not self.exist:
                self.writer.writeheader()

            try:
                for i in range(len(self.hr)):
                    self.writer.writerow({"Time [hh:mm:ss]": self.clock[i],
                                          "Hr [bpm]": self.hr[i],
                                          "SpO2 [%]": " %.2f" % self.spo2[i],
                                          "Temperature [°C]": " %.2f" % self.temperature[i],
                                          "Information": self.alarm[i],
                                          "Runtime[ms]": self.run_time[i]})
            except:
                pass

        except ValueError and AttributeError:
            return

        try:
            self.f.close()
        except:
            pass

    def show(self):
        """ "Lift" page to the top. Just show it. """
        self.lift()