
import logging
import traceback
import matplotlib.pyplot as plt
import datetime
import json
import os
import shutil
import re
import fnmatch
from PIL import Image
import numpy as np
from pycococreatortools import pycococreatortools
import cv2
import tifffile
# https://forum.image.sc/t/tiff-file-that-can-be-opened-in-fiji-but-not-python-matlab-due-to-offset-related-error/59483
from pprint import pprint

from imgann import Sample
from imgann import Convertor

class IMPTOXconverter:
    """
    File: IMPTOXconverter.py
    
    Goal:   Converts binary masks to CoCo annotations. 
            Used to convert Apeer mask predictions to image annotations used to train Detectron2 NN
    
    Source: https://github.com/waspinator/pycococreator/tree/master/examples/shapes
    
    IMPORTANT:
     - Images and annotations must be named identically (except extension), in two separate directories.
    
    
    Structure example: 
    
            
            └── particles
                └── train (root_dir)
                    └── annotations_PNG : contains .PNG masks, one per image matching the particles frame from tiff img
                    └── annotations_inst : contains the processed .PNG masks, one per particle
                    └── annotations_tiff : contains the tiff annotations from Apeer (one per image)
                    └── particles_train2022 : contains the .jpg images matching the Annotation name as above
    
    Parameters: 
    - root_dir: base directory containing the three following
    - image_dir: name of the directory where the images are stored
    - semantic_mask_dir: name of the directory where the binary masks are located. (one mask per image)
    - instance_mask_dir: name of the directory where the binary masks instance annotations are
                         or will be located (one mask per particle)
    
    Note: 
        Works for one unique class - binary masks
        
        # pycococreatortools is needed
        
        #!pip install git+git://github.com/waspinator/pycococreator.git@0.2.0
        #!pip install git+git://github.com/waspinator/coco.git@2.1.0
        # Failed -> Downloaded manually and execute pip install. 
        
    Usage:
    
        converter = mask2coco(
        "./data/particles/trainsmall", -> root folder     
        "particles_train2022",         -> images          
        "annotations_tiff",            -> tif annotations
        "annotations_PNG",             
        "annotations_inst")
        
        converter.process_semantic_annotations()  => creates PNG annotations from .tif
        
                                                  TODO: create one background PNG (check waspinator naming conv.)
                                                       -> might be done in split_image_annotations() NO
                                                       -> DO in TIF -> FRAMES
        
        
        converter.split_image_annotations()       => split the annotations images for instance segmentation
        
        
        converter.test_image_annotation_match()   => Test (print) that the annotations match the right images
        
        
        converter.create_coco_annotations()       => Create dict{} variable
        
        
        converter.write_coco_annotations("file.json") => write the coco annotation dict. to file.
         



"""
    
    def __init__(self, 
                 root_dir, 
                 image_dir, 
                 semantic_mask_dir, 
                 semantic_processed_mask_dir, 
                 instance_mask_dir,
                 annot_coco_dir = "annotations_coco",
                 annot_voc_dir = "annotations_voc"):
        
        
        self._root_dir = root_dir
        self._semantic_mask_dir =           os.path.join(self._root_dir, semantic_mask_dir)
        self._semantic_processed_mask_dir = os.path.join(self._root_dir, semantic_processed_mask_dir)
        self._image_dir =                   os.path.join(self._root_dir, image_dir)
        self._instance_mask_dir =           os.path.join(self._root_dir, instance_mask_dir)
        self._annot_coco_dir =              os.path.join(self._root_dir, annot_coco_dir)
        self._annot_voc_dir =               os.path.join(self._root_dir, annot_voc_dir)

        self._coco_annotations_dict = None
        self._coco_annot_file = None
        
        
        # Create PNG full masks directory if not existing
        if not os.path.exists(self._semantic_processed_mask_dir):
            os.makedirs(self._semantic_processed_mask_dir)
            print(f"The new directory {self._semantic_processed_mask_dir} is created!")
        
        
        # Create instance mask directory if not existing
        if not os.path.exists(self._instance_mask_dir):
            os.makedirs(self._instance_mask_dir)
            print(f"The new directory {self._instance_mask_dir} is created!")
        
        
        # Create voc annotations directory if not existing
        if not os.path.exists(self._annot_voc_dir):
            os.makedirs(self._annot_voc_dir)
            print(f"The new directory {self._annot_voc_dir} is created!")
        
        
        # Create coco annotations directory if not existing
        if not os.path.exists(self._annot_coco_dir):
            os.makedirs(self._annot_coco_dir)
            print(f"The new directory {self._annot_coco_dir} is created!")
        
        
    def __repr__(self):
        return f"mask2coco({self._root_dir!r}, {self._image_dir!r}, {self._semantic_mask_dir!r}, {self._annot_coco_dir!r})"

    def __str__(self):
        
        ret = f"""
        \tRoot directory: {self._root_dir} 
        \tImage directory: {self._image_dir} - {len(os.listdir(self._image_dir))} images
        \tApeer masks directory: {self._semantic_mask_dir} - {len(os.listdir(self._semantic_mask_dir))} images
        \tProcessed masks directory: {self._semantic_processed_mask_dir} - {len(os.listdir(self._semantic_processed_mask_dir))} images
        \tInstance masks directory: {self._instance_mask_dir} - {len(os.listdir(self._instance_mask_dir))} images
        \tCoCo annotations directory: {self._annot_coco_dir} - {len(os.listdir(self._annot_coco_dir))} annotation files
        \tVOC annotations directory: {self._annot_voc_dir} - {len(os.listdir(self._annot_voc_dir))} VOC annotation files
        
        """
        
        return ret
        
    
    @property
    def root_dir(self):
        return self._root_dir
    
    @property
    def semantic_mask_dir(self):
        return self._semantic_mask_dir
    
    @property
    def semantic_processed_mask_dir(self):
        return self._semantic_processed_mask_dir
    
    @property
    def image_dir(self):
        return self._image_dir
    
    @property
    def instance_mask_dir(self):
        return self._instance_mask_dir
    
    @property
    def annot_voc_dir(self):
        return self._annot_voc_dir
    
    
    #--------------------------------------
    @root_dir.setter
    def root_dir(self, value):
        self._root_dir = value
    
    @semantic_mask_dir.setter
    def semantic_mask_dir(self, value):
        self._semantic_mask_dir = value
    
    @semantic_processed_mask_dir.setter
    def semantic_processed_mask_dir(self, value):
        self._semantic_processed_mask_dir = value
        
    @image_dir.setter
    def image_dir(self, value):
        self._image_dir = value
        
    @instance_mask_dir.setter
    def instance_mask_dir(self, value):
        self._instance_mask_dir = value
        
    @annot_voc_dir.setter
    def annot_voc_dir(self, value):
        self._annot_voc_dir = value
        
    
    
    def _filter_for_jpeg(self, root, files):
        """
        Parameters:
         - root: concerned directory
         - files: list of files in the root directory
        Returns a list of files in directory "root" matching the types in the file_types list
        
        Info: https://docs.python.org/3/library/fnmatch.html
        """
        file_types = ['*.jpeg', '*.jpg']
        file_types = r'|'.join([fnmatch.translate(x) for x in file_types])
        files = [os.path.join(root, f) for f in files]
        files = [f for f in files if re.match(file_types, f)]
        
        return files
    
    
    # Probable need to adapt it to your own naming convention
    
    def _filter_for_annotations(self, root, files, image_filename, v=False):
        """
        Returns annotations file list containing "image_filename"
        
        Parameters:
         - root: instance annotations PNG directory
         - files: all the instance annotations file names
         - original image file name -> find regex match in the files list
        """
        file_types = ['*.PNG']
        file_types = r'|'.join([fnmatch.translate(x) for x in file_types])
        
        # Image base name
        basename_no_extension = os.path.splitext(os.path.basename(image_filename))[0]
        
        if v: 
            print(f"Basename no extension: {basename_no_extension}")
        
        file_name_prefix = basename_no_extension + '_'
        

        files = [os.path.join(root, f) for f in files] # List of all annotation files (with path)

        if v:
            print(f"\n\nFilter annot prefix: {file_name_prefix}\n\n")

        # Add annotation files to the list (one only should match per particle)
        files = [f for f in files if file_name_prefix in os.path.splitext(os.path.basename(f))[0]]

        return files
    
    
    def get_islands(self, img):
        """
        From a binarry image, generate one image (nparray) per component (island)
        """
        
        n, labels = cv2.connectedComponents(img.astype('uint8'))
        print(n)
        islands = [labels == i for i in range(1, n)]
        return islands
    
    
    def clean_data(self, confirm=False):
        """
        Delete processed files and created annotations
        TODO: Clean all, or clean only "temporary files" like splitted images. 
        """
        if confirm:
            
            for folder in [self._annot_voc_dir, 
                           self._annot_coco_dir, 
                           self._instance_mask_dir, 
                           self._semantic_processed_mask_dir]:
            
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    try:  
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as error:
                        print(f'Failed to delete {file_path}. Reason: {error}')
        
            return 1
        
        print("Confirm deletion. ")
        return 0
    
    def process_semantic_annotations(self, particle_frame_nr=1, background_frame_nr=0, v=False):
        """
        Tiff -> PNG annotations
        Process the tiff masks to take the right frame and prepare to create the islands in split_image_annotations
        Creates a directory self._semantic_processed_mask_dir to put the new PNG processed images
        
        Parameters: 
        - frame_nr=1: frame from the .tiff image to take, by default the second. 
        
        
        TODO: 
        
            Revoir https://patrickwasp.com/create-your-own-coco-style-dataset/
            
            Ajouter object_class_name dans le nom de fichier
            Traiter chaque frame pour produire les annotations pour le background. 
            
        """
        
         
        
        # List of all tiff masks with all particles
        fullmaskimg_list = [img for img in os.listdir(self._semantic_mask_dir) if ".tiff" in img]
        
        total = len(fullmaskimg_list)
        if v:
            print(f"Full tiff mask list: {fullmaskimg_list}")
        
        # For all tiff full mask
        for i, img_filename in enumerate(fullmaskimg_list):
            if v:
                print("---------------------------------")
                print(f"     Processing full tiff mask {img_filename} - {i} / {total}")
                print("---------------------------------")
            
            # Path to the tiff image
            impath = os.path.join(self._semantic_mask_dir, img_filename)
            
            frames = []
            with tifffile.TiffFile(impath) as tif:
                try:
                    for page in tif.pages:
                        frames.append(page.asarray())

                except Exception:
                    pass
            
            
            
            # We take the second stack, matching the particles
            particle_stack = np.stack(frames)
            if v:
                print(f"Frames dimentions: {particle_stack.shape} - {type(particle_stack)}")
            
            # Get the right frame
            particles = particle_stack[particle_frame_nr]
            
            # Save image
            im = Image.fromarray(particles)
            file_basename = os.path.basename(impath).split('.')[0] # remove extension
            save_path = os.path.join(self._semantic_processed_mask_dir, file_basename + ".PNG")
            if v:
                print("Save to: ", save_path)
            im.save(save_path, quality=100)
            
            # TODO: Same for Background (here or in split_image_annotations) ?
            # background = particle_stack[background_frame_nr]
            
        
        
    def split_image_annotations(self, v=True, force=False):
        """
            Splits a semantic annotation binary image into one image per particle's instance segmentation
            Parameters: 
            - v: If True = verbose mode
            - force: = If True, recreate images if already exist
            
        """
        
        fullmaskimg_list = [img for img in os.listdir(self._semantic_processed_mask_dir) if ".PNG" in img]
        
        if v:
            print(fullmaskimg_list)
        
        
        
        if v:
            print(f"All masks: {fullmaskimg_list}")
        
        total = len(fullmaskimg_list)
        
        # Loop through all PNG (converted from tiff) annotation images.
        
        for i, fullmaskimg in enumerate(fullmaskimg_list):
            if v:
                print("---------------------------------")
                print(f"     Processing mask {i+1} / {total}")
                print("---------------------------------")


            particles_img = cv2.imread(os.path.join(self._semantic_processed_mask_dir, fullmaskimg), cv2.IMREAD_GRAYSCALE)
            if v:
                print(f"Image: {fullmaskimg}")
                print(f"Image dimention: {particles_img.shape}")

            # Get list of images, containing one island (particle) each.
            particle_islands = self.get_islands(particles_img)
            
            

            # For each island (particle), save a separate image file
            for j, island in enumerate(particle_islands):
                if v:
                    print(f"==== Processing island {j+1} / {len(particle_islands)} ====")
                
                # This part should be valid if the pycococreator naming is respected
                new_name = fullmaskimg.split(".")[0] + "_particle_" + str(j) + ".PNG"
                
                # Save new image to the instance_mask_dir
                island_img_path = os.path.join(self._instance_mask_dir, new_name)
                if v:
                    print(f"Island {j} path: {island_img_path}")
                
                # If Force is true or file doesnt exist, create the files
                if (os.path.exists(island_img_path) and force) or (not os.path.exists(island_img_path)):                        
                    # Save image
                    img_island = Image.fromarray(island)
                    img_island.save(island_img_path, quality=100)
                
                else:
                    if v:
                        print("Image already exist.")
            
            ################################################################################
            # Create background image (inverted b/W image)
            background_img = (255 - particles_img)
            
            plt.imshow(background_img)
            plt.show()
            
            # #TODO: remove this, background should be semantic, not instance segmentation.

            # n2, labels2 = cv2.connectedComponents(background_img.astype('uint8'))
            # print(f"n2: {labels2}")
            # background_islands = [labels2 == i for i in range(1, n2)]
            
            
            
            # # for each (most likely one) island of background
            # for j, island in enumerate(background_islands):
            #     if v:
            #         print(f"Processing mask {j}.")
                
            #     # This part should be valid if the pycococreator naming is respected
            #     new_name = fullmaskimg.split(".")[0] + "_background_" + str(j) + ".PNG"
                
            #     # Save new image to the instance_mask_dir
            #     island_img_path = os.path.join(self._instance_mask_dir, new_name)
                
            #     img_island = Image.fromarray(island)
            #     img_island.save(island_img_path, quality=100)
                
            ################################################################################
                                                                   
                                                                   
                                                                   
    def test_image_annotation_match(self, max_image = 2):
        """
        Shows the images and the matching annotations. Allows to check that the match is correct before generating the
            annotations file. The function is by definition verbose.
        
        Parameters:
        - max_image: stops after max_image images to avoid too long runtime. In most case 10 should be enough
                     if the naming convention (image name == annotation name: all unique)
        
        """
        print("Test images - annotation correct match")
        print(self._image_dir)
        print(self._instance_mask_dir)
        print(self._semantic_processed_mask_dir)
        
        
        for _, _, files in os.walk(self._image_dir):
            print("______________________________________________________________")
            image_files = self._filter_for_jpeg(self._image_dir, files)
            
            #print(f"\n\nImage files: {image_files}")

            # go through each image
            for n, image_filename in enumerate(image_files):

                # filter for associated png annotations
                for _, _, annot in os.walk(self._instance_mask_dir):
                    print("\n\n-------------------------------------------------------\n")
                    print("Check for annotations with : ")
                    print(f"--- Instance masks folder : {self._instance_mask_dir}")
                    print(f"--- Image                 : {image_filename}")
                    
                    
                    annotation_files = self._filter_for_annotations(self._instance_mask_dir, annot, image_filename) # PROBLEM HERE - Too Much Files
                    #print(f"Annotation files: {annotation_files}")
                    print("Annotation files: \n\n")
                    pprint(annotation_files)
                    
                if n := n + 1 >= max_image:
                    # Stops after max_image images. 
                    break
        
        return 1
    
    def create_coco_annotations(self, v=False):
        """
        Create the annotation object variable. 
        Run the test first to check for files validity !
        
        Parameters: 
            - v: If True = verbose mode
        
        """
        
        INFO = {
            "description": "Particle Dataset",
            "url": "https://github.com/waspinator/pycococreator",
            "version": "0.1.0",
            "year": 2022,
            "contributor": "waspinator",
            "date_created": datetime.datetime.utcnow().isoformat(' ')
        }

        LICENSES = [
            {
                "id": 1,
                "name": "Attribution-NonCommercial-ShareAlike License",
                "url": "http://creativecommons.org/licenses/by-nc-sa/2.0/"
            }
        ]
        
        # TODO: ajouter catégories ici (background) ?????
        CATEGORIES = [
            {
                'id': 1,
                'name': 'particle',
                'supercategory': 'particles',
            },
            {
                'id': 2,
                'name': 'background',
                'supercategory': 'background'
            }
        ]
        
        coco_output = {
            "info": INFO,
            "licenses": LICENSES,
            "categories": CATEGORIES,
            "images": [],
            "annotations": []
        }
        
        image_id = 1
        segmentation_id = 1
        
        for _, _, files in os.walk(self._image_dir):
            
            image_files = self._filter_for_jpeg(self._image_dir, files)

            # go through each image
            for n, image_filename in enumerate(image_files):
                
                image = Image.open(image_filename)
                image_info = pycococreatortools.create_image_info(
                    image_id, 
                    os.path.basename(image_filename), 
                    image.size)
                coco_output["images"].append(image_info)

                # filter for associated png annotations
                for _, _, annot in os.walk(self._instance_mask_dir):
                    if v:
                        print("\n\n-------------------------------------------------------\n")
                        print("Check for annotations with : ")
                        print(f"--- Instance masks folder : {self._instance_mask_dir}")
                        print(f"--- Image                 : {image_filename}")
                    
                    
                    annotation_files = self._filter_for_annotations(self._instance_mask_dir, annot, image_filename) # PROBLEM HERE - Too Much Files
                    
                    # go through each associated annotation
                    for annotation_filename in annotation_files:

                        #print(f"Annotation filename: {annotation_filename}")
                        
                        # Check if "particles" is in the filename
                        class_id = [x['id'] for x in CATEGORIES if x['name'] in annotation_filename][0]
                        
                        if v:
                            print(f"Class_id: {class_id}")

                        category_info = {'id': class_id, 'is_crowd': 'crowd' in image_filename}
                        #category_info = {'id': class_id, 'is_crowd': 1} 
                        # Is Crowd means: don't train on it. Use semantic segmentation instead of instance.

                        binary_mask = np.asarray(Image.open(annotation_filename).convert('1')).astype(np.uint8)

                        annotation_info = pycococreatortools.create_annotation_info(
                            segmentation_id, image_id, category_info, binary_mask,
                            image.size, tolerance=2)

                        if annotation_info is not None:
                            coco_output["annotations"].append(annotation_info)
                            
                            if v:
                                print("...........Adding annotation..............")
                                print(annotation_info['image_id'])
                                print("..........................................")

                        segmentation_id = segmentation_id + 1

                image_id = image_id + 1

        #with open('{}/instances_particles_train2022.json'.format(ROOT_DIR), 'w') as output_json_file:
        #    json.dump(coco_output, output_json_file)
        print(f"Annotation dictionnary created!")
        
        self._coco_annotations_dict = coco_output
        
        return(1)
    
    def write_coco_annotations(self, filename):
        """
        Write the annotation dict to a json file. The file must be located at self._root_dir
        
        Parameters:
        - filename: filename without path.
        """
        
        
        # dict evaluate to True if not empty
        if not self._coco_annotations_dict:
            print("Coco dictionary is empty.")
        else:
            print("Writing coco annotations to file...")
            
            self._coco_annot_file = os.path.join(self._annot_coco_dir, filename)
            with open(self._coco_annot_file, mode='w', encoding='utf-8') as output_json_file:
                json.dump(self._coco_annotations_dict, output_json_file)
                
            print("Done!")
        return 1
    
    def visualize(self, type_vis):
        """
        Visualize annotations either with imgann tool or other
        visualize with coco, voc or xml ?
        """
        
        
        
        if(type_vis == "coco"):
            Sample.show_samples(self._image_dir, 
                                self._coco_annot_file, 
                                2, # number of image sample, None = all 
                                type_vis, 
                                True )
        elif(type_vis == "voc"):
            #TODO: Check if folder exist and is full.

            Sample.show_samples(self._image_dir, 
                                self._annot_voc_dir, 
                                2, # number of image sample, None = all 
                                type_vis, 
                                True )
        else:
            Sample.describe_data(self._image_dir)
        return 0
    
    
    
    def convert_coco2voc(self):
        """
        convert saved coco annotations to voc.
        """
        # https://pypi.org/project/ImgAnn/
        
        
        
        if os.path.exists(self._coco_annot_file):
            
            try:

                Convertor.coco2voc(self._image_dir,
                                   self._coco_annot_file,
                                   self._annot_voc_dir)
                return 1
            
            except Exception as error:
                logging.error(traceback.format_exc())
                print(error)
                return 0
                
        else:
            print(f"Error. The CoCo file {self._coco_annot_file} does not exist.")
            return 0
    
    
    #TODO: complete after import and CoCo annotations are correctly done. 
    def export_partial_annotations(self, rate=.1, export_dir="export_part_annot", annot_type="coco"):
        """
        Exports an annotation dataset with partially annotated images. 
        
        Annotation of "annot_type" must be present. 
        
        
        TODO: 
        - integrate background ?
        """
        
        
        # check if annotation of type "annot_type" are present
        if annot_type == "coco":
            if not os.path.exists(self._coco_annot_file):
                logging.error("COCO annotations do not exist. Cannot export partial annotations.")
                return 0
            
        elif annot_type == "voc":
            print(f"Pascal VOC annotations directory contains {len(os.listdir(self._annot_voc_dir))} annotations.")
            
            if len(os.listdir(self._annot_voc_dir)) == 0:
                logging.error("Pascal VOC annotations do not exist. Cannot export partial annotations.")
                return 0
        
        
        
        return 0
        
    
    
    
    