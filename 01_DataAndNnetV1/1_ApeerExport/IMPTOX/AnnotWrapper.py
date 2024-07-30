import logging
import os
import json
import shutil
from imgann import Sample
from imgann import Convertor


class AnnotWrapper:
    """
    Read annotation in a specified format (CoCo, PascalVOC,...) and export them in an other format. 


    source_dir: directory containing the images
    source_annotations: annotations file-s or directory


    CoCo -> image_dir + annot_file
    VOC -> image_dir + annot_dir


    """

    def __init__(self, base_dir, image_dir, source_annotations_dir, source_annotations_file, input_annot_type = "coco"):
        
        
        self._input_annot_type = input_annot_type
        self._accepted_formats = ["coco", "voc", "csv"]

        self._base_directory = base_dir

        self._image_dir = os.path.join(base_dir, image_dir)
        self._image_list = [os.path.abspath(x) for x in os.listdir(self._image_dir)]

        self._coco_annot_file = None
        self._coco_annot_dict = None

        self._csv_annot_dir = None
        self._csv_annot_file = None


        if self._input_annot_type == "coco": #------------------------------------------------ COCO

            #self._coco_image_dir = os.path.join(base_dir, image_dir)

            # check if the coco annotation file exists.
            if(os.path.isfile(os.path.join(base_dir, source_annotations_dir, source_annotations_file))):
                self._coco_annot_file = os.path.join(base_dir, source_annotations_dir, source_annotations_file)

                logging.info("Image directory: %s", self._image_dir)
                logging.info("Number of images: %i", len(self._image_list))
                logging.info("Coco annotation file: %s" , self._coco_annot_file)

                # Open annotation file and image directory and display basic information
                with open(self._coco_annot_file, mode='r', encoding='utf-8') as json_file:
                    self._coco_annot_dict = json.load(json_file)
                
                logging.info("Total number of annotations: %i", len(self._coco_annot_dict["annotations"]))
            
            else:
                logging.error("The file %s does not exist.", self._coco_annot_file)

        elif self._input_annot_type == "voc": #------------------------------------------------ VOC

            # Check if the voc annotations directory exists.
            if(os.path.isdir(os.path.join(base_dir, source_annotations_dir))):
                self._voc_annot_dir = os.path.join(base_dir, source_annotations_dir)
          
            logging.info("Image directory: %s", self._image_dir)
            logging.info("Voc annotation directory: %s" , self._voc_annot_dir)
        
        elif self._input_annot_type == "csv": #------------------------------------------------ CSV

            self._csv_annot_dir = os.path.join(base_dir, source_annotations_dir)
            self._csv_annot_file = os.path.join(self._csv_annot_dir, source_annotations_file)

            logging.info("Image directory: %s", self._image_dir)
            logging.info("Csv annotation directory: %s" , self._csv_annot_dir)


        else:
            logging.error("Format not in %s", self._accepted_formats)
            

    @property
    def input_annot_type(self):
        """
        Returns the original input annotation type of the wrapper
        """
        return self._input_annot_type


    def trim_coco(self, keep=0.5):
        """
        Remove part of the annotations and keeps only "keep"% of the annotation

        Saves-it it a new directory named identically as the original one for the corresponding type. 

        
        """
        #TODO first visualize and verify annotations
        

    def create_empty_dir(self, full_path):
        """
        Create an empty dir or empty dir if exists
        """
        if os.path.exists(full_path):
            try:
                if os.path.isfile(full_path) or os.path.islink(full_path):
                    os.unlink(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
            except Exception as ex:
                print('Failed to delete %s. Reason: %s', full_path, ex)
        else:
            os.makedirs(full_path)
        

    def convert_to(self, dest_format, dest_dir, dest_file=None):
        """
        Converts the original annotations to the dest format.

        """

        # Check if the format exists
        if dest_format not in self._accepted_formats:
            logging.error("Unknown annotation format.")
            return None

        # Check if the input format is the same as the destination format. If it's the case, do not delete the folder
        # input-output formats identical ?
        if dest_format == self.input_annot_type:
            # Convertion of two identical formats. -> Use trim ??
            #logging.info("Converting %s to %s", self._input_annot_type, dest_dir)
            logging.warning("Use Trim to create new partial annotations from the already converted data.")
            return None
        else:
            # We can create the destination directory or empty it.
            dest_dir_full = os.path.join(self._base_directory, dest_dir)
            logging.info("Create empty (force) directory %s", dest_dir_full)

            # create destination directory or empty if already exists
            self.create_empty_dir(dest_dir_full)
        
        logging.info("Starts convertion from %s format to %s format.", self.input_annot_type, dest_format)

        # -------- COCO -> Pascal VOC ----------
        
        if self.input_annot_type == 'coco' and dest_format == 'voc':
            logging.info("Converts coco to Pascal VOC annotations.")
            
            # The given destination directory now becomes the directory of the VOC annotations
            self._voc_annot_dir = dest_dir_full
            Convertor.coco2voc(self._image_dir, self._coco_annot_file, self._voc_annot_dir)
        
        # -------- COCO -> CSV ----------

        if self.input_annot_type == 'coco' and dest_format == 'csv':
            logging.info("Converts coco to CSV annotations")

            if dest_file is None:
                logging.error("Specify an output filename for the csv file.")
                return

            # create destination directory or empty if already exists
            self.create_empty_dir(dest_dir_full)
            self._csv_annot_dir = dest_dir_full


            self._csv_annot_file = os.path.join(dest_dir_full, dest_file)



            Convertor.coco2csv(self._image_dir, self._coco_annot_file, self._csv_annot_file)
        


        # -------- Pascal VOC -> CoCo ----------
        #TODO

        # -------- Pascal VOC -> CSV ----------
        #TODO

        # -------- CSV -> CoCo ----------
        #TODO

        # -------- CSV -> Pascal VOC ----------
        #TODO


    def visualize_sample(self, type='coco'):
        """
        Visualize random sample using available annotations.
        """
        pass
