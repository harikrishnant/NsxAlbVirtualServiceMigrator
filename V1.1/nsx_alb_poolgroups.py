#Import Modules
import requests
import sys
import pandas
from tabulate import tabulate

#Class for the Pool Group object
class NsxAlbPoolGroup:
    def __init__(self, url, headers, run_id):
        self._url = url + "/api/poolgroup"
        self._headers = headers
        self._run_id = run_id

    def print_func(self, item):
        print(item)                
        with open(f"./logs/run-{self._run_id}.log", "a", encoding="utf-8") as outfile:
            print(item, file=outfile)

    #Class Method to get the list of all Pools Groups and to handle API Pagination
    def get_poolgroup(self):
        ''' Class Method to fetch the list of all pools groups in the Tenant'''
        self._list_poolgroups = []
        self.dict_poolgroup_url_name = {}
        new_results = True
        page = 1
        while new_results:
            response = requests.get(self._url + f"?page={page}", headers=self._headers, verify=False)
            response_body = response.json()
            new_results = response_body.get("results", [])#Returns False if "results" not found
            for poolgroup in new_results:
                if poolgroup != []:
                    self._list_poolgroups.append(poolgroup)
                    self.dict_poolgroup_url_name[poolgroup["url"]] = poolgroup["name"]
            page += 1
        if (len(self.dict_poolgroup_url_name) == 0) and (response == False): #Handle a scenario where there are no pool groups in NSX ALB tenant
            self.print_func(f"List NSX ALB Pool Groups Unsuccessful ({response.status_code})\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            sys.exit()

    def set_poolgroup(self, dict_selectedvs_originalpoolgroupname):
        '''Class method to get the original pool group ref and name in required dict format for migration'''
        self.get_poolgroup() #get_pool method is a pre-requisite for calling set_pool method
        self.dict_selectedpoolgroup_url_name = {}
        if len(dict_selectedvs_originalpoolgroupname) != 0:
            for selectedvs, selectedvs_poolgroupname in list(dict_selectedvs_originalpoolgroupname.items()):
                for poolgroup_url, poolgroup_name in list(self.dict_poolgroup_url_name.items()):
                    if selectedvs_poolgroupname == poolgroup_name:
                        self.dict_selectedpoolgroup_url_name[poolgroup_url] = poolgroup_name
        else:
            self.dict_selectedpoolgroup_url_name = {}

    def get_poolgroup_member(self, dict_poolgroup_url_name, dict_pool_url_name):    
        self.dict_poolgroupmembers_url_name = {}
        self._list_poolname_poolgroupname = []
        if len(dict_poolgroup_url_name) != 0:
            for url,name in list(dict_poolgroup_url_name.items()):
                for poolgroup in self._list_poolgroups:
                    if name == poolgroup["name"]:
                        if "members" in poolgroup.keys():
                            for member in poolgroup["members"]:
                                for pool_url,pool_name in list(dict_pool_url_name.items()):
                                    if member["pool_ref"] == pool_url:
                                        self.dict_poolgroupmembers_url_name[pool_url] = dict_pool_url_name[pool_url]
                                        self._list_poolname_poolgroupname.append([dict_pool_url_name[pool_url], poolgroup["name"]])
            if len(self._list_poolname_poolgroupname) != 0:
                self.print_func(f"\nSelected Pool Groups has the below pools as members which will be migrated next:\n")
                self.print_func(tabulate(self._list_poolname_poolgroupname, headers=["Pool", "Pool_Group"], showindex=True, tablefmt="fancy_grid"))
            else:
                self.print_func("\nSuccessfully scanned the Pool Groups and no pool members found\n")
        else:
            self.dict_poolgroupmembers_url_name = {}

    def create_poolgroup(self, body):
        ''' Class Method to create NSX ALB Pool Groups in the Tenant on the selected Cloud Account'''
        response = requests.post(self._url, json=body, headers=self._headers, verify=False )
        if response:
            self.print_func(f"\nPool Group '{response.json()['name']}' successfully created ({response.status_code})\n")
        else:
            self.print_func(f"\nPool Group'{body['name']}' creation Failed ({response.status_code})\n")
            self.print_func(tabulate(list(map(list, response.json().items())), headers=["Error", "Details"], showindex=True, tablefmt="fancy_grid"))
            self.print_func("\nExiting, Please cleanup any objects that are created, fix the error and re-run the migrator \n")
            sys.exit()
        return response.json()   

    def migrate_poolgroup(self, dict_poolgroup2migrate_url_name, dict_originalpoolurl_migratedpoolurl, target_cloud_url, prefix_tag, tracker_csv):   
        '''Class Method to migrate pool groups from one NSX ALB cloud to another in the same Tenant''' 
        self.get_poolgroup() #get_poolgroup method is a pre-requisite for calling migrate_poolgroup method
        self.dict_originalpoolgroupurl_migratedpoolgroupurl = {}
        self._dict_migratedpoolgroup_name_url = {}
        self._dict_previously_migrated_poolgroup_oldname_newname = {}
        if len(dict_poolgroup2migrate_url_name) != 0:
            for poolgroup_url, poolgroup_name in list(dict_poolgroup2migrate_url_name.items()):
                if not (prefix_tag + "-" + poolgroup_name) in list(self.dict_poolgroup_url_name.values()): #Checking if the pools to migrate were previously migrated For eg, as part of content switching policies            for poolgroup in self.list_poolgroups:
                    for poolgroup in self._list_poolgroups:
                        if poolgroup_name == poolgroup["name"]:
                            del poolgroup["url"]
                            del poolgroup["uuid"]
                            del poolgroup["_last_modified"]
                            poolgroup["name"] = prefix_tag + "-" + poolgroup["name"]
                            poolgroup["cloud_ref"] = target_cloud_url
                            if "members" in list(poolgroup.keys()):
                                for member in poolgroup["members"]:
                                    for originalpoolurl, migratedpoolurl in list(dict_originalpoolurl_migratedpoolurl.items()):
                                        if member["pool_ref"] == originalpoolurl:
                                            member["pool_ref"] = migratedpoolurl
                            migrated_poolgroup = self.create_poolgroup(poolgroup)
                            migrated_poolgroup_url = self._url + "/" + migrated_poolgroup["uuid"]
                            #Append to tracker
                            dict_migrated_poolgroup = {
                                "obj_type" : ["poolgroup"],
                                "obj_name" : [migrated_poolgroup["name"]],
                                "uuid" : [migrated_poolgroup["uuid"]],
                                "url" : [migrated_poolgroup_url]
                            }
                            df_migrated_poolgroup = pandas.DataFrame(dict_migrated_poolgroup)
                            df_migrated_poolgroup.to_csv(tracker_csv, mode='a', index=False, header=False)
                            self.dict_originalpoolgroupurl_migratedpoolgroupurl[poolgroup_url] = migrated_poolgroup_url
                            self._dict_migratedpoolgroup_name_url[migrated_poolgroup["name"]] = migrated_poolgroup_url
                else:
                    self._dict_previously_migrated_poolgroup_oldname_newname[poolgroup_name] = prefix_tag + "-" + poolgroup_name
                    for url, name in list(self.dict_poolgroup_url_name.items()):
                        if (prefix_tag + "-" + poolgroup_name) == name:
                            self.dict_originalpoolgroupurl_migratedpoolgroupurl[poolgroup_url] = url
        else:
            self.dict_originalpoolgroupurl_migratedpoolgroupurl = {}
        if len(self._dict_migratedpoolgroup_name_url) != 0:
            self.print_func(f"\nThe below Pool Groups are migrated successfully to the new cloud account\n")
            self.print_func(tabulate(list(map(list, self._dict_migratedpoolgroup_name_url.items())), headers=["Migrated_PoolGroup", "Migrated_PoolGroup_Ref"], showindex=True, tablefmt="fancy_grid"))
        if len(self._dict_previously_migrated_poolgroup_oldname_newname) != 0:
            self.print_func(f"\nThe below Pool Groups were previously migrated successfully as part of a different workflow (Eg: Content switching policies) and hence not re-attempted\n")
            self.print_func(tabulate(list(map(list, self._dict_previously_migrated_poolgroup_oldname_newname.items())), headers=["Original_PoolGroup", "Migrated_PoolGroup"], showindex=True, tablefmt="fancy_grid"))
    
    def slice_poolgroup_name(self, poolgroup_name):
        start_index = poolgroup_name.find(self._run_id) + len(self._run_id) + 1
        return poolgroup_name[start_index:]
        
    def remove_poolgroup_prefix(self, obj_tracker, headers):
        ''' Class Method to remove the prefixes of NSX ALB poolgroups '''
        self.get_poolgroup() #get_pool methos is a pre-requisite for calling migrate_pool method
        df_obj_track_csv = pandas.read_csv(obj_tracker + "/obj_track-" + self._run_id + ".csv")
        for index, row in df_obj_track_csv.iterrows():
            if row["obj_type"] == "poolgroup":
                for poolgroup in self._list_poolgroups:
                    if poolgroup["url"] == row["url"]:
                        if poolgroup["name"][:len(self._run_id)] == self._run_id:
                            poolgroup["name"] = self.slice_poolgroup_name(poolgroup["name"])
                            response = requests.put(poolgroup["url"], json=poolgroup, headers=headers, verify=False )
                            if response:
                                print(f"\nPoolgroup Prefix for {self._run_id + '-' + response.json()['name']} removed successfully ({response.status_code}). New Object name is '{response.json()['name']}'\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["poolgroup"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [response.json()['name']],
                                    "PREFIX_REMOVAL_STATUS" : ["SUCCESS"],
                                    "Error" : [""]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                            else:
                                print(f"\nPoolgroup Prefix removal failed for {self._run_id + '-' + poolgroup['name']} - ({response.status_code})\n")
                                dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["poolgroup"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [row["obj_name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [response.json()]
                                }  
                                df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                                df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)
                        else:
                            print(f"\nPrefix tag missing in {poolgroup['name']}, hence not renamed")
                            dict_df_obj_remove_prefix_status = {
                                    "obj_type" : ["poolgroup"],
                                    "obj_name_old" : [row["obj_name"]],
                                    "obj_name_new" : [poolgroup["name"]],
                                    "PREFIX_REMOVAL_STATUS" : ["FAILURE"],
                                    "Error" : [f"Prefix tag missing in {poolgroup['name']}"]
                                }  
                            df_obj_remove_prefix_status = pandas.DataFrame(dict_df_obj_remove_prefix_status)
                            df_obj_remove_prefix_status.to_csv(obj_tracker + "/obj_prefix_removal_status_" + self._run_id + ".csv", index=False, mode='a', header=False)


