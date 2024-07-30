import tkinter as tk
from tkinter import ttk

import Tab1
import Tab2
import Tab3


'''
Sources: 
Tabs: https://stackoverflow.com/questions/66742312/accessing-variables-from-other-tab-in-notebook
Reference: https://stackoverflow.com/questions/36831909/how-to-display-a-value-from-children-window-to-parent-window-in-python-tkinter
En-disable tabs: https://stackoverflow.com/questions/20983309/how-to-enable-disable-tabs-in-a-tkinter-tix-python-gui
Structure: https://stackoverflow.com/questions/17466561/best-way-to-structure-a-tkinter-application/17470842#17470842
Scrollbar stuff: https://stackoverflow.com/questions/3085696/adding-a-scrollbar-to-a-group-of-widgets-in-tkinter/3092341#3092341



'''


class Display:
    def __init__(self):

        self.DISPLAY = "Can I access this text ?"
        
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.quit_me)
        self.root.title('Tab-Tester')
        self.root.geometry('1000x600')

        r = 0
        while r < 50:
            self.root.rowconfigure(r, weight=1)
            self.root.columnconfigure(r, weight=1)
            r += 1

        self.nb = ttk.Notebook(self.root)
        self.nb.grid(column=0, row=0, columnspan=50, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        self.t1 = Tab1.Config_page(self, self.nb)
        self.nb.add(self.t1, text='Configuration') # Add the tab to the notebook

        # Other tabs are added after the configuration is "completed" (no real verification yet)

        
        # self.nb.columnconfigure(0, weight=1)
        # self.nb.rowconfigure(0, weight=1)

        while r < 50:
            self.nb.columnconfigure(r, weight=1)
            self.nb.rowconfigure(r, weight=1)
            r += 1

        self.root.mainloop()


    def quit_me(self):
        print('quit')
        self.root.quit()
        self.root.destroy()

display = Display()
