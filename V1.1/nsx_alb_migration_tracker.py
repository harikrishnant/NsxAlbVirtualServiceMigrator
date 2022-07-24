import pandas
import os
import json
import sys

class NsxAlbMigrationTracker:
    def __init__(self, controller_url, username, nsx_alb_tenant, api_version, run_id, track_dir):
        self._run_id = run_id
        self._controller_url = controller_url
        self._username = username
        self._nsx_alb_tenant = nsx_alb_tenant
        self._api_version = api_version
        self.track_dir = track_dir

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    def set_tracking(self):
        ''' Create the directory to save object tracking info '''
        if not os.path.exists(self.track_dir):
            os.makedirs(self.track_dir)
        if ("obj_track" + "-" + self._run_id + ".csv" in os.listdir(self.track_dir)) or ("infra_track" + "-" + self._run_id + ".json" in os.listdir(self.track_dir)):
            overwrite_prompt = input(f"\nWARNING : Track objects with the same Run ID {[self._run_id]} exists. Overwrite? Y/N ").lower()
            if overwrite_prompt == "n" or overwrite_prompt == "no":
                self.print_func(f"\nAborting..... Cleanup the previous Run [{self._run_id}] and Re-run the migrator with a different prefix (Run ID)\n")
                sys.exit()
            elif overwrite_prompt == "y" or overwrite_prompt == "yes":
                pass
            else:
                self.print_func("\nInvalid entry.....Aborting")
                sys.exit()
        csv_tracker_headers = {
            "obj_type": [],
            "obj_name": [],
            "uuid": [],
            "url": []
        }
        dict_infra_tracker = {
            "controller": self._controller_url,
            "username": self._username,
            "nsx_alb_tenant": self._nsx_alb_tenant,
            "api_version": self._api_version,
            "run_id": self._run_id
        }
        self.tracker_csv = self.track_dir + "/obj_track-" + self._run_id + ".csv"
        self._infra_json = self.track_dir + "/infra_track-" + self._run_id + ".json"
        tracking_dataframe = pandas.DataFrame(csv_tracker_headers)
        tracking_dataframe.to_csv(self.tracker_csv, index=False)
        with open(self._infra_json, "w") as outfile:
            json.dump(dict_infra_tracker, outfile, indent=4)
        self.print_func(f"\nTracking information for cleanup is saved to {self.track_dir}")
        