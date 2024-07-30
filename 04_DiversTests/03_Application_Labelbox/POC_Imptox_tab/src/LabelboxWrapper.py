import labelbox
from labelbox import Dataset
from labelbox import DataRow

import yaml
import logging

class LabelboxWrapper:

    
    def __init__(self, config_file):

        # Load configuration
        conf = open(config_file)
        conf_dict = yaml.load(conf, Loader=yaml.FullLoader)

        # Init attributes
        self.config_file = config_file # Keep it for __repr__
        # self.client = labelbox.Client(api_key=conf_dict["lb_config"]["LB_API_KEY"])
        self.LB_DATASET_NAME = conf_dict["lb_config"]["LB_DATASET_NAME"]
        self.LB_PROJECT_ID = conf_dict["lb_config"]["LB_PROJECT_ID"]

        # Load API from LB conf file. 
        LB_API_KEY_PATH = conf_dict["lb_config"]["LB_API_KEY_PATH"]
        conf_lb = open(LB_API_KEY_PATH)
        conf_lb_dict = yaml.load(conf_lb, Loader=yaml.FullLoader)
        self.client = labelbox.Client(api_key=conf_lb_dict["lb_config"]["API_KEY"])



        # Get all datasets - create one if needed. 
        datasets = self.client.get_datasets(where=(Dataset.name == self.LB_DATASET_NAME)) # Type datasets: <class 'labelbox.pagination.PaginatedCollection'>
        nb_match_datasets = sum(1 for _ in datasets)
        logging.info(str(nb_match_datasets) + " datasets named " + self.LB_DATASET_NAME)
        if nb_match_datasets == 0: # If there is no dataset with this name -> create one. 
            # Create a new dataset
            logging.info("Create new dataset with name: '" + self.LB_DATASET_NAME + "'")
            self.dataset = self.client.create_dataset(name=self.LB_DATASET_NAME)
        else: # if dataset exists, take the first of the list (impossible to have more than 1 with the same name)
            logging.info("Dataset " + self.LB_DATASET_NAME + " already exists.")
            self.dataset = next(dataset for dataset in datasets)
        
        # Close configuration file
        conf.close()

    def __repr__(self):
        return f"LabelboxWrapper({self.config_file!r})"
    
    def __str__(self) -> str:
        return f"LabelboxWrapper: Configuration file {self.config_file!r}"
        

    def lb_get_project(self):
        """
        """
        return self.client.get_project(self.project_id)

    def lb_get_labels(self):
        # Export labels as a json:
        project = self.lb_get_project()
        labels = project.export_labels(download = True)
        return labels
    
    def lb_get_datarows_list(self):
        """
        """
        dataset = self.dataset
        # print("lb: Get datarows list. >Row count:" + str(dataset.row_count))
        return [row.row_data for row in dataset.data_rows()]

    def lb_get_datarows_list_extid(self):
        """
        """
        dataset = self.dataset
        # print("lb: Get datarows list extid. >Row count:" + str(dataset.row_count))
        #print(DataRow)
        return [row.external_id for row in dataset.data_rows()]


# lb_create_data_row(row_data=gcs_filename, external_id=filename)
    def lb_create_datarow(self, row_data, external_id):
        """Create the data row 
        - row_data: google storage link gs://...
        - external_id: filename
        """
        
        print("ROW_DATA = " + row_data)
        print("EXT_ID = " + external_id)
        self.dataset.create_data_row(row_data=row_data, external_id=external_id)

    def lb_create_bulk_datarows(self, assets):
        # from https://docs.labelbox.com/docs/common-sdk-methods-data-rows
        task = self.dataset.create_data_rows(assets)
        task.wait_till_done()   # Wait for the task to complete
        return


    

    # TODO test
    def lb_delete_datarow(self, row_data, external_id):
        """Delete a row in the labelbox dataset
        - row_data: lien gs://url/file
        - external_id: 
        """
        

        for row in self.dataset.data_rows():
            print(f"Run... row {row.row_data}")

            if row.external_id == external_id: # Removed row.row_data == row_data and 
                print("Delete " + row.row_data)
                print("Associated dataset", row.dataset())
                # print("Associated label(s)", next(row.labels()))
                print("External id", row.external_id)

                row.delete()
    
    def lb_is_in_dataset(self, extid):
        try:
            datarow = self.dataset.data_row_for_external_id(extid)
            return True
        except  Exception as e:
            print(f"File does not exist in Labelbox dataset: {e}")
            return False


        

