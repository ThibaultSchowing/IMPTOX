from pyasn1.type.univ import Null
from GCSWrapper import GCSWrapper
from LabelboxWrapper import LabelboxWrapper
from FileWrapper import FileWrapper

# tkinter for file dialog
from tkinter import *
from tkinter import ttk, filedialog
from tkinter.filedialog import askopenfile
from tkinter.messagebox import askyesno

import os
import logging
import re
import uuid

import pandas as pd
import numpy as np




class Imptox:
    """Main class for imptox project
    """

    #TODO: two lists (one for Lb and one for GCS) to keep track of data in both places (CRUD)

    def __init__(self, config_file):
        self.gcs = GCSWrapper(config_file)     #TODO: handle exception
        self.lb = LabelboxWrapper(config_file) #TODO: handle exception

        # Database - List of Files objects
        self.filelist = [] # List of lists
        # # TODO: SWITCH TO DICTIONNARY STRUCTURE
        self.fileslist_dict = []

        self.fileslist = [] # List of FileWrapper
        self.set_file_list()
    
    def print(self):
        """ Prints stuff"""
        print("THIS IS IMPTOX !!!")


    def set_file_list(self):
        """
        Get files from Labelbox and GCS and create the file list.
        Contains useful info like basename, and other name variants. 
        Works if files are not present in one of GCS or Labelbox
        """

        # Reset lists
        self.filelist = [] # List of lists
        self.fileslist = [] # List of FileWrapper

        # Labelbox list
        lb_list = self.lb.lb_get_datarows_list_extid()

        # Google Cloud Storage list - Remove directories 
        is_file_regex = re.compile(r".*/$") # Removes directories
        gcs_list = [i for i in self.gcs.gcs_get_bucket_blobs_name_list() if not is_file_regex.match(i)]

        #column_names = ['Local Path', 'Basename', 'GCS Path', 'GCS Url', 'Labelbox extid']

        # Get the files from GCS, if only in GCS, should be uploaded in LB (or deleted)
        for gcs_path in gcs_list:
            localpath = ""
            # Path , filename => withtout the /
            gcs_directory, basename = os.path.split(gcs_path)
            gcs_url = "gs://" + self.gcs.GCS_BUCKET_NAME + "/" + gcs_directory + "/" + basename

            # Check if the file is present in Labelbox
            if(basename in lb_list):
                lb_extid = basename
            else:
                # The file is in GCS but not in Labelbox
                lb_extid = "" # Later check if empty to remove

            # Add the file to the file list
            logging.info(f"File {basename} added to list.")
            self.filelist.append([localpath, basename, gcs_path, gcs_url, lb_extid])
        
        # Get the files from labelbox -> if only in labelbox, should be deleted
        lb_extid_list_in_gcs = [a[4] for a in self.filelist] # Labelbox extid from GCS
        for lb_extid in lb_list: # For every extid from Labelbox
            basename = lb_extid # The file in Labelbox have no directories
            if(lb_extid in lb_extid_list_in_gcs): # The file already exists in the table
                print(f"---File {lb_extid} is already in the table.")
                continue
            else: # The file exists only in Labelbox
                print(f"---File only in LB: {lb_extid}.")
                localpath = ""
                self.filelist.append([localpath, basename, "", "", lb_extid])

        for l in self.filelist:
            # logging.info(f"File> {l}")
            self.fileslist.append(FileWrapper(l[0], l[1], l[2], l[3], l[4]))
            self.fileslist_dict.append( 
                                        {
                                            'ID': uuid.uuid1(), 
                                            'Localpath': localpath, 
                                            'Basename': basename,
                                            'GCS_path': gcs_path,
                                            'GCS_url':gcs_url,
                                            'LB_extid':lb_extid
                                        }
                                       )

        logging.info("Remote file list generated. ")
        return

    def get_files_list(self):
        """Returns a list of FileWrapper"""
        self.set_file_list() # Update the list
        return self.fileslist
    
    def get_files_list_dict(self):
        """Returns a list of dictionnaries"""
        self.set_file_list() # Update the list
        return self.fileslist_dict


    def imp_upload_file_to_labelbox(self, file: FileWrapper):
        """Upload a file already present in GSC to Labelbox"""
        
        if not self.file_exists_in_bucket_file(file):
            logging.warning("The file should exist in GCS first. ")
            return(Null)
        
        
        filename = file.get_lb_extid()
        
        logging.debug(f"Uploading {filename} to Labelbox: ")

        try:
            self.lb.lb_create_datarow(row_data=file.get_gcs_url(), external_id=filename)
        except:
            logging.error(f"Something went wrong while uploading to Labelbox.")
            return False

        self.set_file_list() # Update the list
        return self.file_exists_in_dataset_file(file)


    def imp_delete_file_FW(self, file: FileWrapper):
        
        basename = file.get_basename()
        gcs_url = file.get_gcs_url()
        blob_name = file.get_gcs_path()

        logging.info(f"Deleting file {basename} stored at {gcs_url} with blobname {blob_name}...")

        try:
            #if(basename in self.lb.lb_get_datarows_list_extid()): # TODO replace with data_row_for_external_id()
            if(self.lb.lb_is_in_dataset(basename)):
                logging.info(f"Removing file from Labelbox with param {gcs_url} and {basename}")
                self.lb.lb_delete_datarow(gcs_url, basename)
            else:
                logging.warning(f"File {basename} is not in Labelbox dataset.")
            
            if(gcs_url in self.gcs.gcs_get_blob_URI_list()):
                logging.info(f"Removing file from Google Cloud")
                self.gcs.gcs_delete_blob(blob_name)
            else:
                logging.warning(f"File {basename} not in Google Drive Storage bucket.")

        except Exception as e:
            print(f"Deletion failed: {e}")

        return Null

    def imp_delete_file_labelbox_FW(self, file: FileWrapper):
        
        basename = file.get_basename()
        gcs_url = file.get_gcs_url()
        blob_name = file.get_gcs_path()

        logging.info(f"Deleting file {basename} stored at {gcs_url} with blobname {blob_name}...")

        try:
            #if(basename in self.lb.lb_get_datarows_list_extid()): # TODO replace with data_row_for_external_id()
            if(self.lb.lb_is_in_dataset(basename)):
                logging.info(f"Removing file from Labelbox with param {gcs_url} and {basename}")
                self.lb.lb_delete_datarow(gcs_url, basename)
            else:
                logging.warning(f"File {basename} is not in Labelbox dataset.")
            

        except Exception as e:
            print(f"Deletion failed: {e}")

        return Null

    def imp_delete_file_gcs_FW(self, file: FileWrapper):
        basename = file.get_basename()
        gcs_url = file.get_gcs_url()
        blob_name = file.get_gcs_path()

        logging.info(f"Deleting file {basename} stored at {gcs_url} with blobname {blob_name}...")

        try:
            if(gcs_url in self.gcs.gcs_get_blob_URI_list()):
                logging.info(f"Removing file from Google Cloud")
                self.gcs.gcs_delete_blob(blob_name)
            else:
                logging.warning(f"File {basename} not in Google Drive Storage bucket.")

        except Exception as e:
            print(f"Deletion failed: {e}")

        return Null





    def file_exists_in_bucket_str(self, gcs_filename: str):
        """ Return T/F if file exists in the bucket. 
        -gcs_file_name: 'dir/file.ext'
        """
        logging.debug("Checking if " + str(gcs_filename) + " exists in bucket.")
        return gcs_filename in self.gcs.gcs_get_bucket_blobs_name_list()
    
    def file_exists_in_bucket_file(self, file: FileWrapper):
        """ Return T/F if file exists in the bucket. 
        -gcs_file_name: 'dir/file.ext'
        """
        logging.debug("Checking if " + str(file.get_gcs_path) + " exists in bucket.")
        return file.get_gcs_path in self.gcs.gcs_get_bucket_blobs_name_list()


    def file_exists_in_dataset_str(self, filename: str):
        """ Return T/F if the file exists in the LB dataset. 
        -filename: Filename -> external id. Simply the filename, without the GCS directory path. 
        """
        logging.debug("Checking if " + str(filename) + " exists in dataset.")
        return(filename in self.lb.lb_get_datarows_list_extid())
    
    def file_exists_in_dataset_file(self, file: FileWrapper):
        """ Return T/F if the file exists in the LB dataset. 
        -filename: Filename -> external id. Simply the filename, without the GCS directory path. 
        """
        logging.debug("Checking if " + str(file.get_lb_extid) + " exists in dataset.")
        return(file.get_lb_extid in self.lb.lb_get_datarows_list_extid())

    # def imp_upload_file_to_labelbox(self, gcs_filename):
    #     """Upload a file already present in GSC to Labelbox"""
    #     is_in_gcs = self.file_exists_in_bucket(gcs_filename)
    #     if not is_in_gcs:
    #         logging.warning("The file should exist in GCS first. ")
    #         return(Null)
        
    #     # From the GCS file, get the filename for Labelbox entry.
    #     filename = os.path.basename(gcs_filename)
        
    #     logging.debug("imp_upload_file_to_labelbox: ")
    #     logging.debug("Filename: " + filename + " - " + str(type(filename)))
    #     logging.debug("gcs_filename: " + gcs_filename + " - " + str(type(gcs_filename)))

    #     self.lb.lb_create_datarow(row_data="gs://" + self.gcs.GCS_BUCKET_NAME + "/" + gcs_filename, external_id=filename)

    #     return self.file_exists_in_dataset(filename)

    def imp_get_sync_list(self):
        """Returns the list of images both in LB and GCS."""
        gcs_list = self.gcs.gcs_get_bucket_blobs_name_list() # directory/image.ext
        gcs_list = [os.path.basename(e) for e in gcs_list] # we take only the basename to make them unique. Add gcs_dir later for CRUD.
        gcs_list = [e for e in gcs_list if e != ''] # remove empty elements (directory elements)
        lb_list = self.lb.lb_get_datarows_list_extid() # image.ext

        return list(set(gcs_list + lb_list))
        

    # def imp_upload_file_prompt(self, filepath):
        """Upload a file to Google Cloud Storage as well as in Labelbox. Prompt for file selection.
        -  
        """
        

        # The filename will represent the actual file in both location and therefore must be unique. 
        filename = os.path.basename(filepath)

        # Get the filename for GCS, which includes the directory. 
        gcs_filename = self.gcs.gcs_get_bucket_dir() + "/" + filename

        #TODO verifications on path
        #TODO file preprocessing e.g. convertion
        #TODO VERIFY IF IT EXISTS IN BOTH BUCKET AND LABELBOX !!

        
        # Check if the file already exists in the bucket
        # TODO: for now we suppose that if it is in the bucket, it is in labelbox. CRUD to be done.
        is_in_gcs = self.file_exists_in_bucket(gcs_filename)
        is_in_lb = self.file_exists_in_dataset(filename)

        print("File exists in dataset: " + str(is_in_lb))

        if is_in_gcs:
            # It is in GCS. If it is not in labelbox, use check_sync() to solve the problem. 
            logging.info("File already exists. Skipping...")
        else:
            # It isn't in GCS. We thus consider that it is not in Labelbox either. 
            logging.info("File does not exist in GCS or Labelbox. Adding...")
            logging.info("Adding to GCS...")
            logging.info("gcs_filename: " + gcs_filename)
            logging.info("filepath: " + filepath)
            self.gcs.gcs_upload_to_bucket(gcs_filename, filepath) 

            # Create the datarow in Labelbox
            logging.info("Adding to Labelbox...")
            self.lb.lb_create_datarow(self.gcs.GCS_BUCKET_PATH + gcs_filename, filename)
            
        
        return Null

    def imp_check_sync(self):
        """Verify images in both bucket/dataset. Returns true if sets are the same. 
        """

       

        # Some printable stuff
        # print(str(imptox.gcs.gcs_get_bucket_blobs_id_list()))
        # print(str(self.lb.lb_get_datarows_list_extid())) # ['istockphoto-1343808526-2048x2048.jpg']
        # print(str(self.lb.lb_get_datarows_list())) # ['https://storage.googleapis.com/storage-test-1-imptox/test1/istockphoto-1343808526-2048x2048.jpg?GoogleAccessId=gsda-ckx7a4im03km01076e0z9etdm@labelbox-193903.iam.gserviceaccount.com&Expires=1641647264&Signature=ufqu3PmwQU%2...

        # lb_list = self.lb.lb_get_datarows_list_extid()
        # prefix = self.gcs.GCS_BUCKET_DIR # Add the gcs directory 
        # lb_list = [prefix + "/" + elem for elem in lb_list]

        # logging.info("Label box content")
        # logging.info(str(lb_list))

        # logging.info("Google Cloud Storage content")
        # gcs_list = self.gcs.gcs_get_bucket_blobs_name_list()

        # # We need to remove the directories and keep only the files
        # gcs_list = [i for i in gcs_list if not i.endswith('/')]
        # logging.info(str(gcs_list))

        # if lb_list == gcs_list:
        #     return True
        # elif len(lb_list) > len(gcs_list):
        #     # We cannot add the data from labelbox to GCS. It is very unlikely to happen tho. 
        #     logging.warning("Missing data on GCS. \nLabelbox data: " + str(lb_list) + "\nGCS data: " + str(gcs_list))
        #     return False
        # elif len(lb_list) < len(gcs_list):
        #     unsync = [e for e in gcs_list if e not in lb_list]
        #     logging.warning("Missing data in Labelbox. \nAdding data: " + str(unsync))
        #     for e in unsync:
        #         self.imp_upload_file_to_labelbox(e)

        
    
    def imp_get_data(self):
        """ 
        Returns a table with all files, from Lb and GCS
        - Filename | present in GCS (directory!) | present in LB | Pre-annotation present locally | ::remote |  
        """




            
         


        





