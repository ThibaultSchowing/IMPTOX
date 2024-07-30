from google.cloud import storage
import yaml
import logging


class GCSWrapper:
    """Wrapper for Google Cloud Services API

    ...

    Attributes
    ----------
    GCS_PROJECT_ID : str
        Main project's name. 
    GCS_PROJECT_NUMBER : str
        Main project number (equivalent to ID)
    GCS_BUCKET_NAME : str
        Name of the Google Cloud Storage bucket where the data will be hosted
    GCS_BUCKET_DIR : int
        Bucket's sub directory (simply /dir/ added to the path)

    Methods
    -------
    gcs_get_bucket_blobs_name_list()
    
    """
    def __init__(self, config_file):
        # Load configuration
        conf = open(config_file)
        conf_dict = yaml.load(conf, Loader=yaml.FullLoader)

        # Init attributes
        self.client = storage.Client.from_service_account_json(conf_dict["gcs_config"]["GCS_RW_KEY"]) # key has to be next to .py file

        self.GCS_PROJECT_ID = conf_dict["gcs_config"]["GCS_PROJECT_ID"]
        self.GCS_PROJECT_NUMBER = conf_dict["gcs_config"]["GCS_PROJECT_NUMBER"]
        self.GCS_BUCKET_NAME = conf_dict["gcs_config"]["GCS_BUCKET_NAME"]
        self.GCS_BUCKET_DIR = conf_dict["gcs_config"]["GCS_BUCKET_DIR"]
        self.GCS_BUCKET_PATH = "gs://" + self.GCS_BUCKET_NAME + "/" 
        # BUCKET_PATH + BUCKET_DIR + filename 
        # BUCKET_PATH + gcs_filename

        # Close config file
        conf.close()

        # Verify that "GCS_BUCKET_NAME" is an existing bucket
        if self.GCS_BUCKET_NAME not in [bucket.name for bucket in self.client.list_buckets()]:
            print("Error: bucket does not exist.")
            raise ValueError("Bucket " + self.GCS_BUCKET_NAME + " does not exist. Check configuration file and name an existing bucket.")

    def gcs_get_bucket_dir(self):
        return self.GCS_BUCKET_DIR

    def gcs_get_bucket_blobs(self):
        """Get the blobs' list from the bucket
        """
        blobs = self.client.list_blobs(self.GCS_BUCKET_NAME)
        return(blobs)
    
    def gcs_get_bucket_blobs_name_list(self):
        """Returns a list of the blob's names in the bucket.
        """
        blobs = self.gcs_get_bucket_blobs()
        return [blob.name for blob in blobs]
    
    def gcs_get_bucket_blobs_id_list(self):
        """Returns a list of the blob's id in the bucket.
        """
        blobs = self.gcs_get_bucket_blobs()
        return [blob.id for blob in blobs]


    def gcs_upload_to_bucket(self, blob_name, local_file_path):
        """Upload a file to the bucket given a name and a local path
        """
        try:
            bucket = self.client.get_bucket(self.GCS_BUCKET_NAME)
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(local_file_path)
            return True
        except Exception as e:
            print(e)
            return False
    

    def gcs_get_blob_URI_list(self):
        """Returns the bucket's files links list.
        """
        blobs = self.gcs_get_bucket_blobs()
        links = ["gs://" + self.GCS_BUCKET_NAME + "/" + blob.name for blob in blobs]
        return links
    
    def gcs_print_URI(self):
        """Prints out the bucket's elements list
        """
        print(str(self.gcs_get_blob_URI_list()))

    def gcs_delete_blob(self, blob_name):
        """Deletes a blob from the bucket."""
        # bucket_name = "your-bucket-name"
        # blob_name = "your-object-name"

        

        bucket = self.client.bucket(self.GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.delete()

        print("Blob {} deleted.".format(blob_name))
    



