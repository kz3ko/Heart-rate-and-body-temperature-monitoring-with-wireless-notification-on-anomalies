import tkinter as tk
import threading
import sys
from tkinter import ttk
from tkinter import simpledialog
from page import Page
from homepage import Homepage


class Layout(tk.Frame):
    def __init__(self, *args, **kwargs):
        """
        This is initiation of Layout class which is main class of applicaction. It inheritates from tk.Frame class.
        All app managment happens here, as well as buttons and functionalities shown independently of type of page
        opened.
        """
        tk.Frame.__init__(self, *args, **kwargs)

        # Setting up two frames which are used all the time. The button frame is frame where all of the page buttons
        # are placed. Container is rest of screen. Also, app is made to work properly only on FHD display.
        self.button_frame = tk.Frame(self, height=40)
        self.container = tk.Frame(self, height=1860)
        self.button_frame.pack(anchor='nw', fill="both", expand=True)
        self.container.pack(anchor='nw', fill="both", expand=True)

        # x coord being the point from which page buttons start being placed.
        self.page_but_x = 130

        # Making instance of ttk.Style() is needed to manage some widgets form, such as text size or font type.
        self.style = ttk.Style()
        self.font = 'Segoe'

        # Maximum update time applied for updating all the stuff, such as logs, graphs, data, etc.
        self.update_time = 5000

        # Setting up the homepage, which is an instance of Homepage class. Place it in 'container' at x=0 and y=0, which
        # are actually x=0 and y=40 in whole screen.
        self.homepage = Homepage(update_time=self.update_time)
        self.homepage.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)

        # Buffor with all pages instances.
        self.pages = []

        # Amount of MQTT clients, which actually is equivalent to amount of pages.
        self.clients = 0

        # Initiation of buttons, adding one page and showing homepage again.
        self.buttons_init()
        self.add_page()
        self.homepage.show()

        # Setting new thread. Thread is a process working independently in the background. With daemon set to True it
        # the thread is killed when app is closed.
        self.loop = threading.Thread(target=self.homepage_update, daemon=True)
        self.loop.start()

    def buttons_init(self):
        """
        Declaring all buttons and placing them on the screen. These are buttons placed in buttonframe, so they are shown
        all the time.
        """
        self.buttons = []
        self.style.configure('TButton', font=('Segoe', 10))
        self.page_choose_entry_visible = False

        self.homepage_button = ttk.Button(self.button_frame, text="Main panel", style='TButton', command=self.homepage.show)
        self.add_page_button = ttk.Button(self.button_frame, text="Add", style='TButton', command=self.add_page)
        self.delete_page_button = ttk.Button(self.button_frame, text="Delete", style='TButton', command=self.delete_page)
        self.add_many_button = ttk.Button(self.button_frame, text="Add many", style='TButton', command=self.add_many)
        self.delete_many_button = ttk.Button(self.button_frame, text="Delete many", style='TButton', command=self.delete_many)

        self.delete_page_button.place(in_=self.button_frame, x=1850, y=10, width=60, height=30)
        self.add_page_button.place(in_=self.button_frame, x=1790, y=10, width=60, height=30)
        self.delete_many_button.place(in_=self.button_frame, x=1680, y=10, width=110, height=30)
        self.add_many_button.place(in_=self.button_frame, x=1590, y=10, width=90, height=30)
        self.homepage_button.place(in_=self.button_frame, x=10, y=10, width=110, height=30)

    def homepage_update(self):
        """
        Homepage update function. It checks if 'connect all' button on homepage was pressed. If it was, then it connects
        with all devices declared on pages. 'Disconnect all' works analogically. Also, this function transmits data from
        all the pages to the homepage. Thanks to that values from each Page instance can be manage in Homepage as well,
        seperately.
        """
        if self.homepage.connect_all_flag == True:
            self.connect_all()
        elif self.homepage.connect_all_flag == False:
            self.disconnect_all()

        self.homepage.connect_all_flag = None

        for i in range(self.clients):
            if self.pages[i].connected:
                data = self.pages[i].get_recent_data()
                if data != None:
                    self.homepage.data_update(data)
            else:
                continue

        # Using tk.after function. It repeates declared function every declared time. Here it runs self.homepage_update
        # every 2.5s. Thanks to running this function as a thread it is possible to use rest of app while this function
        # runs.
        self.home_update_after = self.after(int(self.update_time/2), self.homepage_update)

    def connect_all(self):
        """ Connect with all devices. """
        for i in range(self.clients):
            if self.pages[i].connected:
                continue
            else:
                self.pages[i].connect()
                self.pages[i].connected = True

    def disconnect_all(self):
        """ Disonnect with all devices. """
        for i in range(self.clients):
            if not self.pages[i].connected:
                continue
            else:
                self.pages[i].disconnect()
                self.pages[i].connected = False

    def add_page(self):
        """ Add page."""
        self.clients += 1
        page = Page(client_id=self.clients, update_time=self.update_time)
        page.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)
        self.pages.append(page)
        button = ttk.Button(text=f"{self.clients}", style='TButton', command=self.pages[self.clients-1].show)
        if self.clients <= 40:
            button.place(in_=self.button_frame, x=self.page_but_x, y=10, width=30, height=30)
        else:
            self.show_page_choose_entry()
        self.page_but_x += 30 + 2
        self.buttons.append(button)

    def show_page_choose_entry(self):
        """ Show entry box responsible for getting page ID. At default it has client ID typed in. """
        if not self.page_choose_entry_visible:
            self.page_choose_entry_visible = True
            self.entry = tk.StringVar()
            self.id_choose_entry = ttk.Entry(self, textvariable=self.entry, font=(self.font, 11, 'normal'))
            self.id_choose_button = ttk.Button(text='Open page', style='TButton',
                                               command=self.show_page_by_num)
            self.id_choose_button.place(x=1435, y=10, height=30, width=92)
            self.id_choose_entry.place(x=1527, y=10.5, height=28, width=35)
        self.entry.set(self.clients)

    def show_page_by_num(self):
        """ Show page by number typed in entrybox. """
        try:
            num = int(self.entry.get()) - 1
            self.pages[num].show()
        except IndexError:
            pass

    def hide_page_choose_entry(self):
        """ Hide page choose entry box."""
        self.page_choose_entry_visible = False
        self.id_choose_button.place_forget()
        self.id_choose_entry.place_forget()

    def add_many(self):
        """ Add many pages. It just runs add_page function declared amount of times. """
        try:
            amount = simpledialog.askstring(title="Add many", prompt="Amount of pages to add:")
            for i in range(int(amount)):
                self.add_page()
        except:
            return

    def delete_page(self):
        """ Delete page unless there is one left. """
        if self.clients < 2:
            return
        else:
            self.clients -= 1

        if self.clients <= 40 and self.page_choose_entry_visible:
            self.hide_page_choose_entry()
        elif self.page_choose_entry_visible:
            self.entry.set(self.clients)

        self.pages[-1].delete()
        self.pages = self.pages[:-1]
        self.buttons[-1].place_forget()
        self.buttons = self.buttons[:-1]
        self.page_but_x -= 30 + 2
        self.pages[self.clients-1].show()

    def delete_many(self):
        """ Delete many pages. It just runs delete_page function declared amount of times. """
        try:
            amount = simpledialog.askstring(title="Delete many", prompt="Amount of pages to delete:")
            for i in range(int(amount)):
                self.delete_page()
        except:
            return

    def close(self):
        """ Runs when app is closed. sys.exit() closes the app even after converting app to exe file.  """
        self.destroy()
        sys.exit()


if __name__ == "__main__":
    # Initiate tkinter window.
    root = tk.Tk()

    # Show window on full screen by default,
    root.state('zoomed')

    # Window is based on Layot class.
    main = Layout(root)

    # Pack the 'main' in root and basically fill whole screen with it.
    main.pack(side="top", fill="both", expand=True)

    # Set resolution of root as 1920x1080 and allow to resize, which is not recommended though.
    root.wm_geometry("1920x1080")
    root.resizable(width=True, height=True)

    # Set title of window.
    root.title('MAX30102 control panel')

    # Define function which will be called when window will be closed.
    root.protocol("WM_DELETE_WINDOW", main.close)

    # Start tkinter mainloop of root declared.
    root.mainloop()