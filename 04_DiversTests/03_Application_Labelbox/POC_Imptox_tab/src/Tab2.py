import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askopenfilenames
from tkinter.ttk import Separator, Style
from tkinter.messagebox import askyesnocancel, showinfo, askyesno, showerror

from pyasn1.type.univ import Null
from pathlib import Path
import logging
import os

class File_page(ttk.Frame):
    """This will contain what is going to be shown on the second tab."""

    def __init__(self, *args, **kwargs):
        
        print("-----TAB2-----")
        # parent -> notebook 
        self.display = args[0]
        self.root_nb = args[1]

        self.path_detectron2_pth = ""
        
        super().__init__(self.root_nb)

        self.imptox = self.display.imptox 
        self.imptox.print()
        # self.imptox.create_file_list() # Moved in __init__
        # self.display.imptox.print()

        self.labelImageTitle = Label(self, text="Upload local image", width=30, height=3, anchor="w")
        self.labelImageTitle.grid(row=8, column=0, columnspan=4, padx=10, pady=10, sticky=W)

        # # TBR
        # self.labtbr = Label(self, text="... blah ...", width = 30, anchor="e")
        # self.labtbr.grid(row = 2, column=50, sticky=N+S+E+W)

        


        self.labelImage1 = Label(self, text="Choose images: ", width=30, anchor="w")
        #self.buttonImage1 = Button(self, text="Browse", width=15, command=self.browseImage)
        #self.labelImage2 = Label(self, text="...", width=70, anchor="w")
        #self.labelImage1.grid(row=9, column=0)
        #self.buttonImage1.grid(row=9, column=1, sticky=W)
        #self.labelImage2.grid(row=9, column=2, columnspan=20)
        #self.labelImageStatusGCS = Label(self, text="GCS:          No image input", width=30, anchor="w") # Status if image is present in GCS
        #self.labelImageStatusLB =  Label(self, text="Labelbox:  No image input", width=30, anchor="w") # Status if image is present in LB
        #self.labelImageStatusGCS.grid(row=13, column=0)
        #self.labelImageStatusLB.grid(row=14, column=0)

        # Button for multiple files
        self.labelImageUploadMulti = Label(self, text="Select and upload multiple files", width=30, anchor="w")
        self.labelImageUploadMulti.grid(row=15, column=0, sticky=W, padx=2, pady=2)
        self.button_multi_file = Button(self, text="Browse", width=15, anchor="w", command=self.select_files, state=ACTIVE)
        self.button_multi_file.grid(row=15, column=1, sticky=W, padx=2, pady=2)


        # Button to select Detectron .pth file
        #self.label_choose_NN = Label(self, text="Choose Neural Net:", anchor=W)
        #self.label_choose_NN.grid(row=20, column=0, sticky=W, padx=2, pady=2)
        #self.button_NN = Button(self, text="Load Neural Network", command=self.start_loadNN, state=ACTIVE)
        #self.button_NN.grid(row = 20, column = 1, sticky=W, padx=2, pady=2)
        #self.label_load_NN = Label(self, text="No .pth Detectron2 file selected.", anchor=W)
        #self.label_load_NN.grid(row = 20, column = 2, sticky=W, padx=2, pady=2)

        # self.buttonImageUpload = Button(self, text="Upload image", width=15, anchor="w", state=DISABLED, command=self.uploadImage)
        # self.buttonImageUpload.grid(row=15, column=1, sticky=W)

    
    
    def browseImage(self):
        """Get and verify the file to be loaded
        - Verify that it is not present in GCS or LB
        - Update text fields about image
        - ? preview image
        - Check GCS and LB image status (found or not)
        """
        Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        self.image_filepath = askopenfilename() # show an "Open" dialog box and return the path to the selected file

        # Update fields according to new path.
        self.check_local_image_status()   
        return

    def select_files(self):
        """Select multiple files and fill a list of files to upload, after verification of their presence-abscence"""
        Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        # Ask for files
        

        filenames = askopenfilenames(
            title='Open files',
            initialdir='.',
            filetypes=[("image", ".jpeg"),("image", ".png"),("image", ".jpg")]
        )

        showinfo(
            title='Selected Files',
            message=filenames
        )

        # TODO: switch buttons to "loading" or "verifying status"
        self.switch_upload(False)
        self.labelImageUploadMulti['text'] = "Checking files status..."

        # List of dict to uploade to labelbox (bulk)
        self.lb_assets = []
        self.gcs_assets = []
        # For each file verify if present in GCS and LB, add in tmp list / dict if present
        for filepath in filenames:
            print(f"Checking file {filepath} before adding...")
            

            # Get the filename for GCS, which includes the directory. For Labelbox, only the filename is used (external_id)
            
            image_filename = os.path.basename(filepath)
            image_gcs_filename = self.imptox.gcs.gcs_get_bucket_dir() + "/" + image_filename
            # Get the two status in dataset / GCS
            is_in_gcs = self.imptox.file_exists_in_bucket_str(image_gcs_filename)
            is_in_lb = self.imptox.file_exists_in_dataset_str(image_filename) 

            print(f"File status: GCS: {is_in_gcs}")
            print(f"File status: LB: {is_in_lb}")

            # TODO if files are not in GCS, check if they are in LB. If not, add to upload list
            if(not is_in_gcs and not is_in_lb):
                # GCS
                logging.info("File does not exist in GCS or Labelbox. Adding...")
                logging.info("Adding to GCS...")
                logging.info("gcs_filename: " + image_gcs_filename)
                logging.info("Local filepath: " + filepath)
                logging.info(f"File {image_gcs_filename} uploading...")
                self.gcs_assets.append({"gcs_filename": image_gcs_filename, "filepath": filepath})
                # upload image to gcs
                #self.imptox.gcs.gcs_upload_to_bucket(image_gcs_filename, filepath)
                logging.info(f"File {filepath} uploaded")
            

                # LB - first add to list then use bulk upload for efficiency
                #assets = [{"row_data": "https://storage.googleapis.com/labelbox-sample-datasets/Docs/basic.jpg", "external_id": str(uuid4())},
                self.lb_assets.append({"row_data": self.imptox.gcs.GCS_BUCKET_PATH + image_gcs_filename, "external_id": image_filename})
                
        answer = askyesno(title=f"Upload confirmation", message=f'Do you want to upload the file to GCS and Labelbox?\n{self.lb_assets} ')
        if answer:
            # Upload
            print("Uploading to GCS and LB...")
            for element in self.gcs_assets:
                print("Uploading to GCS...")
                print(element)
                self.imptox.gcs.gcs_upload_to_bucket(element['gcs_filename'], element['filepath'])
            print("Upload to GCS done.")

            print("Uploading to LB...")
            self.imptox.lb.lb_create_bulk_datarows(self.lb_assets)
            print("Upload to LB done.")
            
        # Upload valid files, update Tab3 
        print("Update tab 3")
        self.display.t3.get_files_actions() # Update files list on tab 3

        # Clean and quit
        self.switch_upload(True)
        self.labelImageUploadMulti['text'] = "Select and upload multiple files"



    def uploadImage(self):
        """If an image has been loaded"""
        logging.info("Upload button clicked")
        # deactivate upload button after upload
        # reset image label buttons to initial value

        logging.info("File does not exist in GCS or Labelbox. Adding...")
        logging.info("Adding to GCS...")
        logging.info("gcs_filename: " + self.image_gcs_filename)
        logging.info("Local filepath: " + self.image_filepath)
        self.imptox.gcs.gcs_upload_to_bucket(self.image_gcs_filename, self.image_filepath) 

        # Create the datarow in Labelbox
        logging.info("Adding to Labelbox...")
        logging.info("Google Storage path: " + self.imptox.gcs.GCS_BUCKET_PATH + self.image_gcs_filename)
        logging.info("External ID: " + self.image_filename)
        self.imptox.lb.lb_create_datarow(self.imptox.gcs.GCS_BUCKET_PATH + self.image_gcs_filename, self.image_filename)
        
        # Update local image status and remote file list

        self.check_local_image_status()
        
        # self.check_remote_files()
        # Show status (if error status should be "")

        self.display.t3.get_files_actions() # Update files list on tab 3

        return

    def check_local_image_status(self):
        """If image_filepath is set, update local image fields and remote image status. If remote image exists, disable upload button."""
        logging.info("Checking status of local image: " + str(self.image_filepath))

        if self.image_filepath == "":
            logging.warning("Empty/invalid filepath given! " + str(self.image_filepath))
            self.switch_upload(False)
            return
        else:
            self.labelImage2['text'] = self.image_filepath
            self.image_filename = os.path.basename(self.image_filepath)

            # Get the filename for GCS, which includes the directory. For Labelbox, only the filename is used (external_id)
            self.image_gcs_filename = self.imptox.gcs.gcs_get_bucket_dir() + "/" + self.image_filename

            # Get the two status in dataset / GCS
            is_in_gcs = self.imptox.file_exists_in_bucket_str(self.image_gcs_filename)
            is_in_lb = self.imptox.file_exists_in_dataset_str(self.image_filename)

            # Check if image is already in the databases
            self.switch_upload(False)
            if is_in_gcs == False and is_in_lb == False:
                # File doesn't exist in databases -> change labels and activate upload button.
                self.labelImageStatusGCS['text'] = "GCS:            ready to upload."
                self.labelImageStatusGCS['fg'] = "green"
                self.labelImageStatusLB['text'] =  "Labelbox:   ready to upload."
                self.labelImageStatusLB['fg'] = "green"
                self.validImageLoaded = True
                logging.info(f"ACTIVATE BUTTON")
                self.switch_upload(True)
            
            if is_in_gcs == True:
                self.labelImageStatusGCS['text'] = "GCS:           file already present"
                self.labelImageStatusGCS['fg'] = "red"
            if is_in_lb == True:
                self.labelImageStatusLB['text'] =  "Labelbox:  file already present"
                self.labelImageStatusLB['fg'] = "red"
            
        return

    def switch_upload(self, active):
        if active:
            self.button_multi_file = Button(self, text="Browse", width=15, anchor="w", command=self.select_files, state=ACTIVE)
            self.button_multi_file.grid(row=15, column=1, sticky=W, padx=2, pady=2)
        else:
            self.button_multi_file = Button(self, text="Loading...", width=15, anchor="w", state=DISABLED, command=self.select_files)
            self.button_multi_file.grid(row=15, column=1, sticky=W, padx=2, pady=2)


    def start_loadNN(self):
        """Updates the labels before loading the file."""
        self.button_NN['text'] = "Loading..."
        self.label_load_NN['text'] = "Loading..."
        self.loadNN()
        return

    def loadNN(self):
        """Load the app configuration from the yaml file and create the Imptox object as well as the different remote elements.
        """
        Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file

        # Check path
        sx = Path(filename).suffix
        logging.info("Config file suffix: " + sx)
        if sx != ".pth" or filename == "" or filename == Null:
            self.label_load_NN['text'] = "Error: Chose a valid .pth file."
            self.button_NN['text'] = "Load Neural Network"
            return 
        else:
            self.path_detectron2_pth = filename
            return