import uuid


class FileWrapper:
    """
    Represent an Image that will be uploaded to LB and GCS 
    CRUD must be done outside (provided wrappers)

    """
    def __init__(self, localpath, basename, gcs_path, gcs_url, lb_extid):
        self.ID = uuid.uuid1()
        self.local_file_path = localpath # On creation, providing a local path is mandatory. This should be used for upload only. 
        self.gcs_path = gcs_path # path to GCS 
        self.gcs_url = gcs_url
        self.lb_extid = lb_extid  # path to Labelbox (extid)
        self.basename = basename


    
    # def is_in_lb(self):
    #     return (self.lb_path != "")

    # def is_in_gcs(self):
    #     return (self.gcs_path != "")

    def print(self):
        print(f"File {self.ID} \nBasename and Labelbox extid: {self.lb_extid} \nGCS url: {self.gcs_url}")

    def get_id(self):
        return self.ID
    
    def get_basename(self):
        return self.basename

    def get_local_path(self):
        return self.local_file_path

    def get_gcs_path(self):
        return self.gcs_path
    
    def get_gcs_url(self):
        return self.gcs_url

    def get_lb_extid(self):
        return self.lb_extid


    def set_gcs_path(self, path):
        self.gcs_path = path
        return
    
    def set_lb_extid(self, path):
        self.lb_extid = path
        return

    
