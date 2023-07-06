import requests
import pandas
import sys
from tabulate import tabulate

class NsxAlbCleanup:
    def __init__(self, headers, tracker_dir, run_id):
        self._headers = headers
        self._tracker_dir = tracker_dir
        self._run_id = run_id
        self.list_df_obj_deletion_status = []
        self.dict_obj_not_deleted = {}
        self._dict_df_obj_deletion_status = {
                "obj_type" : [],
                "obj_name" : [],
                "url" : [],
                "CLEANUP_STATUS" : [],
                "Error" : []
            }  
        df_obj_deletion_status = pandas.DataFrame(self._dict_df_obj_deletion_status)
        df_obj_deletion_status.to_csv(self._tracker_dir + "/obj_cleanup_status_" + self._run_id + ".csv", index=False)

    def delete_object(self, url, obj_type, obj_name):
        response = requests.delete(url, headers=self._headers, verify=False)
        if response:
            print(f"\n{obj_type.title()} object [{obj_name}] deleted successfully - ({response.status_code})")
            dict_df_obj_deletion_status = {
                "obj_type" : [obj_type],
                "obj_name" : [obj_name],
                "url" : [url],
                "CLEANUP_STATUS" : ["SUCCESS"],
                "Error" : [""]
            }
            df_obj_deletion_status = pandas.DataFrame(dict_df_obj_deletion_status)
            df_obj_deletion_status.to_csv(self._tracker_dir + "/obj_cleanup_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
        else:
            print(f"\n{obj_type.title()} object [{obj_name}] deletion failed - ({response.status_code})")
            dict_df_obj_deletion_status = {
                "obj_type" : [obj_type],
                "obj_name" : [obj_name],
                "url" : [url],
                "CLEANUP_STATUS" : ["FAILURE"],
                "Error" : [response.json()]
            }
            df_obj_deletion_status = pandas.DataFrame(dict_df_obj_deletion_status)
            df_obj_deletion_status.to_csv(self._tracker_dir + "/obj_cleanup_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
            self.dict_obj_not_deleted["url"] = obj_name

    def initiate_cleanup(self):
        df_track_csv = pandas.read_csv(self._tracker_dir + "/obj_track" + "-" + self._run_id + ".csv")
        for each_obj in ["virtualservice", "vsvip", "httppolicyset", "poolgroup", "pool"]:
            for index, row in df_track_csv.iterrows():
                if row["obj_type"] == each_obj:
                    self.delete_object(row["url"], row["obj_type"], row["obj_name"])            
                   