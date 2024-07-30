import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import askyesno

import logging
from pyasn1.type.univ import Null

from FileWrapper import FileWrapper
from ToolTip import CreateToolTip

class MAL_page(ttk.Frame):
    """Scroll frame with all files and various actions -> check imptox class first for data generation"""
        
    def __init__(self, *args, **kwargs):

        print("-----TAB3-----")
        self.display = args[0]
        self.root_nb = args[1]

        super().__init__(self.root_nb)

        r = 0
        while r < 50:
            self.columnconfigure(r, weight=1)
            self.rowconfigure(r, weight=1)
            r += 1

        self.imptox = self.display.imptox

        # Dict of selected ID
        self.select_dict = {}

        # TODO: List/dict of FileWrapper -> to act on files from outside scroll area options
        self.file_dict = {}

        # Create files list scroll area
        self.get_files_actions()


        

    def get_files_actions(self):
        """Get files lists from GCS and Labelbox. Executed at startup and each time a (or more TODO) files are uploaded."""
        logging.info(f"Update Tab3 get_file_actions()")
        # Dummy

        # self.label_test = Label(self, text="SOME BIG LABEL !! WOW !", width=30, anchor="w")
        # self.label_test.grid(row = 0, column = 0)

        # self.label_test2 = Label(self, text="SOME BIG LABEL Right", width=30, anchor="e")
        # self.label_test2.grid(row = 0, column = 50)

        

        # Action on selected files - Option menu
        self.label_action_selection = Label(self, text="Action on selected", anchor=W, width=30)
        self.label_action_selection.grid(row = 4, column = 0, sticky=W, padx=2, pady=2)

        self.options = ["Uncheck all", "Delete selection"]
        self.option_var = tk.StringVar(self)
        self.option_action_selection = OptionMenu(self, self.option_var, *self.options, command=self.option_changed)
        self.option_action_selection.grid(row = 4, column = 1, sticky=W, padx=2, pady=2)




        # //// Scroll area start
        text = tk.Text(self)
        text.grid(row = 5, column=0, columnspan=50, sticky="nsew")
        sb = tk.Scrollbar(self, command=text.yview)
        sb.grid(row = 5, column=50, sticky="nse")
        text.configure(yscrollcommand=sb.set)
        
        # Titles
        title1 = tk.Label(text, text="Select", width=15)
        title2 = tk.Label(text, text="Filename", width=30, padx=2, pady=2)
        title3 = tk.Label(text, text="In GCS", width=12, padx=2, pady=2)
        title4 = tk.Label(text, text="In Labelbox", width=12, padx=2, pady=2)
        title5 = tk.Label(text, text="Actions", width=30, padx=2, pady=2)
        # title6 = tk.Label(text, text="Delete", width=15, padx=2, pady=2)

        text.window_create("end", window=title1, padx=2, pady=2)
        text.window_create("end", window=title2, padx=2, pady=2)
        text.window_create("end", window=title3, padx=2, pady=2)
        text.window_create("end", window=title4, padx=2, pady=2)
        text.window_create("end", window=title5, padx=2, pady=2)
        # text.window_create("end", window=title6, padx=2, pady=2)
        
        text.insert("end", "\n")

        
        # i = 0
        for f in self.imptox.get_files_list():

            

            # Init Select box to 0
            current_id = f.get_id()
            current_basename = f.get_basename()

            # Fill dit with ID as key
            self.file_dict[current_id] = f

            ingcs = "x" if f.get_gcs_path() != "" else ""
            inlb = "x" if f.get_lb_extid() != "" else ""

            #print(f"\n-------------------\nGenerating row. {current_basename}")

            # Contains the ID and 1 or 0 if it is selected or not
            self.select_dict[current_id] = 0


            # button_del_lb = tk.Button(text, text=str(f"Del. of Labelbox"), command=lambda ffile = f.get_lb_extid(): self.action_delete_labelbox(ffile))
            # button_del_gcs = tk.Button(text, text=str(f"Del. of GCS"), command=lambda f_gcs_path = f.get_gcs_path(): self.action_delete_GCS(f_gcs_path))
            button_del_file = tk.Button(text, text="Delete", command=lambda fileFW = f: self.action_delete_file(fileFW))
            check_var = tk.IntVar() 
            chkbtn1 = tk.Checkbutton(   text, 
                                        width=12, 
                                        text='',variable=check_var, 
                                        onvalue=1, offvalue=0, 
                                        command=lambda ffile = current_id, chk = check_var: self.update_selection(chk, ffile))

            

            

            lbl2 = tk.Label(text, text=str(current_basename), width=30, padx=2, pady=2, anchor='w')
            CreateToolTip(lbl2, text = f"Filename: {current_basename}")

            lbl3 = tk.Label(text, text=ingcs, width=12, padx=2, pady=2)
            lbl4 = tk.Label(text, text=inlb, width=12, padx=2, pady=2)

            
            text.window_create("end", window=chkbtn1, padx=2, pady=2)
            text.window_create("end", window=lbl2,    padx=2, pady=2)
            text.window_create("end", window=lbl3,    padx=2, pady=2)
            text.window_create("end", window=lbl4,    padx=2, pady=2)
            text.window_create("end", window=button_del_file, padx=2, pady=2)

            text.insert("end", "\n")
            # i = i + 1
        text.configure(state="disabled")
        
        # //// Scroll area end
        return

    def action_delete_file(self,  file: FileWrapper):
        """Delete file from labelbox and GCS"""
        logging.info(f"Action delete initiated for file {file.get_basename()}")
        answer = askyesno(title='confirmation', message=f'Are you sure that you want remove {file.get_basename()} from Labelbox?')
        if(answer):
            logging.info(f"Action confirmed: delete file {file.get_basename()}")
            try:
                self.imptox.imp_delete_file_FW(file)
                # Refresh the list
                self.get_files_actions()
            except:
                # Refresh the list
                self.get_files_actions()
                logging.warning(f"<action> Failed to delete file {file.get_basename()}")
        else:
            logging.info("Deletion canceled.")
            return

    def action_delete_labelbox(self,  file: FileWrapper):
        """Delete a file from the Labelbox dataset only. Takes FileWrapper as input
        """
        print(f"Action delete labelbox for file {file.get_basename}")
        answer = askyesno(title='confirmation', message='Are you sure that you want remove {extid} from Labelbox?')
        if(answer):
            # check if extid exists
            try:
                self.imptox.imp_delete_file_labelbox_FW(file)
                # Refresh the list
                self.get_files_actions()
            except:
                self.get_files_actions()
        else:
            logging.info("Deletion canceled.")
            return
            
        # Refresh the list
        self.get_files_actions()
        return     

    def action_delete_GCS(self, file: FileWrapper):
        """Delete a file from the GCS bucket only. Takes FileWrapper as input
        """
        print(f"Action delete GCS for file {file.get_gcs_url}")
        answer = askyesno(title='confirmation', message='Are you sure that you want to remove {gcs_fname} from Google Cloud Storage?')
        if(answer):
            # check if extid exists
            try:
                self.imptox.imp_delete_file_gcs_FW(file)
                # Refresh the list
                self.get_files_actions()
            except:
                self.get_files_actions()
        else:
            logging.info("Deletion canceled.")
            return
        # Refresh the list
        self.get_files_actions()
        return  
        

    def update_selection(self, status, file_id):
        """Update the selection list for each file
        """
        logging.info("ID: " + str(file_id) + " --- Status: " + str(status))
        
        self.select_dict[file_id] = status.get() #tk.IntVar need .get to have the int value
        
        logging.info("Selection Update")
        print(str(self.select_dict))
        return
    
    def option_changed(self, *args): 
        '''When selecting an option for selected files, prompt yes/no and execute the action. 
        '''
        selected = self.option_var.get() 
        # logging.DEBUG(f"You selected: {str(self.option_var.get())}")
        print(f"You selected the option: {self.option_var.get()}")
        # print(f"Liste selected: {self.select_dict}")


        if selected == "Delete selection": # Action DELETE on selected file
            print("deleteeeuuuu")
            print(f"All keys: {[(g,v) for g,v in self.select_dict.items()]}")
            files_to_delete = [k for k,v in self.select_dict.items() if v == 1]
            answer = askyesno(title='confirmation', message=f'Are you sure that you want to definitively delete the {len(files_to_delete)} selected files from Google Cloud Storage and Labelbox?')
            for ids in files_to_delete:
                print(f"Ids of selected files: {ids}")
                filew = self.file_dict.get(ids, "no file")
                print(f"File: {filew.get_basename()}")

        elif selected == "Uncheck all": # Set all values of self.select_dict to 0
            print("uncheckeuuuu")
            # Reset all dict values to 0
            self.select_dict = dict.fromkeys(self.select_dict, 0)
        elif selected == "Check all":
            print("checkeuuuu")


    def start_loadNN(self):
        """Updates the labels before loading the file."""
        self.button_NN['text'] = "Loading..."
        self.label_load_NN['text'] = "Loading..."
        self.loadNN()
        return
    





