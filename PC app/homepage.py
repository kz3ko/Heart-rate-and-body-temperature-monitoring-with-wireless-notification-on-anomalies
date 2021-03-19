import tkinter as tk
from tkinter import ttk
from graph import Bar
from numpy import mean
import threading

class Homepage(tk.Frame):
    def __init__(self, update_time, *args, **kwargs):
        """
        Initiation of Homepage responsible for displaying averaged values of all devices connected. All functions are
        made analogically to these made in page.Page class. If explaination is needed look at page.py class and searched
        function.
        """
        tk.Frame.__init__(self, *args, **kwargs)
        self.style = ttk.Style()
        self.font = 'Segoe'

        self.data_bufors_init()
        self.logs_init()
        self.buttons_init()
        self.graph_show()

        self.update_time = update_time
        self.update_loop_start()

    def update_loop_start(self):
        self.hr_update_loop = threading.Thread(target=self.hr_graph_update, daemon=True)
        self.spo2_update_loop = threading.Thread(target=self.spo2_graph_update, daemon=True)
        self.temperature_update_loop = threading.Thread(target=self.temperature_graph_update, daemon=True)

        self.hr_update_loop.start()
        self.spo2_update_loop.start()
        self.temperature_update_loop.start()

    def data_bufors_init(self):
        self.data = []
        self.id = []

    def data_update(self, data):
        if self.data == data:
            return
        self.data = data

        id = int(data[0])
        date = data[1]
        begin = data[2]
        now = data[3]
        hr = data[4]
        spo2 = data[5]
        temp = data[6]
        alarms = data[7]

        hr_avg = "%d" % mean(hr)
        spo2_avg = "%.2f" % mean(spo2)
        temp_avg = "%.2f" % mean(temp)
        time_period = f"{begin} - {now}"

        self.logs_update(id, date, time_period, hr_avg, spo2_avg, temp_avg, alarms)
        self.graph_data_update(id, hr_avg, spo2_avg, temp_avg, hr, spo2, temp)

    def graph_show(self):
        try:
            if self.graph_visible:
                return
        except AttributeError:
            pass
        self.frame = tk.Frame(self, width=1200, height=915)
        self.hr_graph = Bar(self.frame, type ='Pulse')
        self.spo2_graph = Bar(self.frame, type = 'SpO2')
        self.temperature_graph = Bar(self.frame, type = 'Temperature')
        self.frame.place(x=830, y=45)
        self.graph_visible = True

    def graph_hide(self):
        if not self.graph_visible:
            return
        self.graph_visible = False
        self.frame.place_forget()
        self.frame = None

    def graph_data_update(self, id, hr_avg, spo2_avg, temp_avg, hr, spo2, temp):
        if not self.graph_visible:
            return

        self.hr_graph.data_update(id, hr_avg, hr)
        self.spo2_graph.data_update(id, spo2_avg, spo2)
        self.temperature_graph.data_update(id, temp_avg, temp)

    def hr_graph_update(self):
        self.after(self.update_time, self.hr_graph_update)
        if not self.graph_visible:
            return

        try:
            self.hr_graph.update()
        except:
            pass

    def spo2_graph_update(self):
        self.after(self.update_time, self.spo2_graph_update)
        if not self.graph_visible:
            return

        try:
            self.spo2_graph.update()
        except:
            pass

    def temperature_graph_update(self):
        self.after(self.update_time, self.temperature_graph_update)
        if not self.graph_visible:
            return

        try:
            self.temperature_graph.update()
        except:
            pass

    def buttons_init(self):
        self.connect_all_flag = None

        self.style.configure('W.TButton', font=(self.font, 14))

        self.connect_button = ttk.Button(self, text="Connect all", style='W.TButton', command=self.connect_all)
        self.disconnect_button = ttk.Button(self, text="Disconnect all", style='W.TButton', command=self.disconnect_all)
        self.clear_logs_button = ttk.Button(self, text="Clear logs", style='W.TButton', command=self.logs_clear)
        self.show_graph_button = ttk.Button(self, text="Show graph", style='W.TButton', command=self.graph_show)
        self.hide_graph_button = ttk.Button(self, text="Hide graph", style='W.TButton', command=self.graph_hide)

        self.connect_button.place(x=10, y=10, height=35, width=140)
        self.disconnect_button.place(x=160, y=10, height=35, width=180)
        self.clear_logs_button.place(x=350, y=10, height=35, width=130)
        self.show_graph_button.place(x=1640, y=10, height=35, width=130)
        self.hide_graph_button.place(x=1780, y=10, height=35, width=130)

    def connect_all(self):
        self.connect_all_flag = True

    def disconnect_all(self):
        self.connect_all_flag = False

    def logs_init(self):
        columns_width = [30,125,180,70,70,125,200]
        width = sum(columns_width)

        self.logs = ttk.Treeview(self, selectmode='extended', style='Treeview')
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.logs.yview)

        self.logs.place(x=10, y=55, width=width, height=895) # 895/915
        self.vsb.place(x=width+10, y=55, height=895)

        self.logs_clear()

        self.logs.configure(yscrollcommand=self.vsb.set)
        self.logs.tag_configure('alarm', background='#FF3C3C')
        self.logs.tag_configure('noalarm', background='#FFFFFF')

        self.logs["columns"] = ("1", "2", "3", "4", "5", "6","7")
        self.logs['show'] = 'headings'
        headings = ["ID" ,"Date [dd:mm:yy]", "Time period [hh:mm:ss]", "Hr [bpm]",
                    "SpO2 [%]", "Temperature [°C]", "Information"]

        for id in self.logs["columns"]:
            i = int(id) - 1
            if i == 6:
                self.logs.column(id, width=columns_width[i] - 2, anchor='c')
            else:
                self.logs.column(id, width=columns_width[i], anchor='c')
            self.logs.heading(id, text=headings[i])


    def logs_update(self, id, date, time, hr, spo2, temp, alarms):
        alarm = ''
        if alarms != len(alarms) * ['-']:
            hr_done = False
            spo_done = False
            temp_done = False
            tag = 'alarm'
            for buf in alarms:
                messages = buf.split('|')
                for msg in messages:
                    if msg == 'HR_TOO_LOW' and not hr_done:
                        alarm += 'HR↓ '
                        hr_done = True
                    elif msg == 'HR_TOO_HIGH' and not hr_done:
                        alarm += 'HR↑ '
                        hr_done = True
                    elif msg == 'SPO2_TOO_LOW' and not spo_done:
                        alarm += 'SPO2↓ '
                        spo_done = True
                    elif msg == 'TEMP_TOO_HIGH' and not temp_done:
                        alarm += 'TEMPERATURE↑'
                        temp_done = True
        else:
            tag = 'noalarm'
            alarm = '-'

        values = (str(id), str(date), str(time), str(hr), str(spo2), str(temp), str(alarm))

        try:
            self.logs.delete(self.logs_items[id])
            self.logs_items[id] = self.logs.insert("", 'end', values=values, tag=tag)
        except KeyError:
            self.logs_items.update({id:self.logs.insert("", 'end', values=values, tag=tag)})

    def logs_clear(self):
        self.logs.delete(*self.logs.get_children())
        self.logs_items = {}

    def fixed_map(self, option):
        return [elm for elm in self.style.map("Treeview", query_opt=option)
                if elm[:2] != ("!disabled", "!selected")]

    def show(self):
        self.lift()