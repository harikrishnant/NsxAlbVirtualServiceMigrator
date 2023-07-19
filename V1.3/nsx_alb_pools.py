#Import modules
import requests
import sys
from tabulate import tabulate
from art import line
import pandas

#Class for the Pool pbject
class NsxAlbPool:
    def __init__(self, url, headers, run_id):
        self._url = url + "/api/pool"
        self._headers = headers
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    #Class Method to get the list of all Pools and to handle API Pagination
    def get_pool(self):
        ''' Class Method to fetch the list of all pools in the Tenant'''
        self._list_pools = []
        self.dict_pool_url_name = {}
        new_results = True
        page = 1
        while new_results: 
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", []) #Returns False if "results" not found
            for pool in new_results:
                if pool != []:
                    self._list_pools.append(pool)
                    self.dict_pool_url_name[pool["url"]] = pool["name"]
            page += 1
        if (len(self.dict_pool_url_name) == 0) and (response == False): #Handle a scenario where there are no pools in NSX ALB tenant
            self.print_func(f"\nList NSX ALB Pools Unsuccessful ({response.status_code})\n")
            #Print the error details in table using tabulate function
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()
    
    def set_pool(self, dict_selectedvs_originalpoolname):
        '''Class method to get the original pool url and name in required dict format for migration'''
        self.get_pool() #get_pool method is a pre-requisite for calling set_pool method
        self.dict_selectedpool_url_name = {}
        if len(dict_selectedvs_originalpoolname) != 0:
            for selectedvs, selectedvs_poolname in list(dict_selectedvs_originalpoolname.items()):
                for pool_url, pool_name in list(self.dict_pool_url_name.items()):
                    if selectedvs_poolname == pool_name:
                        self.dict_selectedpool_url_name[pool_url] = pool_name
        else:
            self.dict_selectedpool_url_name = {}

    def create_pool(self, body):
        ''' Class Method to create NSX ALB pools in the Tenant on the selected Cloud Account'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False )
        if response:
            self.print_func(f"\nPool '{response.json()['name']}' successfully created ({response.status_code})\n")
        else:
            self.print_func(f"\nPool '{body['name']}' creation Failed ({response.status_code})\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            self.print_func("\nExiting, Please cleanup any objects that are created, fix the error and re-run the migrator \n")
            sys.exit()
        return response.json()

    def migrate_pool(self, dict_pool2migrate_url_name, target_cloud_url, target_vrfcontext_url, target_vrfcontext_tier1path, prefix_tag, tracker_csv):
        '''Class Method to migrate pools from one NSX ALB cloud to another in the same Tenant'''
        self.get_pool() #get_pool methos is a pre-requisite for calling migrate_pool method
        self.dict_originalpoolurl_migratedpoolurl = {}
        self._dict_migratedpool_name_url = {}
        self._dict_previously_migrated_pool_oldname_newname = {}
        if len(dict_pool2migrate_url_name) != 0:
            for pool_url, pool_name in list(dict_pool2migrate_url_name.items()):
                if not (prefix_tag + "-" + pool_name) in list(self.dict_pool_url_name.values()): #Checking if the pools to migrate were previously migrated For eg, as part of content switching policies
                    for pool in self._list_pools:
                        if pool_name == pool["name"]:
                            del pool["url"]
                            del pool["uuid"]
                            del pool["_last_modified"]
                            if "tier1_lr" in pool:
                                del pool["tier1_lr"]
                            if "placement_networks" in list(pool.keys()):
                                del pool["placement_networks"]
                            if "networks" in list(pool.keys()):
                                del pool["networks"]
                            if "servers" in list(pool.keys()) and len(pool["servers"]) != 0:
                                for server in pool["servers"]:
                                    if "discovered_networks" in list(server.keys()):
                                        del server["discovered_networks"]
                                    if "vm_ref" in list(server.keys()):
                                        del server["vm_ref"]
                                    if "nw_ref" in list(server.keys()):
                                        del server["nw_ref"] 
                            pool["enabled"] = "true"
                            pool["name"] = prefix_tag + "-" + pool["name"]
                            pool["cloud_ref"] = target_cloud_url
                            pool["vrf_ref"] = target_vrfcontext_url
                            if target_vrfcontext_tier1path != "":
                                pool["tier1_lr"] = target_vrfcontext_tier1path
                            migrated_pool = self.create_pool(pool)
                            migrated_pool_url = self._url + "/" + migrated_pool["uuid"]
                            #Append to tracker
                            dict_migrated_pool = {
                                "obj_type" : ["pool"],
                                "obj_name" : [migrated_pool["name"]],
                                "uuid" : [migrated_pool["uuid"]],
                                "url" : [migrated_pool_url]
                            }
                            df_migrated_pool = pandas.DataFrame(dict_migrated_pool)
                            df_migrated_pool.to_csv(tracker_csv, mode='a', index=False, header=False)                           
                            self.dict_originalpoolurl_migratedpoolurl[pool_url] = migrated_pool_url
                            self._dict_migratedpool_name_url[migrated_pool["name"]] = migrated_pool_url
                else:
                    self._dict_previously_migrated_pool_oldname_newname[pool_name] = prefix_tag + "-" + pool_name
                    for url, name in list(self.dict_pool_url_name.items()):
                        if (prefix_tag + "-" + pool_name) == name:
                            self.dict_originalpoolurl_migratedpoolurl[pool_url] = url
        else:
            self.dict_originalpoolurl_migratedpoolurl = {}
        if len(self._dict_migratedpool_name_url) != 0:
            self.print_func(f"\nThe below pools are migrated successfully to the target cloud account\n")
            self.print_func(tabulate(list(map(list, self._dict_migratedpool_name_url.items())), headers=["Migrated_Pool", "Migrated_Pool_Ref"], showindex=True, tablefmt="fancy_grid"))
        if len(self._dict_previously_migrated_pool_oldname_newname) != 0:
            self.print_func(f"\nThe below pools were previously migrated as part of a different workflow (Eg: Content switching policies) and hence not re-attempted\n")
            self.print_func(tabulate(list(map(list, self._dict_previously_migrated_pool_oldname_newname.items())), headers=["Original_Pool", "Migrated_Pool"], showindex=True, tablefmt="fancy_grid"))

    def slice_pool_name(self, pool_name):
        start_index = pool_name.find(self._run_id) + len(self._run_id) + 1
        return pool_name[start_index:]
        
    def remove_pool_prefix(self, obj_tracker, headers):
        ''' Class Method to remove the prefixes of NSX ALB pools '''
        self.get_pool() #get_pool methos is a pre-requisite for calling migrate_pool method
        df_obj_track_csv = pandas.read_csv(obj_tracker + "/obj_track-" + self._run_id + ".csv")
        for index, row in df_obj_track_csv.iterrows():
            if row["obj_type"] == "pool":
                for pool in self._list_pools:
                    if pool["url"] == row["url"]:
                        if pool["name"][:len(self._run_id)] == self._run_id:
                            pool["name"] = self.slice_pool_name(pool["name"])
                            response = requests.put(pool["url"], json=pool, headers=headers, verify=False )
                            if response:
                                print(f"\nPool Prefix for {self._run_id + '-' + response.json()['name']} removed successfully ({response.status_code}). New Object name is '{response.json()['name']}'\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["pool"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [response.json()['name']],
                                    "PREFIX_REMOVAL_STATUS" : ["SUCCESS"],
                                    "Error" : [""]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                            else:
                                print(f"\nPool Prefix removal failed for {self._run_id + '-' + pool['name']} - ({response.status_code})\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["pool"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [row["obj_name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [response.json()]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                        else:
                            print(f"\nPrefix tag missing in {pool['name']}, hence not renamed")
                            dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["pool"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [pool["name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [f"Prefix tag missing in {pool['name']}"]
                                }  
                            df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                            df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)