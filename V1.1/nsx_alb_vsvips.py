#Import modules
import requests
import sys
import pandas
from tabulate import tabulate

class NsxAlbVsVip:
    def __init__(self, url, headers, run_id):
        self._url = url + "/api/vsvip"
        self._headers = headers
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    #Class Method to get the list of all VS Vips and to handle API Pagination
    def get_vsvip(self):
        ''' Class Method to fetch the list of all VS VIPs in the Tenant'''
        self._list_vsvips = []
        self.dict_vsvip_url_name = {}
        new_results = True
        page = 1
        while new_results: 
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for vsvip in new_results:
                if vsvip != []:
                    self._list_vsvips.append(vsvip)
                    self.dict_vsvip_url_name[vsvip["url"]] = vsvip["name"]
            page += 1
        if (len(self.dict_vsvip_url_name) == 0) and (response == False): #Handle a scenario where there are no VS VIPs in NSX ALB tenant
            self.print_func(f"\nList NSX ALB VS VIPs Unsuccessful ({response.status_code})\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()

    def set_vsvip(self, dict_selectedvs_originalvsvipname):
        '''Class method to get the original VS VIP ref and name in required dict format for migration'''
        self.get_vsvip() #get_vsvip method is a pre-requisite for calling set_vsvip method
        self.dict_selectedvsvip_url_name = {}
        if len(dict_selectedvs_originalvsvipname) != 0:
            for selectedvs, selectedvs_vsvipname in list(dict_selectedvs_originalvsvipname.items()):
                for vsvip_url, vsvip_name in list(self.dict_vsvip_url_name.items()):
                    if selectedvs_vsvipname == vsvip_name:
                        self.dict_selectedvsvip_url_name[vsvip_url] = vsvip_name
        else:
            self.dict_selectedvsvip_url_name = {}

    def create_vsvip(self, body):
        ''' Class Method to create NSX ALB VS VIPs in the Tenant on the selected Cloud Account'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False )
        if response:
            self.print_func(f"\nVS-VIP '{response.json()['name']}' successfully created ({response.status_code})\n")
        else:
            self.print_func(f"\nVS-VIP '{body['name']}' creation Failed ({response.status_code})\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            self.print_func("\nExiting, Please cleanup any objects that are created, fix the error and re-run the migrator \n")
            sys.exit()
        return response.json()
    
    def migrate_vsvip(self, target_cloud_url, target_vrfcontext_url, target_vrfcontext_tier1path, prefix_tag, tracker_csv):
        ''' Class Method to migrate VS VIPs to target cloud account '''
        self._dict_vsvipmigrated_name_url = {}
        self.dict_originalvsvipurl_migratedvsvipurl = {}
        for selectedvsvip_url, selectedvsvip_name in list(self.dict_selectedvsvip_url_name.items()):
            for vsvip in self._list_vsvips:
                if selectedvsvip_name == vsvip["name"]:
                    del vsvip["uuid"]
                    del vsvip["url"]
                    del vsvip["_last_modified"]
                    if "tier1_lr" in vsvip:
                        del vsvip["tier1_lr"]
                    vsvip["cloud_ref"] = target_cloud_url
                    vsvip["vrf_context_ref"] = target_vrfcontext_url
                    if target_vrfcontext_tier1path != "":
                        vsvip["tier1_lr"] = target_vrfcontext_tier1path                    
                    for item in vsvip["vip"]:
                        if "discovered_networks" in item.keys():
                            del item["discovered_networks"]
                        if "placement_networks" in item.keys():
                            del item["placement_networks"]
                    vsvip["name"] = prefix_tag + "-" + vsvip["name"]
                    migrated_vsvip = self.create_vsvip(vsvip)
                    migrated_vsvip_url = self._url + "/" + migrated_vsvip["uuid"]
                    #Append to tracker
                    dict_migrated_vsvip = {
                                "obj_type" : ["vsvip"],
                                "obj_name" : [migrated_vsvip["name"]],
                                "uuid" : [migrated_vsvip["uuid"]],
                                "url" : [migrated_vsvip_url]
                            }
                    df_migrated_vsvip = pandas.DataFrame(dict_migrated_vsvip)
                    df_migrated_vsvip.to_csv(tracker_csv, mode='a', index=False, header=False)
                    self._dict_vsvipmigrated_name_url[migrated_vsvip["name"]] = migrated_vsvip_url
                    self.dict_originalvsvipurl_migratedvsvipurl[selectedvsvip_url] = migrated_vsvip_url
        if len(self._dict_vsvipmigrated_name_url) != 0:
            self.print_func("\nThe below VS-VIPs are migrated successfully\n")
            self.print_func(tabulate(list(map(list, self._dict_vsvipmigrated_name_url.items())), headers=["VS-VIP_Name", "VS-VIP_Ref"], showindex=True, tablefmt="fancy_grid"))

    def slice_vsvip_name(self, vsvip_name):
        start_index = vsvip_name.find(self._run_id) + len(self._run_id) + 1
        return vsvip_name[start_index:]
        
    def remove_vsvip_prefix(self, obj_tracker, headers):
        ''' Class Method to remove the prefixes of NSX ALB vsvips '''
        self.get_vsvip() #get_pool methos is a pre-requisite for calling migrate_pool method
        df_obj_track_csv = pandas.read_csv(obj_tracker + "/obj_track-" + self._run_id + ".csv")
        for index, row in df_obj_track_csv.iterrows():
            if row["obj_type"] == "vsvip":
                for vsvip in self._list_vsvips:
                    if vsvip["url"] == row["url"]:
                        if vsvip["name"][:len(self._run_id)] == self._run_id:
                            vsvip["name"] = self.slice_vsvip_name(vsvip["name"])
                            response = requests.put(vsvip["url"], json=vsvip, headers=headers, verify=False )
                            if response:
                                print(f"\nvsvip Prefix for {self._run_id + '-' + response.json()['name']} removed successfully ({response.status_code}). New Object name is '{response.json()['name']}'\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["vsvip"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [response.json()['name']],
                                    "PREFIX_REMOVAL_STATUS" : ["SUCCESS"],
                                    "Error" : [""]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                            else:
                                print(f"\nvsvip Prefix removal failed for {self._run_id + '-' + vsvip['name']} - ({response.status_code})\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["vsvip"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [row["obj_name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [response.json()]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                        else:
                            print(f"\nPrefix tag missing in {vsvip['name']}, hence not renamed")
                            dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["vsvip"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [vsvip["name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [f"Prefix tag missing in {vsvip['name']}"]
                                }  
                            df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                            df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)        