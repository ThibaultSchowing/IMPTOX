import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.filedialog import askopenfilename

import logging
import os
from pathlib import Path, WindowsPath

from pyasn1.type.univ import Null

from Imptox import Imptox
import Tab2
import Tab3

class Config_page(ttk.Frame):
    """This will contain what is going to be shown on the first tab."""

    def __init__(self, *args, **kwargs):

        # parent -> notebook 
        print("-----TAB1-----")
        
        self.display = args[0]
        self.root_nb = args[1]
        
        # Init the frame parent class with the notebook 
        super().__init__(self.root_nb)

        self.labelTitle = Label(self, text="Configuration", anchor="w")
        self.labelTitle.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky=W)


        self.labelConf1 = Label(self, text="Conf. file: ", width=30, anchor="w")
        self.labelConf1.grid(row=1, column=0)


        # Button to select config file
        self.buttonConf1 = Button(self, text="Load", width=15, command=self.start_loadConfig, state=ACTIVE)
        self.buttonConf1.grid(row=1, column=1, sticky=W)


        # Path of config file
        self.labelConf2 = Label(self, text="...", width=50, anchor="w")
        self.labelConf2.grid(row=2, column=0)

        # Information about Labelbox and GCS services

        self.labelInfo1 = Label(self, text="IMPTOX info", width=30, height=2, anchor="w")
        self.labelInfo1.grid(row=5, column=0, columnspan=4, padx=10, pady=10, sticky=W)

        self.labelInfoGCS1 = Label(self, text="GCS: ", width=30, anchor="w")
        self.labelInfoGCS2 = Label(self, text="key_file", width=20, anchor="w")
        self.labelInfoGCS3 = Label(self, text="Status", width=50, anchor="w")
        self.labelInfoGCS1.grid(row=6, column=0)
        self.labelInfoGCS2.grid(row=6, column=1)
        self.labelInfoGCS3.grid(row=6, column=2)


        self.labelInfoLB1 = Label(self, text="Labelbox", width=30, anchor="w")
        self.labelInfoLB2 = Label(self, text="API key", width=20, anchor="w")
        self.labelInfoLB3 = Label(self, text="Status", width=50, anchor="w")
        self.labelInfoLB1.grid(row=8, column=0)
        self.labelInfoLB2.grid(row=8, column=1)
        self.labelInfoLB3.grid(row=8, column=2)


    def start_loadConfig(self):
        """Updates the labels before loading the config."""
        self.labelConf2['text'] = "Loading..."
        self.buttonConf1['text'] = "Loading..."
        self.loadConfig()
        return

    def loadConfig(self):
        """Load the app configuration from the yaml file and create the Imptox object as well as the different remote elements.
        """
        Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file

        # Check path
        sx = Path(filename).suffix
        logging.info("Config file suffix: " + sx)
        if sx != ".yaml" or filename == "" or filename == Null:
            self.labelConf2['text'] = "Error: Chose a valid .yaml file."
            return 
        else:
            self.display.imptox = Imptox(filename)

            # Inactivate load button
            self.buttonConf1['state'] = DISABLED
            self.buttonConf1['text'] = "Loaded"

            # ACTIVATE TABS

            self.display.t2 = Tab2.File_page(self.display, self.root_nb)
            self.display.t3 = Tab3.MAL_page(self.display, self.root_nb)

            self.root_nb.add(self.display.t2, text='Images')
            self.root_nb.add(self.display.t3, text='MAL')

            # Activate image button
            # => no reason to deactiate as the tab is not visible

            
            # Show filename
            self.labelConf2['text'] = filename

            # TODO: this is just nice looking but is not actually checking anything.
            self.labelInfoGCS3['text'] = "Loaded"
            self.labelInfoLB3['text'] = "Loaded"
            self.labelInfoGCS3['fg'] = "#0f0"
            self.labelInfoLB3['fg'] = "#0f0"

            
        return

    def get_imptox(self):
        return self.imptox